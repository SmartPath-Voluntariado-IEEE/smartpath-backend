from datetime import UTC, datetime

from database.database import get_admin_client, get_db_client
from schemas.achievement import SyncAchievementsRequest

DEFAULT_ACHIEVEMENTS = [
    {
        "id": "first-module-passed",
        "title": "Primer Paso",
        "description": "Aprueba tu primera evaluación de módulo con éxito.",
        "category": "modules",
        "icon_name": "Target",
        "badge_color": "purple",
        "criteria_type": "passed_modules_count",
        "criteria_value": 1,
        "xp_points": 50,
    },
    {
        "id": "perfect-score",
        "title": "Puntaje Perfecto",
        "description": "Obtén una calificación perfecta del 100% en cualquier test.",
        "category": "quizzes",
        "icon_name": "Award",
        "badge_color": "emerald",
        "criteria_type": "perfect_score",
        "criteria_value": 1,
        "xp_points": 100,
    },
    {
        "id": "three-modules-passed",
        "title": "Explorador Imparable",
        "description": "Completa 3 módulos evaluados satisfactoriamente.",
        "category": "modules",
        "icon_name": "Zap",
        "badge_color": "indigo",
        "criteria_type": "passed_modules_count",
        "criteria_value": 3,
        "xp_points": 150,
    },
    {
        "id": "course-completed",
        "title": "Curso Conquistado",
        "description": "Aprueba todos los módulos de un curso activo.",
        "category": "courses",
        "icon_name": "BookOpen",
        "badge_color": "amber",
        "criteria_type": "completed_course",
        "criteria_value": 1,
        "xp_points": 200,
    },
    {
        "id": "level-1-mastered",
        "title": "Fundamentos Dominados",
        "description": "Domina todas las habilidades clave del Nivel 1 en tu Roadmap.",
        "category": "roadmap",
        "icon_name": "Trophy",
        "badge_color": "orange",
        "criteria_type": "level_completed",
        "criteria_value": 1,
        "xp_points": 300,
    },
    {
        "id": "streak-active",
        "title": "Hábito de Hierro",
        "description": "Mantén una racha de estudio activa en la plataforma.",
        "category": "streak",
        "icon_name": "Flame",
        "badge_color": "orange",
        "criteria_type": "streak_days",
        "criteria_value": 3,
        "xp_points": 100,
    },
]


class AchievementService:

    @staticmethod
    def get_all_achievements() -> list[dict]:
        try:
            supabase = get_admin_client()
            result = supabase.table("achievements").select("*").execute()
            if result.data and len(result.data) > 0:
                return result.data
        except Exception as e:
            print(f"⚠️ [ACHIEVEMENTS] Fallback a logros en memoria: {e}")
        return DEFAULT_ACHIEVEMENTS

    @staticmethod
    def get_user_achievements(user_id: str, token: str | None = None) -> list[dict]:
        try:
            supabase = get_db_client(token) if token else get_admin_client()
            res = (
                supabase.table("user_achievements")
                .select("achievement_id, unlocked_at, metadata, achievements(*)")
                .eq("user_id", user_id)
                .execute()
            )

            if res.data:
                unlocked = []
                for item in res.data:
                    ach = item.get("achievements") or {}
                    ach_id = item.get("achievement_id")
                    if not ach:
                        ach = next((a for a in DEFAULT_ACHIEVEMENTS if a["id"] == ach_id), {})

                    unlocked.append({
                        "achievement_id": ach_id,
                        "title": ach.get("title", ach_id),
                        "description": ach.get("description", ""),
                        "icon_name": ach.get("icon_name", "Trophy"),
                        "badge_color": ach.get("badge_color", "purple"),
                        "category": ach.get("category", "general"),
                        "xp_points": ach.get("xp_points", 50),
                        "unlocked_at": item.get("unlocked_at"),
                        "metadata": item.get("metadata") or {},
                    })
                return unlocked
        except Exception as e:
            print(f"⚠️ [ACHIEVEMENTS] Error al consultar logros de usuario {user_id}: {e}")

        return []

    @staticmethod
    def unlock_achievement(
        user_id: str,
        achievement_id: str,
        metadata: dict | None = None,
        token: str | None = None,
    ) -> bool:
        try:
            supabase = get_db_client(token) if token else get_admin_client()
            payload = {
                "user_id": user_id,
                "achievement_id": achievement_id,
                "unlocked_at": datetime.now(UTC).isoformat(),
                "metadata": metadata or {},
            }
            supabase.table("user_achievements").upsert(payload).execute()
            return True
        except Exception as e:
            print(f"⚠️ [ACHIEVEMENTS] Error al desbloquear logro {achievement_id} para {user_id}: {e}")
            return False

    @staticmethod
    def sync_and_evaluate(
        user_id: str,
        sync_req: SyncAchievementsRequest,
        token: str | None = None,
    ) -> list[dict]:
        to_unlock: list[str] = []

        if sync_req.passed_modules_count >= 1:
            to_unlock.append("first-module-passed")
        if sync_req.passed_modules_count >= 3:
            to_unlock.append("three-modules-passed")
        if sync_req.last_quiz_score == 100 or sync_req.perfect_score_count >= 1:
            to_unlock.append("perfect-score")
        if sync_req.completed_courses_count >= 1:
            to_unlock.append("course-completed")
        if sync_req.level_1_mastered:
            to_unlock.append("level-1-mastered")
        if sync_req.streak_days >= 3:
            to_unlock.append("streak-active")

        for ach_id in to_unlock:
            AchievementService.unlock_achievement(user_id, ach_id, token=token)

        return AchievementService.get_user_achievements(user_id, token=token)
