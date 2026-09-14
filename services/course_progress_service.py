from core.cache import invalidate, ttl_cache
from database.database import get_admin_client, get_db_client


class CourseProgressService:

    @staticmethod
    def select_course_for_skill(
        user_id: str, skill_slug: str, course_id: int, token: str
    ) -> dict:
        invalidate("user:progress_summary")
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
        invalidate("user:progress_summary")
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
    @ttl_cache("user:progress_summary", ttl_seconds=60)
    def get_dashboard_summary(
        user_id: str,
        roadmap_skills: list[dict],
        token: str,
    ) -> list[dict]:
        """roadmap_skills: [{"skill_slug": "python", ...}, ...] de tu roadmap actual."""
        supabase = get_db_client(token)
        admin = get_admin_client()

        # 1. Traer niveles declarados de user_skills (1 viaje)
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

        # 2. Traer todos los cursos vinculados del usuario de una sola vez (1 viaje)
        user_courses_resp = (
            supabase.table("user_skill_courses")
            .select("skill_slug, course_id")
            .eq("user_id", user_id)
            .execute()
        )
        user_courses_by_slug = {
            row["skill_slug"]: row["course_id"]
            for row in (user_courses_resp.data or [])
            if row.get("skill_slug")
        }

        course_ids = list({cid for cid in user_courses_by_slug.values() if cid})
        courses_by_id = {}
        modules_by_course: dict[int, list[str]] = {cid: [] for cid in course_ids}
        all_module_ids = []

        # 3. Traer cursos y módulos en bloque (máx 2 viajes)
        if course_ids:
            courses_resp = (
                admin.table("courses")
                .select("id, title, url")
                .in_("id", course_ids)
                .execute()
            )
            courses_by_id = {c["id"]: c for c in (courses_resp.data or [])}

            modules_resp = (
                admin.table("course_modules")
                .select("id, course_id")
                .in_("course_id", course_ids)
                .execute()
            )
            for m in (modules_resp.data or []):
                modules_by_course.setdefault(m["course_id"], []).append(m["id"])
                all_module_ids.append(m["id"])

        # 4. Traer módulos completados por el usuario en bloque (1 viaje)
        passed_module_ids = set()
        if all_module_ids:
            completed_resp = (
                supabase.table("user_module_completion")
                .select("module_id")
                .eq("user_id", user_id)
                .eq("passed", True)
                .in_("module_id", all_module_ids)
                .execute()
            )
            passed_module_ids = {
                r["module_id"] for r in (completed_resp.data or [])
            }

        summary = []
        for skill in roadmap_skills:
            slug = skill["skill_slug"]
            course_id = user_courses_by_slug.get(slug)

            if not course_id:
                summary.append({
                    "skill_slug": slug,
                    "course_id": None,
                    "course_title": None,
                    "course_url": None,
                    "progress": None,
                })
                continue

            course = courses_by_id.get(course_id, {})
            mod_ids = modules_by_course.get(course_id, [])
            total = len(mod_ids)
            completed = sum(1 for mid in mod_ids if mid in passed_module_ids)
            percentage = round(completed / total * 100, 2) if total > 0 else 0.0

            initial_level = user_skill_levels.get(slug, 0)
            initial_percentage = min(max(initial_level * 20, 0), 100)
            remaining_percentage = 100 - initial_percentage
            module_weight = (remaining_percentage / total) if total > 0 else 0
            skill_percentage = round(
                initial_percentage + completed * module_weight, 2
            )

            summary.append({
                "skill_slug": slug,
                "course_id": course_id,
                "course_title": course.get("title"),
                "course_url": course.get("url"),
                "progress": {
                    "completed": completed,
                    "total": total,
                    "percentage": percentage,
                    "skill_percentage": skill_percentage,
                },
            })

        return summary

    @staticmethod
    def get_skill_effective_progress(
        user_id: str, skill_slug: str, token: str
    ) -> dict:
        """
        Progreso efectivo de una sola skill: combina el nivel declarado en
        el perfil (user_skills, escala 1-5 -> 20% cada punto) con el avance
        real de módulos del curso vinculado a esa skill.

        Misma fórmula que usa get_dashboard_summary, pero para una sola
        skill (útil para el endpoint /users/skill-progress).
        """
        supabase = get_db_client(token)

        user_skill_result = (
            supabase.table("user_skills")
            .select("level, skills(slug)")
            .eq("user_id", user_id)
            .execute()
        )

        declared_level = 0
        for item in user_skill_result.data or []:
            skill_info = item.get("skills")
            if skill_info and skill_info.get("slug") == skill_slug:
                declared_level = item.get("level", 0)
                break

        base_percent = min(max(declared_level * 20, 0), 100)

        selection = (
            supabase.table("user_skill_courses")
            .select("course_id")
            .eq("user_id", user_id)
            .eq("skill_slug", skill_slug)
            .limit(1)
            .execute()
        )

        if not selection.data:
            return {
                "percent": round(base_percent, 2),
                "course_linked": False,
                "modules_completed": 0,
                "modules_total": 0,
            }

        course_id = selection.data[0]["course_id"]
        module_progress = CourseProgressService.get_course_progress(
            user_id, course_id, token
        )

        total = module_progress["total"]
        completed = module_progress["completed"]

        if total == 0:
            return {
                "percent": round(base_percent, 2),
                "course_linked": True,
                "modules_completed": 0,
                "modules_total": 0,
            }

        remaining = 100 - base_percent
        bonus = (completed / total) * remaining
        final_percent = min(100, base_percent + bonus)

        return {
            "percent": round(final_percent, 2),
            "course_linked": True,
            "modules_completed": completed,
            "modules_total": total,
        }