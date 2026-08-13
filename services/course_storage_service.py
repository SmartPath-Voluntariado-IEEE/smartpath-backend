from database.database import get_admin_client


class CourseStorageService:

    @staticmethod
    def save_course(course: dict) -> dict:

        supabase = get_admin_client()

        course_url = course.get("url")

        # Revisar si el curso ya existe
        if course_url:
            existing = (
                supabase.table("courses")
                .select("id")
                .eq("url", course_url)
                .limit(1)
                .execute()
            )

            if existing.data:
                return {
                    "status": "already_exists",
                    "course_id": existing.data[0]["id"],
                    "title": course.get("title"),
                }

        # Si no existe, guardarlo
        result = (
            supabase.table("courses")
            .insert(course)
            .execute()
        )

        return {
            "status": "created",
            "course_id": result.data[0]["id"],
            "course": result.data[0],
        }

    @staticmethod
    def get_skill_id_by_slug(skill_slug: str) -> str | None:
        supabase = get_admin_client()

        response = (
            supabase
            .table("skills")
            .select("id")
            .eq("slug", skill_slug)
            .limit(1)
            .execute()
        )

        if response.data:
            return response.data[0]["id"]

        return None

    @staticmethod
    def link_course_skill(course_id: str, skill_id: str) -> bool:
        supabase = get_admin_client()

        # Evitar duplicados en la tabla intermedia
        existing = (
            supabase
            .table("course_skills")
            .select("course_id")
            .eq("course_id", course_id)
            .eq("skill_id", skill_id)
            .limit(1)
            .execute()
        )

        if existing.data:
            return False  # ya estaba vinculado

        supabase.table("course_skills").insert({
            "course_id": course_id,
            "skill_id": skill_id,
        }).execute()

        return True