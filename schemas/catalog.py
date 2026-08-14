from datetime import date

from pydantic import BaseModel


class SkillResponse(BaseModel):
    id: int
    slug: str
    name: str
    category: str
    description: str | None = None
    difficulty: int
    aliases: list[str] | None = None

class JobResponse(BaseModel):
    id: int
    company: str | None = None
    position: str | None = None
    salary: int | None = None
    seniority: str | None = None
    description: str | None = None
    location: str | None = None
    posted_at: date | None = None

class CourseResponse(BaseModel):
    id: int
    platform: str | None = None
    institution: str | None = None
    title: str | None = None
    duration_hours: int | None = None
    language: str | None = None
    price: str | None = None
    is_free: bool = False
    rating: float | None = None
    level: str | None = None
    url: str | None = None
    skill_slugs: list[str] = []

class RoleTargetResponse(BaseModel):
    id: str
    label: str
    core_skill_slugs: list[str] = []
