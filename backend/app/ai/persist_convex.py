from __future__ import annotations
import base64
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import httpx

from ..convex_client import ConvexClient


@dataclass
class PersistResult:
    course_id: Optional[str]
    module_ids: List[str]
    storage_ids: Dict[str, Dict[str, Optional[str]]]


async def convex_generate_upload_url(convex: ConvexClient) -> Optional[str]:
    try:
        data = await convex.run("files:generateUploadUrl", {})
        return data.get("uploadUrl") if isinstance(data, dict) else None
    except Exception:
        return None


async def convex_put_bytes(upload_url: str, data: bytes, content_type: str = "application/octet-stream") -> Optional[str]:
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            res = await client.put(upload_url, content=data, headers={"Content-Type": content_type})
            res.raise_for_status()
            body = res.json()
            # Convex returns { storageId: string }
            if isinstance(body, dict):
                return body.get("storageId") or body.get("storage_id")
    except Exception:
        return None
    return None


async def persist_course_and_modules(
    *,
    convex: ConvexClient,
    course_payload: Dict[str, Any],
    modules: List[Dict[str, Any]],
    existing_course_id: Optional[str] = None,
) -> PersistResult:
    """Persist to Convex if configured, else return in-memory placeholders.

    - Files first (image/video), then docs via expected Convex functions.
    """
    module_ids: List[str] = []
    storage_ids: Dict[str, Dict[str, Optional[str]]] = {}
    course_id: Optional[str] = None

    if convex.enabled:
        # Create initial course if not already present
        if existing_course_id:
            course_id = existing_course_id
        else:
            try:
                course_doc = await convex.mutation("courses:createDetailed", course_payload)
                course_id = course_doc.get("id") if isinstance(course_doc, dict) else None
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
                    except Exception:
                        pass

            # Upload video if present
            if m.get("video_path") and os.path.exists(m["video_path"]):
                upload_url = await convex_generate_upload_url(convex)
                if upload_url:
                    try:
                        with open(m["video_path"], "rb") as f:
                            vid_bytes = f.read()
                        sid = await convex_put_bytes(upload_url, vid_bytes, content_type="video/mp4")
                        storage_ids[str(mid)]["video"] = sid
                    except Exception:
                        pass

            # Upsert module document
            try:
                await convex.mutation("modules:upsert", {
                    "courseId": course_id,
                    "moduleId": mid,
                    "title": m.get("title"),
                    "outline": m.get("outline", []),
                    "text": m.get("text", ""),
                    "manimCode": m.get("manim_code", ""),
                    "imageStorageId": storage_ids[str(mid)]["image"],
                    "imageCaption": m.get("gemini_output", {}).get("gemini_image_caption"),
                    "videoStorageId": storage_ids[str(mid)]["video"],
                })
            except Exception:
                pass

        # Finalize course
        try:
            if course_id:
                await convex.mutation("courses:finalize", {"courseId": course_id, "moduleIds": module_ids})
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
