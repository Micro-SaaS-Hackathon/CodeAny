from __future__ import annotations
import os
from pathlib import Path
from uuid import uuid4
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from .models import (
    Course,
    CourseCreate,
    Stats,
    Activity,
    now_iso,
    AICourseRequest,
    AICourseResponse,
    CourseDetail,
    CourseUpdate,
    Module,
    ModuleUpdate,
)
from .convex_client import ConvexClient

# Load environment from .env automatically (so MANIM_* and others are picked up)
try:  # pragma: no cover - best-effort env loading
    from dotenv import load_dotenv  # type: ignore
    # Search upwards from CWD for a .env file; do not override real env
    load_dotenv(override=False)
    # Additionally try project root (two levels up from this file)
    load_dotenv(dotenv_path=str(Path(__file__).resolve().parents[2] / ".env"), override=False)
except Exception:
    pass
from .ai import run_course_build
from .ai.logging_utils import get_logger
from .ai.persist_convex import convex_generate_upload_url, convex_put_bytes
import asyncio

app = FastAPI(title="Cursly Teacher Hub API", version="0.1.0")

# CORS for local Nuxt dev and deployed frontends
frontend_origins = [
    os.getenv("FRONTEND_ORIGIN", "http://localhost:3010"),
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

convex = ConvexClient()
log = get_logger("api")

# --- In-memory fallback (for local dev without Convex) ---
_memory_courses: List[Course] = []
_threads: Dict[str, Dict[str, Any]] = {}
_memory_modules: Dict[str, List[Module]] = {}
_memory_course_meta: Dict[str, Dict[str, Any]] = {}


def _fallback_list_courses() -> List[Course]:
    return _memory_courses


def _fallback_create_course(title: str) -> Course:
    now = now_iso()
    course = Course(
        id=str(uuid4()),
        title=title or "Untitled Course",
        progress=0,
        created_at=now,
        updated_at=now,
        status="draft",
    )
    _memory_courses.append(course)
    _memory_course_meta[course.id] = {}
    return course


def _fallback_stats() -> Stats:
    total = len(_memory_courses)
    activities = [
        Activity(course_id=c.id, event="created", timestamp=c.created_at) for c in _memory_courses[-5:]
    ]
    return Stats(total_courses=total, active_teachers=1 if total else 0, recent_activity=activities)


def _fallback_get_course(course_id: str) -> Optional[CourseDetail]:
    for c in _memory_courses:
        if c.id == course_id:
            mods = _memory_modules.get(course_id, [])
            meta = _memory_course_meta.get(course_id, {})
            # Provide default None for detail fields not tracked in memory
            return CourseDetail(
                id=c.id,
                title=c.title,
                progress=c.progress,
                created_at=c.created_at,
                updated_at=c.updated_at,
                status=c.status,
                description=meta.get("description"),
                instructor=meta.get("instructor"),
                audience=meta.get("audience"),
                level_label=meta.get("level_label"),
                duration_weeks=meta.get("duration_weeks"),
                category=meta.get("category"),
                age_range=meta.get("age_range"),
                language=meta.get("language"),
                modules=mods,
            )
    return None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/convex/diagnostics")
async def convex_diagnostics():
    """Return Convex connectivity diagnostics to ease setup and debugging."""
    info: Dict[str, Any] = {
        "enabled": convex.enabled,
        "base_url": getattr(convex, "base_url", None),
        "auth_mode": (
            "admin" if getattr(convex, "deploy_key", None)
            else ("user_bearer" if getattr(convex, "user_bearer", None) else "none")
        ),
    }
    if not convex.enabled:
        info["status"] = "disabled (CONVEX_URL not set)"
        return info
    # Test query endpoint using a known function name used in this app
    try:
        # Expose candidate URLs for troubleshooting
        candidates = getattr(convex, "_base_candidates", lambda: [])()
        info["candidates"] = candidates
    except Exception:
        pass
    try:
        await convex.query("stats:get", {})
        info["query_ok"] = True
        info["query_path"] = "/api/query"
    except Exception as e:
        info["query_ok"] = False
        info["query_error"] = str(e)
    # Test run endpoint and function identifier normalization (':' -> '/')
    try:
        await convex.run("files:generateUploadUrl", {})
        info["run_ok"] = True
        info["run_path"] = "/api/run/{namespace/function}"
    except Exception as e:
        info["run_ok"] = False
        info["run_error"] = str(e)
    return info


@app.get("/courses", response_model=List[Course])
async def get_courses():
    if convex.enabled:
        try:
            log.info(f"Convex list start | base_url={getattr(convex, 'base_url', None)}")
            # expects Convex function name "courses:list"
            data = await convex.query("courses:list", {})
            # Unwrap various response shapes to a list of dicts
            items: List[Dict[str, Any]] = []
            if isinstance(data, list):
                items = [x for x in data if isinstance(x, dict)]
            elif isinstance(data, dict):
                for k in ("items", "value", "data", "result"):
                    v = data.get(k)
                    if isinstance(v, list):
                        items = [x for x in v if isinstance(x, dict)]
                        break
            log.info(f"Convex list ok | count={len(items)}")
            # ensure each item matches Course fields
            return [Course(**item) for item in items]
        except Exception as e:
            # fall back if Convex missing
            log.warning(f"Convex get_courses error | base_url={getattr(convex, 'base_url', None)} | err={e}")
    return _fallback_list_courses()


@app.post("/courses", response_model=Course)
async def create_course(payload: CourseCreate):
    title = payload.title or "Untitled Course"
    if convex.enabled:
        try:
            log.info(f"Convex create start | title={title}")
            data = await convex.mutation("courses:create", {"title": title})
            log.info("Convex create ok")
            return Course(**data)
        except Exception as e:
            log.warning(f"Convex create_course error | err={e}")
    return _fallback_create_course(title)


@app.get("/courses/{course_id}", response_model=CourseDetail)
async def get_course_detail(course_id: str):
    if convex.enabled:
        try:
            data = await convex.query("courses:get", {"id": course_id})
            if not data:
                raise HTTPException(status_code=404, detail="Course not found")
            # Fetch modules
            mods_raw = await convex.query("modules:listByCourse", {"courseId": course_id})
            mods: List[Module] = []
            if isinstance(mods_raw, list):
                for m in mods_raw:
                    if isinstance(m, dict):
                        mods.append(Module(**m))
            # Map fields and normalize names
            detail = CourseDetail(
                id=data.get("id"),
                title=data.get("title"),
                progress=data.get("progress", 0),
                created_at=data.get("created_at") or now_iso(),
                updated_at=data.get("updated_at") or now_iso(),
                status=data.get("status", "draft"),
                description=data.get("description"),
                instructor=data.get("instructor"),
                audience=data.get("audience"),
                level_label=data.get("levelLabel"),
                duration_weeks=data.get("durationWeeks"),
                category=data.get("category"),
                age_range=data.get("ageRange"),
                language=data.get("language"),
                modules=mods,
            )
            return detail
        except HTTPException:
            raise
        except Exception as e:
            log.warning(f"Convex get_course_detail error | err={e}")
    # fallback
    detail = _fallback_get_course(course_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return detail


@app.patch("/courses/{course_id}", response_model=CourseDetail)
async def update_course(course_id: str, payload: CourseUpdate):
    if convex.enabled:
        try:
            args: Dict[str, Any] = {"courseId": course_id}
            # Map snake_case to Convex camelCase for detail fields
            if payload.title is not None:
                args["title"] = payload.title
            if payload.status is not None:
                args["status"] = payload.status
            if payload.description is not None:
                args["description"] = payload.description
            if payload.instructor is not None:
                args["instructor"] = payload.instructor
            if payload.audience is not None:
                args["audience"] = payload.audience
            if payload.level_label is not None:
                args["levelLabel"] = payload.level_label
            if payload.duration_weeks is not None:
                args["durationWeeks"] = payload.duration_weeks
            if payload.category is not None:
                args["category"] = payload.category
            if payload.age_range is not None:
                args["ageRange"] = payload.age_range
            if payload.language is not None:
                args["language"] = payload.language
            await convex.mutation("courses:updateBasic", args)
            # return fresh detail
            return await get_course_detail(course_id)
        except Exception as e:
            log.warning(f"Convex update_course error | err={e}")
    # fallback memory update
    found = False
    for i, c in enumerate(_memory_courses):
        if c.id == course_id:
            updated = Course(
                id=c.id,
                title=payload.title or c.title,
                progress=c.progress,
                created_at=c.created_at,
                updated_at=now_iso(),
                status=payload.status or c.status,
            )
            _memory_courses[i] = updated
            found = True
            break
    if not found:
        raise HTTPException(status_code=404, detail="Course not found")
    # update meta
    meta = _memory_course_meta.setdefault(course_id, {})
    for k in [
        "description",
        "instructor",
        "audience",
        "level_label",
        "duration_weeks",
        "category",
        "age_range",
        "language",
    ]:
        v = getattr(payload, k, None)
        if v is not None:
            meta[k] = v
    _memory_course_meta[course_id] = meta
    return _fallback_get_course(course_id)


@app.delete("/courses/{course_id}")
async def delete_course(course_id: str):
    if convex.enabled:
        try:
            result = await convex.mutation("courses:delete_", {"courseId": course_id})
            if not result:
                raise HTTPException(status_code=404, detail="Course not found")
            return {"deleted": True, "id": course_id}
        except Exception as e:
            log.warning(f"Convex delete_course error | err={e}")
    # fallback memory delete
    for i, c in enumerate(_memory_courses):
        if c.id == course_id:
            _memory_courses.pop(i)
            # Clean up modules and meta
            _memory_modules.pop(course_id, None)
            _memory_course_meta.pop(course_id, None)
            return {"deleted": True, "id": course_id}
    raise HTTPException(status_code=404, detail="Course not found")


@app.get("/courses/{course_id}/modules", response_model=List[Module])
async def list_modules(course_id: str):
    if convex.enabled:
        try:
            mods_raw = await convex.query("modules:listByCourse", {"courseId": course_id})
            items: List[Module] = []
            if isinstance(mods_raw, list):
                for m in mods_raw:
                    if isinstance(m, dict):
                        items.append(Module(**m))
            return items
        except Exception as e:
            log.warning(f"Convex list_modules error | err={e}")
    return _memory_modules.get(course_id, [])


@app.get("/courses/{course_id}/modules/{module_id}", response_model=Module)
async def get_module(course_id: str, module_id: str):
    if convex.enabled:
        try:
            mods_raw = await convex.query("modules:listByCourse", {"courseId": course_id})
            if isinstance(mods_raw, list):
                for m in mods_raw:
                    if isinstance(m, dict) and str(m.get("moduleId")) == str(module_id):
                        return Module(**m)
        except Exception as e:
            log.warning(f"Convex get_module error | err={e}")
    # fallback
    mods = _memory_modules.get(course_id, [])
    for m in mods:
        if m.moduleId == str(module_id):
            return m
    raise HTTPException(status_code=404, detail="Module not found")


@app.patch("/courses/{course_id}/modules/{module_id}", response_model=Module)
async def upsert_module(course_id: str, module_id: str, payload: ModuleUpdate):
    if convex.enabled:
        try:
            args: Dict[str, Any] = {"courseId": course_id, "moduleId": module_id}
            for k in (
                "title",
                "outline",
                "text",
                "manimCode",
                "imageStorageId",
                "imageCaption",
                "videoStorageId",
            ):
                v = getattr(payload, k, None)
                if v is not None:
                    args[k] = v
            await convex.mutation("modules:upsert", args)
            # Return the current module by refetching list and filtering
            mods = await list_modules(course_id)
            for m in mods:
                if m.moduleId == module_id:
                    return m
            # If not found in list, construct from payload
            return Module(courseId=course_id, moduleId=module_id, **payload.model_dump(exclude_none=True))
        except Exception as e:
            log.warning(f"Convex upsert_module error | err={e}")
    # fallback in-memory upsert
    mods = _memory_modules.setdefault(course_id, [])
    existing = None
    for i, m in enumerate(mods):
        if m.moduleId == module_id:
            existing = i
            break
    base = Module(courseId=course_id, moduleId=module_id)
    data = base.model_dump()
    data.update({k: v for k, v in payload.model_dump(exclude_none=True).items()})
    mod = Module(**data)
    if existing is not None:
        mods[existing] = mod
    else:
        mods.append(mod)
    _memory_modules[course_id] = mods
    return mod


@app.delete("/courses/{course_id}/modules/{module_id}")
async def delete_module(course_id: str, module_id: str):
    if convex.enabled:
        try:
            result = await convex.mutation("modules:delete_", {"courseId": course_id, "moduleId": module_id})
            if not result:
                raise HTTPException(status_code=404, detail="Module not found")
            return {"deleted": True, "courseId": course_id, "moduleId": module_id}
        except Exception as e:
            log.warning(f"Convex delete_module error | err={e}")
    # fallback memory delete
    mods = _memory_modules.get(course_id, [])
    for i, m in enumerate(mods):
        if m.moduleId == module_id:
            mods.pop(i)
            _memory_modules[course_id] = mods
            return {"deleted": True, "courseId": course_id, "moduleId": module_id}
    raise HTTPException(status_code=404, detail="Module not found")


@app.post("/courses/{course_id}/modules/{module_id}/recompile", response_model=Module)
async def recompile_module(course_id: str, module_id: str):
    # Resolve current module + manim code
    manim_code: str = ""
    module_title: str = f"Module {module_id}"
    existing: Optional[Module] = None

    if convex.enabled:
        try:
            mods_raw = await convex.query("modules:listByCourse", {"courseId": course_id})
            if isinstance(mods_raw, list):
                for m in mods_raw:
                    if isinstance(m, dict) and str(m.get("moduleId")) == str(module_id):
                        manim_code = str(m.get("manimCode") or "")
                        module_title = str(m.get("title") or module_title)
                        existing = Module(**m)
                        break
        except Exception as e:
            log.warning(f"Convex fetch module for recompile failed | err={e}")
    else:
        # memory fallback
        mods = _memory_modules.get(course_id, [])
        for m in mods:
            if m.moduleId == str(module_id):
                manim_code = m.manimCode or ""
                module_title = m.title or module_title
                existing = m
                break

    # Compile
    from .ai.compile_manim import compile_manim_to_mp4
    try:
        path = await asyncio.to_thread(compile_manim_to_mp4, str(module_id), manim_code)
    except Exception as e:
        log.warning(f"Manim compile exception | module={module_id} | err={e}")
        path = None
    if not path:
        raise HTTPException(status_code=500, detail="Compile failed")

    # Upload to Convex and patch module
    updated: Optional[Module] = None
    if convex.enabled:
        try:
            upload_url = await convex_generate_upload_url(convex)
            if not upload_url:
                raise RuntimeError("Upload URL unavailable")
            with open(path, "rb") as f:
                vid_bytes = f.read()
            storage_id = await convex_put_bytes(upload_url, vid_bytes, content_type="video/mp4")
            if not storage_id:
                raise RuntimeError("Upload failed")
            await convex.mutation("modules:upsert", {
                "courseId": course_id,
                "moduleId": module_id,
                "videoStorageId": storage_id,
            })
            # refetch
            mods_raw = await convex.query("modules:listByCourse", {"courseId": course_id})
            if isinstance(mods_raw, list):
                for m in mods_raw:
                    if isinstance(m, dict) and str(m.get("moduleId")) == str(module_id):
                        updated = Module(**m)
                        break
        except Exception as e:
            log.warning(f"Convex upload/patch failed | module={module_id} | err={e}")
            raise HTTPException(status_code=500, detail="Upload failed")
    else:
        # Update memory only; no hosting available
        mods = _memory_modules.setdefault(course_id, [])
        for i, m in enumerate(mods):
            if m.moduleId == str(module_id):
                mods[i] = Module(**{**m.model_dump(), **{"videoStorageId": None}})
                updated = mods[i]
                break
        _memory_modules[course_id] = mods

    return updated or existing or Module(courseId=course_id, moduleId=str(module_id))


@app.get("/stats", response_model=Stats)
async def get_stats():
    if convex.enabled:
        try:
            log.info("Convex stats start")
            data = await convex.query("stats:get", {})
            # Ensure shape matches expected schema
            if not isinstance(data, dict):
                raise ValueError("Invalid stats shape")
            if not all(k in data for k in ("total_courses", "active_teachers", "recent_activity")):
                raise ValueError("Missing stats fields")
            log.info("Convex stats ok")
            return Stats(**data)
        except Exception as e:
            log.warning(f"Convex stats error | err={e}")
            # compute from Convex courses as a backup
            try:
                courses_raw = await convex.query("courses:list", {})
                courses_list = courses_raw if isinstance(courses_raw, list) else []
                total = len(courses_list)
                recent = courses_list[-5:] if total else []
                activities = []
                for c in recent:
                    cid = (c.get('id') if isinstance(c, dict) else '') or ''
                    ts = (c.get('updated_at') if isinstance(c, dict) else None) or now_iso()
                    activities.append(Activity(course_id=cid, event="updated", timestamp=ts))
                return Stats(total_courses=total, active_teachers=1 if total else 0, recent_activity=activities)
            except Exception:
                pass
    return _fallback_stats()


# --- AI endpoints ---

def _create_memory_ai_course_doc(payload: AICourseRequest) -> Course:
    now = now_iso()
    course = Course(
        id=str(uuid4()),
        title=payload.title or payload.topic,
        progress=0,
        created_at=now,
        updated_at=now,
        status="creating",
    )
    _memory_courses.append(course)
    return course


async def _update_progress(target_id: Optional[str], status: str, progress: int):
    # Update Convex if configured
    if convex.enabled and target_id:
        try:
            log.info(f"Convex updateProgress | courseId={target_id} | status={status} | progress={progress}")
            await convex.mutation("courses:updateProgress", {"courseId": target_id, "status": status, "progress": progress})
        except Exception:
            pass
    # Also update in-memory if present
    for i, c in enumerate(_memory_courses):
        if target_id and c.id == target_id:
            _memory_courses[i] = Course(
                id=c.id,
                title=c.title,
                progress=progress,
                created_at=c.created_at,
                updated_at=now_iso(),
                status=status if status else c.status,
            )
            break


@app.post("/ai/build", response_model=AICourseResponse)
async def ai_build(payload: AICourseRequest):
    thread_id = str(uuid4())
    log.info(f"/ai/build start | thread={thread_id} | topic={payload.topic} | level={payload.level} | title={payload.title}")

    # Map UI fields to agent constraints
    constraints = dict(payload.constraints or {})
    constraints.update({
        "title": payload.title,
        "description": payload.description,
        "instructor": payload.instructor,
        "audience": payload.audience,
        "level_label": payload.level_label,
        "duration_weeks": payload.duration_weeks,
        "category": payload.category,
        "age_range": payload.age_range,
        "language": payload.language,
        "learning_outcomes": payload.learning_outcomes,
        "prerequisites": payload.prerequisites,
    })

    # Immediate course doc for progress tracking
    course_id: Optional[str] = None
    # Create Convex course up-front for progress updates if possible
    if convex.enabled:
        try:
            doc = await convex.mutation("courses:createDetailed", {
                "topic": payload.topic,
                "level": payload.level,
                "moduleCount": 0,
                "moduleIds": [],
                "createdAt": __import__("time").time(),
                "title": payload.title,
                "description": payload.description,
                "instructor": payload.instructor,
                "audience": payload.audience,
                "levelLabel": payload.level_label,
                "durationWeeks": payload.duration_weeks,
                "category": payload.category,
                "ageRange": payload.age_range,
                "language": payload.language,
                "status": "creating",
                "progress": 0,
            })
            if isinstance(doc, dict):
                course_id = doc.get("id") or doc.get("_id")
            log.info(f"Convex pre-createDetailed ok | courseId={course_id}")
        except Exception:
            course_id = None
            # Fallback to minimal create if detailed function is not available
            try:
                min_doc = await convex.mutation("courses:create", {"title": payload.title or payload.topic})
                if isinstance(min_doc, dict):
                    course_id = min_doc.get("id") or min_doc.get("_id")
                    log.info(f"Convex pre-create fallback ok | courseId={course_id}")
            except Exception:
                course_id = None

    # Create memory record mirroring the course
    mem_course = _create_memory_ai_course_doc(payload)
    # Map thread to course tracking
    _threads[thread_id] = {"course_id": course_id or mem_course.id, "progress": 0, "status": "creating"}

    async def progress_cb(pct: int, status: str):
        _threads[thread_id]["progress"] = pct
        _threads[thread_id]["status"] = status
        await _update_progress(course_id or mem_course.id, status, pct)
        log.info(f"progress | thread={thread_id} | status={status} | {pct}%")

    # Run build (synchronous for now)
    try:
        course_package = await run_course_build(
            topic=payload.topic,
            level=payload.level,
            constraints=constraints,
            convex=convex,
            progress_cb=progress_cb,
            existing_course_id=course_id,
        )
        _threads[thread_id]["course"] = course_package
        # Final status
        await _update_progress(course_id or mem_course.id, "ready", 100)
        log.info(f"/ai/build done | thread={thread_id} | status=ready")
    except Exception as e:
        _threads[thread_id]["error"] = str(e)
        await _update_progress(course_id or mem_course.id, "failed", 100)
        log.error(f"/ai/build failed | thread={thread_id} | err={e}")
        raise HTTPException(status_code=500, detail=f"Build failed: {e}")

    return AICourseResponse(thread_id=thread_id, course=_threads[thread_id].get("course", {}))


@app.get("/ai/stream")
async def ai_stream(thread_id: str):
    async def event_gen():
        # Simple polling loop for this thread; in real use you'd push updates
        import asyncio as _asyncio
        for _ in range(100):
            info = _threads.get(thread_id) or {}
            yield f"data: {info}\n\n"
            if (info.get("status") == "ready") or (info.get("status") == "failed"):
                break
            await _asyncio.sleep(1)
    return StreamingResponse(event_gen(), media_type="text/event-stream")


@app.get("/files/convex-url")
async def get_convex_file_url(storageId: str):
    if not storageId:
        raise HTTPException(status_code=400, detail="storageId required")
    if convex.enabled:
        try:
            url = await convex.run("files:getUrl", {"storageId": storageId})
            if isinstance(url, str) and url:
                return {"url": url}
        except Exception as e:
            log.warning(f"Convex getUrl error | id={storageId} | err={e}")
    raise HTTPException(status_code=404, detail="URL not available")
