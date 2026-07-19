from pydantic import BaseModel
from typing import Optional, List
from datetime import date

class SkillResponse(BaseModel):
    id: int
    slug: str
    name: str
    category: str
    description: Optional[str] = None
    difficulty: int
    aliases: Optional[List[str]] = None

class JobResponse(BaseModel):
    id: int
    company: Optional[str] = None
    position: Optional[str] = None
    salary: Optional[int] = None
    seniority: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    posted_at: Optional[date] = None

class CourseResponse(BaseModel):
    id: int
    platform: Optional[str] = None
    title: Optional[str] = None
    duration_hours: Optional[int] = None
    price: Optional[str] = None
    rating: Optional[float] = None
    level: Optional[str] = None
    url: Optional[str] = None
    skill_slugs: List[str] = []

class RoleTargetResponse(BaseModel):
    id: str
    label: str
    core_skill_slugs: List[str] = []
