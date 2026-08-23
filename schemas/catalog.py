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
    skill_slugs: list[str] = []

class CourseResponse(BaseModel):
    id: int
    platform: str | None = None
    institution: str | None = None
    title: str | None = None
    instructor: str | None = None
    duration_hours: int | None = None
    language: str | None = None
    price: str | None = None
    is_free: bool = False
    rating: float | None = None
    level: str | None = None
    certificate: bool = False
    url: str | None = None
    skill_slugs: list[str] = []

class RoleTargetResponse(BaseModel):
    id: str
    label: str
    core_skill_slugs: list[str] = []


# ============================================
# MARKET OVERVIEW
# ============================================

class SkillDemandItem(BaseModel):
    slug: str
    name: str
    category: str
    count: int
    frequency: float  # 0.0 - 1.0

class SalaryRange(BaseModel):
    min: int | None = None
    max: int | None = None
    avg: int | None = None
    count: int = 0

class MarketOverviewResponse(BaseModel):
    total_jobs: int
    skill_demand: list[SkillDemandItem]
    salary_ranges: dict[str, SalaryRange]
    top_companies: list[str]


# ============================================
# JOB MATCH
# ============================================

class JobMatchResponse(BaseModel):
    job: JobResponse
    match_percentage: int  # 0-100
    matched_skills: list[str]
    missing_skills: list[str]
