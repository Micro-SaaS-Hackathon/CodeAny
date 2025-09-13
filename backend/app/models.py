from __future__ import annotations
from typing import List, Literal
from pydantic import BaseModel, Field
from datetime import datetime

CourseStatus = Literal['draft', 'published', str]

class Course(BaseModel):
    id: str
    title: str
    progress: int = Field(ge=0, le=100)
    created_at: str
    updated_at: str
    status: str

class CourseCreate(BaseModel):
    title: str = 'Untitled Course'

class Activity(BaseModel):
    course_id: str
    event: str
    timestamp: str

class Stats(BaseModel):
    total_courses: int
    active_teachers: int
    recent_activity: List[Activity]


def now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'


# --- AI Course schemas ---
class AICourseRequest(BaseModel):
    topic: str
    level: str = 'beginner'
    title: str
    description: str
    instructor: str | None = None
    audience: str | None = None
    level_label: str | None = None
    duration_weeks: int | None = None
    category: str | None = None
    age_range: str | None = None
    language: Literal['en', 'az'] = 'en'
    learning_outcomes: List[str] = []
    prerequisites: List[str] = []
    constraints: dict = {}


class AICourseResponse(BaseModel):
    thread_id: str
    course: dict
