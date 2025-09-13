from __future__ import annotations
import os
from uuid import uuid4
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from .models import Course, CourseCreate, Stats, Activity, now_iso, AICourseRequest, AICourseResponse
from .convex_client import ConvexClient
from .ai import run_course_build
from .ai.logging_utils import get_logger

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
    return course


def _fallback_stats() -> Stats:
    total = len(_memory_courses)
    activities = [
        Activity(course_id=c.id, event="created", timestamp=c.created_at) for c in _memory_courses[-5:]
    ]
    return Stats(total_courses=total, active_teachers=1 if total else 0, recent_activity=activities)


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
            # expects Convex function name "courses:list"
            data = await convex.query("courses:list", {})
            # ensure each item matches Course fields
            return [Course(**item) for item in data]
        except Exception as e:
            # fall back if Convex missing
            print("Convex get_courses error:", e)
    return _fallback_list_courses()


@app.post("/courses", response_model=Course)
async def create_course(payload: CourseCreate):
    title = payload.title or "Untitled Course"
    if convex.enabled:
        try:
            data = await convex.mutation("courses:create", {"title": title})
            return Course(**data)
        except Exception as e:
            print("Convex create_course error:", e)
    return _fallback_create_course(title)


@app.get("/stats", response_model=Stats)
async def get_stats():
    if convex.enabled:
        try:
            data = await convex.query("stats:get", {})
            # Ensure shape matches expected schema
            if not isinstance(data, dict):
                raise ValueError("Invalid stats shape")
            if not all(k in data for k in ("total_courses", "active_teachers", "recent_activity")):
                raise ValueError("Missing stats fields")
            return Stats(**data)
        except Exception as e:
            print("Convex stats error:", e)
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
