from database.database import get_admin_client, get_db_client


class CourseProgressService:

    @staticmethod
    def select_course_for_skill(
        user_id: str, skill_slug: str, course_id: int, token: str
    ) -> dict:
        supabase = get_db_client(token)

        existing = (
            supabase.table("user_skill_courses")
            .select("id")
            .eq("user_id", user_id)
            .eq("skill_slug", skill_slug)
            .limit(1)
            .execute()
        )

        row = {
            "user_id": user_id,
            "skill_slug": skill_slug,
            "course_id": course_id,
        }

        if existing.data:
            
            CourseProgressService._reset_progress_for_skill(
                user_id, skill_slug, token
            )
            supabase.table("user_skill_courses").update(row).eq(
                "user_id", user_id
            ).eq("skill_slug", skill_slug).execute()
        else:
            supabase.table("user_skill_courses").insert(row).execute()

        return row

    @staticmethod
    def unlink_course_from_skill(user_id: str, skill_slug: str, token: str):
        CourseProgressService._reset_progress_for_skill(user_id, skill_slug, token)

        supabase = get_db_client(token)
        supabase.table("user_skill_courses").delete().eq(
            "user_id", user_id
        ).eq("skill_slug", skill_slug).execute()

    @staticmethod
    def _reset_progress_for_skill(user_id: str, skill_slug: str, token: str):
        admin = get_admin_client()

        current = (
            admin.table("user_skill_courses")
            .select("course_id")
            .eq("user_id", user_id)
            .eq("skill_slug", skill_slug)
            .limit(1)
            .execute()
        )

        if not current.data:
            return

        course_id = current.data[0]["course_id"]

        modules = (
            admin.table("course_modules")
            .select("id")
            .eq("course_id", course_id)
            .execute()
        )

        module_ids = [m["id"] for m in (modules.data or [])]

        if not module_ids:
            return

        supabase = get_db_client(token)
        supabase.table("user_module_completion").delete().eq(
            "user_id", user_id
        ).in_("module_id", module_ids).execute()

    @staticmethod
    def get_course_progress(user_id: str, course_id: int, token: str) -> dict:
        admin = get_admin_client()
        supabase = get_db_client(token)
        user_skills_result = (
            supabase.table("user_skills")
            .select("level, skills(slug)")
            .eq("user_id", user_id)
            .execute()
        )

        user_skill_levels = {}

        for item in user_skills_result.data or []:
            skill_info = item.get("skills")
            if skill_info and skill_info.get("slug"):
                user_skill_levels[skill_info["slug"]] = item.get("level", 0)

        modules = (
            admin.table("course_modules")
            .select("id")
            .eq("course_id", course_id)
            .execute()
        )

        module_ids = [m["id"] for m in (modules.data or [])]
        total = len(module_ids)

        if total == 0:
            return {"completed": 0, "total": 0, "percentage": 0.0}

        supabase = get_db_client(token)
        completed_result = (
            supabase.table("user_module_completion")
            .select("module_id")
            .eq("user_id", user_id)
            .eq("passed", True)
            .in_("module_id", module_ids)
            .execute()
        )

        completed = len(completed_result.data or [])

        return {
            "completed": completed,
            "total": total,
            "percentage": round(completed / total * 100, 2),
        }

    @staticmethod
    def get_dashboard_summary(
        user_id: str,
        roadmap_skills: list[dict],
        token: str,
    ) -> list[dict]:
        """roadmap_skills: [{"skill_slug": "python", ...}, ...] de tu roadmap actual."""
        supabase = get_db_client(token)
        admin = get_admin_client()

        user_skills_result = (
            supabase.table("user_skills")
            .select("level, skills(slug)")
            .eq("user_id", user_id)
            .execute()
        )

        user_skill_levels = {}

        for item in user_skills_result.data or []:
            skill_info = item.get("skills")
            if skill_info and skill_info.get("slug"):
                user_skill_levels[skill_info["slug"]] = item.get("level", 0)

        summary = []
        for skill in roadmap_skills:
            slug = skill["skill_slug"]

            selection = (
                supabase.table("user_skill_courses")
                .select("course_id")
                .eq("user_id", user_id)
                .eq("skill_slug", slug)
                .limit(1)
                .execute()
            )

            if not selection.data:
                summary.append({
                    "skill_slug": slug,
                    "course_id": None,
                    "course_title": None,
                    "course_url": None,
                    "progress": None,
                })
                continue

            course_id = selection.data[0]["course_id"]

            
            course_info = (
                admin.table("courses")
                .select("title, url")
                .eq("id", course_id)
                .limit(1)
                .execute()
            )
            course = course_info.data[0] if course_info.data else {}

            progress = CourseProgressService.get_course_progress(
                user_id, course_id, token
            )

            initial_level = user_skill_levels.get(slug, 0)
            initial_percentage = min(max(initial_level * 20, 0), 100)

            remaining_percentage = 100 - initial_percentage

            module_weight = (
                remaining_percentage / progress["total"]
                if progress["total"] > 0
                else 0
            )

            skill_percentage = round(
                initial_percentage + progress["completed"] * module_weight,
                2,
            )

            progress["skill_percentage"] = skill_percentage

            summary.append({
                "skill_slug": slug,
                "course_id": course_id,
                "course_title": course.get("title"),
                "course_url": course.get("url"),
                "progress": progress,
            })

        return summary