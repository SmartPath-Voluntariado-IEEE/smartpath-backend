from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

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
    full_name: Optional[str] = None
    career: Optional[str] = None
    university: Optional[str] = None
    academic_cycle: Optional[int] = None
    english_level: Optional[str] = None
    experience_level: Optional[str] = None
    role_experience: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Experiencia previa relacionada con el rol objetivo",
    )
    weekly_hours: Optional[int] = None
    target_months: Optional[int] = 6
    professional_goal: Optional[str] = None
    target_role_id: Optional[str] = None
    interests: Optional[List[str]] = None
    learning_preferences: Optional[List[str]] = None
    skills: Optional[List[UserSkillInput]] = None

class UserProfileResponse(BaseModel):
    id: UUID
    google_id: Optional[str] = None
    full_name: str
    email: str
    career: Optional[str] = None
    university: Optional[str] = None
    academic_cycle: Optional[int] = None
    english_level: Optional[str] = None
    experience_level: Optional[str] = None
    role_experience: Optional[str] = None
    weekly_hours: Optional[int] = None
    target_months: Optional[int] = 6
    professional_goal: Optional[str] = None
    target_role_id: Optional[str] = None
    interests: Optional[List[str]] = None
    learning_preferences: Optional[List[str]] = None
    skills: List[UserSkillInput] = Field(default_factory=list)
    created_at: Optional[datetime] = None
