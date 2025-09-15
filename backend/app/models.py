from __future__ import annotations
from typing import List, Literal, Optional, Any
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

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    description: Optional[str] = None
    instructor: Optional[str] = None
    audience: Optional[str] = None
    level_label: Optional[str] = None
    duration_weeks: Optional[int] = None
    category: Optional[str] = None
    age_range: Optional[str] = None
    language: Optional[str] = None

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


# --- Modules & Course Detail ---
class Module(BaseModel):
    courseId: str
    moduleId: str
    title: Optional[str] = None
    outline: List[Any] = []
    text: Optional[str] = ""
    manimCode: Optional[str] = ""
    imageStorageId: Optional[str] = None
    imageCaption: Optional[str] = None
    videoStorageId: Optional[str] = None


class ModuleUpdate(BaseModel):
    title: Optional[str] = None
    outline: Optional[List[Any]] = None
    text: Optional[str] = None
    manimCode: Optional[str] = None
    imageStorageId: Optional[str] = None
    imageCaption: Optional[str] = None
    videoStorageId: Optional[str] = None


class CourseDetail(Course):
    description: Optional[str] = None
    instructor: Optional[str] = None
    audience: Optional[str] = None
    level_label: Optional[str] = None
    duration_weeks: Optional[int] = None
    category: Optional[str] = None
    age_range: Optional[str] = None
    language: Optional[str] = None
    modules: List[Module] = []
