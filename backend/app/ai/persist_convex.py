from __future__ import annotations
import base64
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import httpx

from ..convex_client import ConvexClient
from .logging_utils import get_logger

log = get_logger("persist")


@dataclass
class PersistResult:
    course_id: Optional[str]
    module_ids: List[str]
    storage_ids: Dict[str, Dict[str, Optional[str]]]


async def convex_generate_upload_url(convex: ConvexClient) -> Optional[str]:
    try:
        data = await convex.run("files:generateUploadUrl", {})
        # Convex typical pattern returns a string URL; some wrappers may return an object
        if isinstance(data, str):
            return data
        if isinstance(data, dict):
            return data.get("uploadUrl") or data.get("url")
    except Exception as e:
        log.warning(f"Convex generateUploadUrl failed | err={e}")
        return None


async def convex_put_bytes(upload_url: str, data: bytes, content_type: str = "application/octet-stream") -> Optional[str]:
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            res = await client.post(upload_url, content=data, headers={"Content-Type": content_type})
            res.raise_for_status()
            body = res.json()
            # Convex returns { storageId: string }
            if isinstance(body, dict):
                return body.get("storageId") or body.get("storage_id")
    except Exception as e:
        log.warning(f"Convex upload failed | url={upload_url[:60]}... | err={e}")
        return None
    return None


async def persist_course_and_modules(
    *,
    convex: ConvexClient,
    course_payload: Dict[str, Any],
    modules: List[Dict[str, Any]],
    existing_course_id: Optional[str] = None,
    owner_id: Optional[str] = None,
) -> PersistResult:
    """Persist to Convex if configured, else return in-memory placeholders.

    - Files first (image/video), then docs via expected Convex functions.
    """
    module_ids: List[str] = []
    storage_ids: Dict[str, Dict[str, Optional[str]]] = {}
    course_id: Optional[str] = None

    if convex.enabled and not owner_id:
        log.warning("Convex persistence skipped: missing owner_id")

    if convex.enabled and owner_id:
        log.info(f"Persist to Convex | base_url={getattr(convex, 'base_url', None)} | modules={len(modules)}")
        course_payload = {**course_payload, "ownerId": owner_id}
        # Create initial course if not already present
        if existing_course_id:
            course_id = existing_course_id
        else:
            try:
                log.info(f"Convex createDetailed start | title={course_payload.get('title')} | topic={course_payload.get('topic')}")
                course_doc = await convex.mutation("courses:createDetailed", course_payload)
                course_id = course_doc.get("id") if isinstance(course_doc, dict) else None
                log.info(f"Convex createDetailed ok | courseId={course_id}")
            except Exception:
                course_id = None
                # Fallback to minimal create if detailed function missing
                try:
                    min_doc = await convex.mutation(
                        "courses:create",
                        {
                            "title": course_payload.get("title") or course_payload.get("topic") or "Untitled Course",
                            "ownerId": owner_id,
                        },
                    )
                    if isinstance(min_doc, dict):
                        course_id = min_doc.get("id") or min_doc.get("_id")
                        log.info(f"Convex create fallback ok | courseId={course_id}")
                except Exception:
                    course_id = None

        # Step: upload files and upsert modules
        for m in modules:
            mid = m.get("module_id") or m.get("id")
            module_ids.append(str(mid))
            storage_ids[str(mid)] = {"image": None, "video": None}

            # Upload image if present
            if m.get("gemini_output", {}).get("gemini_image_b64"):
                upload_url = await convex_generate_upload_url(convex)
                if upload_url:
                    try:
                        img_bytes = base64.b64decode(m["gemini_output"]["gemini_image_b64"])
                        sid = await convex_put_bytes(upload_url, img_bytes, content_type="image/png")
                        storage_ids[str(mid)]["image"] = sid
                        if sid:
                            log.info(f"Convex upload image ok | module={mid} | storageId={sid}")
                        else:
                            log.warning(f"Convex upload image failed (no storageId) | module={mid}")
                    except Exception:
                        pass
                else:
                    log.warning(f"Convex upload image skipped (no URL) | module={mid}")

            # Upload video if present
            if m.get("video_path") and os.path.exists(m["video_path"]):
                upload_url = await convex_generate_upload_url(convex)
                if upload_url:
                    try:
                        with open(m["video_path"], "rb") as f:
                            vid_bytes = f.read()
                        sid = await convex_put_bytes(upload_url, vid_bytes, content_type="video/mp4")
                        storage_ids[str(mid)]["video"] = sid
                        if sid:
                            log.info(f"Convex upload video ok | module={mid} | storageId={sid}")
                        else:
                            log.warning(f"Convex upload video failed (no storageId) | module={mid}")
                    except Exception:
                        pass
                else:
                    log.warning(f"Convex upload video skipped (no URL) | module={mid}")

            # Upsert module document
            try:
                manim_code = m.get("manim_code", "")
                await convex.mutation(
                    "modules:upsert",
                    {
                        "courseId": course_id,
                        "moduleId": mid,
                        "title": m.get("title"),
                        "outline": m.get("outline", []),
                        "text": m.get("text", ""),
                        "manimCode": manim_code,
                        "imageStorageId": storage_ids[str(mid)]["image"],
                        "imageCaption": m.get("gemini_output", {}).get("gemini_image_caption"),
                        "videoStorageId": storage_ids[str(mid)]["video"],
                        "ownerId": owner_id,
                    },
                )
                log.info(
                    f"Convex upsert module ok | module={mid} | manim_code_len={len(manim_code or '')}"
                )
            except Exception:
                pass

        # Finalize course
        try:
            if course_id:
                await convex.mutation(
                    "courses:finalize",
                    {"courseId": course_id, "moduleIds": module_ids, "ownerId": owner_id},
                )
                log.info(f"Convex finalize course ok | courseId={course_id} | modules={len(module_ids)}")
        except Exception:
            pass

        return PersistResult(course_id=course_id, module_ids=module_ids, storage_ids=storage_ids)

    # In-memory fallback
    for m in modules:
        mid = m.get("module_id") or m.get("id")
        module_ids.append(str(mid))
        storage_ids[str(mid)] = {
            "image": m.get("gemini_output", {}).get("gemini_image_b64"),
            "video": m.get("video_path"),
        }
    return PersistResult(course_id=None, module_ids=module_ids, storage_ids=storage_ids)
