from __future__ import annotations
import os
from uuid import uuid4
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .models import Course, CourseCreate, Stats, Activity, now_iso
from .convex_client import ConvexClient

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

# --- In-memory fallback (for local dev without Convex) ---
_memory_courses: List[Course] = []


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
            return Stats(**data)
        except Exception as e:
            print("Convex stats error:", e)
            # compute from Convex courses as a backup
            try:
                courses = await convex.query("courses:list", {})
                total = len(courses)
                activities = [
                    Activity(course_id=c.get('id',''), event="updated", timestamp=c.get('updated_at', now_iso()))
                    for c in courses[-5:]
                ]
                return Stats(total_courses=total, active_teachers=1 if total else 0, recent_activity=activities)
            except Exception:
                pass
    return _fallback_stats()
