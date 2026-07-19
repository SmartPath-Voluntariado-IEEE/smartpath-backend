from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    career: Optional[str] = None
    university: Optional[str] = None
    academic_cycle: Optional[int] = None
    english_level: Optional[str] = None
    experience_level: Optional[str] = None
    weekly_hours: Optional[int] = None
    professional_goal: Optional[str] = None

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
    weekly_hours: Optional[int] = None
    professional_goal: Optional[str] = None
    created_at: Optional[datetime] = None
