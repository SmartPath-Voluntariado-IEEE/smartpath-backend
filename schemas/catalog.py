from datetime import date, datetime

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


# ============================================
# BOLSA LABORAL (HU-57 / HU-58)
# ============================================

class JobRequirementItem(BaseModel):
    """Requisito no técnico extraído de la descripción (HU-58)."""

    type: str  # experiencia | educacion | idioma | contrato | modalidad
    label: str
    value: str | int | None = None


class ScrapedJobResponse(BaseModel):
    """
    Oferta recolectada por scraping, con lo que HU-58 extrajo de ella.

    Extiende a JobResponse en vez de reemplazarla porque el dashboard y el
    resumen de mercado ya consumen la forma anterior.
    """

    id: int
    company: str | None = None
    position: str | None = None
    location: str | None = None
    description: str | None = None
    seniority: str | None = None
    posted_at: date | None = None

    # HU-57: procedencia y frescura
    source: str | None = None
    url: str | None = None
    is_remote: bool | None = None
    job_type: str | None = None
    scraped_at: datetime | None = None

    # HU-57: salario tal como lo publica el portal
    salary: int | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    salary_currency: str | None = None
    salary_interval: str | None = None

    # HU-58: habilidades y requisitos
    skill_slugs: list[str] = []
    required_skills: list[str] = []
    desirable_skills: list[str] = []
    experience_years_min: int | None = None
    education_level: str | None = None
    english_required: bool | None = None
    requirements: list[JobRequirementItem] = []


class JobRecommendationItem(BaseModel):
    """Una oferta puntuada contra la ruta del usuario."""

    job: ScrapedJobResponse

    match_percentage: int          # 0-100, puntaje final
    alignment_percentage: int      # cuánto tiene que ver con la ruta
    readiness_percentage: int      # cuánto de lo exigido ya domina

    matched_skills: list[str]
    missing_skills: list[str]
    missing_from_route: list[str]  # lo que falta y la ruta sí enseña
    route_skills: list[str]
    required_skills: list[str]
    desirable_skills: list[str]
    seniority_fit: bool


class JobRecommendationsResponse(BaseModel):
    target_role_id: str
    target_role_label: str | None = None
    route_skills: list[str]
    user_skills: list[str]
    total: int
    results: list[JobRecommendationItem]


class JobScrapeResponse(BaseModel):
    """Resultado de una corrida del recolector (HU-57)."""

    message: str
    search_terms: list[str] = []
    sites: list[str] = []
    collected: int = 0
    saved: int = 0
    errors: list[dict] = []
    requirements: dict | None = None
