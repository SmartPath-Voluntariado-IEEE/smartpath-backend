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
            "course": result.data[0],
        }