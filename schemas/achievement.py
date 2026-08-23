from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class AchievementResponse(BaseModel):
    id: str
    title: str
    description: str
    category: str = "general"
    icon_name: str
    badge_color: str = "purple"
    criteria_type: str
    criteria_value: int = 1
    xp_points: int = 50

    model_config = ConfigDict(from_attributes=True)


class UserAchievementResponse(BaseModel):
    achievement_id: str
    title: str
    description: str
    icon_name: str
    badge_color: str
    category: str
    xp_points: int
    unlocked_at: datetime
    metadata: dict = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class UnlockAchievementRequest(BaseModel):
    achievement_id: str
    metadata: dict = Field(default_factory=dict)


class SyncAchievementsRequest(BaseModel):
    passed_modules_count: int = 0
    perfect_score_count: int = 0
    completed_courses_count: int = 0
    streak_days: int = 0
    level_1_mastered: bool = False
    last_quiz_score: float | None = None
