
from pydantic import BaseModel

from schemas.catalog import RoleTargetResponse


class MarketSkillStat(BaseModel):
    skill_slug: str
    name: str
    count: int
    frequency: float
    category: str

class MasteredSkill(BaseModel):
    skill_slug: str
    name: str
    level: int
    marketFreq: float

class PartialSkill(BaseModel):
    skill_slug: str
    name: str
    level: int
    marketFreq: float

class MissingSkill(BaseModel):
    skill_slug: str
    name: str
    marketFreq: float
    priority: float

class GapAnalysisResponse(BaseModel):
    target_role: RoleTargetResponse
    mastered: list[MasteredSkill] = []
    partial: list[PartialSkill] = []
    missing: list[MissingSkill] = []
    coverage: float

class RoadmapSkill(BaseModel):
    skill_slug: str
    name: str
    marketFreq: float
    estHours: int

class RoadmapLevel(BaseModel):
    level: int
    label: str
    skills: list[RoadmapSkill] = []

class CourseRecommendation(BaseModel):
    title: str
    platform: str
    url: str
    price: str
    rating: float
    hours: int
    level: str
    style: str
    why: str
