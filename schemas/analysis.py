
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
    # Score de priorización (HU-42): demanda + severidad de la brecha +
    # disponibilidad de cursos + intereses - tier.
    priority: float = 0.0
    courseCount: int = 0
    freeCourseCount: int = 0

class RoadmapLevel(BaseModel):
    level: int
    label: str
    skills: list[RoadmapSkill] = []
    estHours: int = 0
    # Horas acumuladas hasta el final de este nivel, y si esas horas caben en
    # el plazo del usuario (weekly_hours x target_months). El roadmap no se
    # recorta: informa hasta dónde alcanza.
    cumulativeHours: int = 0
    estimatedWeeks: int = 0
    withinTarget: bool = True

class CourseRecommendation(BaseModel):
    title: str
    platform: str
    # La fuente deja sin dato la mayoría de estos campos (de 582 cursos, 17
    # traen duración y 32 rating), así que son opcionales: exigirlos hacía
    # fallar la validación de la respuesta.
    institution: str | None = None
    url: str
    price: str | None = None
    is_free: bool = False
    language: str | None = None
    rating: float | None = None
    hours: int | None = None
    level: str | None = None
    style: str
    why: str
