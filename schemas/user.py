from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class UserSkillInput(BaseModel):
    skill_slug: str = Field(
        ...,
        min_length=1,
        max_length=50,
    )
    level: int = Field(
        ...,
        ge=1,
        le=5,
        description="Nivel de dominio entre 1 y 5",
    )

class UserProfileUpdate(BaseModel):
    full_name: str | None = None
    career: str | None = None
    university: str | None = None
    academic_cycle: int | None = None
    english_level: str | None = None
    experience_level: str | None = None
    role_experience: str | None = Field(
        default=None,
        max_length=2000,
        description="Experiencia previa relacionada con el rol objetivo",
    )
    weekly_hours: int | None = None
    target_months: int | None = 6
    professional_goal: str | None = None
    target_role_id: str | None = None
    interests: list[str] | None = None
    learning_preferences: list[str] | None = None
    skills: list[UserSkillInput] | None = None

class UserProfileResponse(BaseModel):
    id: UUID
    google_id: str | None = None
    full_name: str
    email: str
    career: str | None = None
    university: str | None = None
    academic_cycle: int | None = None
    english_level: str | None = None
    experience_level: str | None = None
    role_experience: str | None = None
    weekly_hours: int | None = None
    target_months: int | None = 6
    professional_goal: str | None = None
    target_role_id: str | None = None
    interests: list[str] | None = None
    learning_preferences: list[str] | None = None
    skills: list[UserSkillInput] = Field(default_factory=list)
    created_at: datetime | None = None
