from core.cache import invalidate, ttl_cache
from database.database import get_admin_client, get_db_client


class CourseProgressService:

    @staticmethod
    def select_course_for_skill(
        user_id: str, skill_slug: str, course_id: int, token: str
    ) -> dict:
        invalidate("user:progress_summary")
        admin = get_admin_client()

        # 1. Registrar o actualizar en user_skill_courses
        existing = (
            admin.table("user_skill_courses")
            .select("id, course_id")
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
            admin.table("user_skill_courses").update({
                "course_id": course_id,
            }).eq("user_id", user_id).eq("skill_slug", skill_slug).execute()
        else:
            admin.table("user_skill_courses").insert(row).execute()

        # 2. Asegurar que el curso quede activo en user_module_completion para que persista
        try:
            first_mod = (
                admin.table("course_modules")
                .select("id")
                .eq("course_id", course_id)
                .order("module_order")
                .limit(1)
                .execute()
            )
            if first_mod.data:
                mid = first_mod.data[0]["id"]
                comp_check = (
                    admin.table("user_module_completion")
                    .select("module_id")
                    .eq("user_id", user_id)
                    .eq("module_id", mid)
                    .limit(1)
                    .execute()
                )
                if not comp_check.data:
                    admin.table("user_module_completion").insert({
                        "user_id": user_id,
                        "module_id": mid,
                        "score": 0,
                        "passed": False,
                        "attempts": 0,
                    }).execute()
        except Exception as e:
            print(f"⚠️ [SELECT COURSE] Error registrando módulo inicial: {e}")

        return {"user_id": user_id, "skill_slug": skill_slug, "course_id": course_id}

    @staticmethod
    def unlink_course_from_skill(
        user_id: str, skill_slug: str, token: str, course_id: int | None = None
    ):
        invalidate("user:progress_summary")
        admin = get_admin_client()

        if course_id:
            # Si el curso en user_skill_courses es el que se desvincula, eliminar la asignacion
            current = (
                admin.table("user_skill_courses")
                .select("course_id")
                .eq("user_id", user_id)
                .eq("skill_slug", skill_slug)
                .limit(1)
                .execute()
            )
            if current.data and current.data[0]["course_id"] == course_id:
                admin.table("user_skill_courses").delete().eq("user_id", user_id).eq("skill_slug", skill_slug).execute()

            # Eliminar intentos no aprobados de este curso
            c_mods = admin.table("course_modules").select("id").eq("course_id", course_id).execute()
            mids = [m["id"] for m in (c_mods.data or [])]
            if mids:
                admin.table("user_module_completion").delete().eq("user_id", user_id).eq("passed", False).in_("module_id", mids).execute()
        else:
            admin.table("user_skill_courses").delete().eq("user_id", user_id).eq("skill_slug", skill_slug).execute()

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

        admin = get_admin_client()
        admin.table("user_module_completion").delete().eq(
            "user_id", user_id
        ).in_("module_id", module_ids).execute()

    @staticmethod
    def get_course_progress(user_id: str, course_id: int, token: str = "") -> dict:
        admin = get_admin_client()
        user_skills_result = (
            admin.table("user_skills")
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

        completed_result = (
            admin.table("user_module_completion")
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
        token: str = "",
    ) -> list[dict]:
        """roadmap_skills: [{"skill_slug": "python", ...}, ...] de tu roadmap actual."""
        admin = get_admin_client()

        # 1. Traer niveles declarados de user_skills (1 viaje)
        user_skills_result = (
            admin.table("user_skills")
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
            admin.table("user_skill_courses")
            .select("skill_slug, course_id")
            .eq("user_id", user_id)
            .execute()
        )
        user_courses_by_slug: dict[str, list[int]] = {}
        all_course_ids = set()
        for row in (user_courses_resp.data or []):
            s_slug = row.get("skill_slug")
            c_id = row.get("course_id")
            if s_slug and c_id:
                base_slug = s_slug.split("__c__")[0]
                if c_id not in user_courses_by_slug.setdefault(base_slug, []):
                    user_courses_by_slug[base_slug].append(c_id)
                all_course_ids.add(c_id)

        # 3. Traer todos los módulos completados o intentados por el usuario
        user_completion_resp = (
            admin.table("user_module_completion")
            .select("module_id, passed")
            .eq("user_id", user_id)
            .execute()
        )
        user_attempted_mids = [r["module_id"] for r in (user_completion_resp.data or [])]
        passed_module_ids = {
            r["module_id"] for r in (user_completion_resp.data or []) if r.get("passed")
        }

        # Si el usuario tiene actividad en módulos, averiguar qué cursos son
        if user_attempted_mids:
            attempted_mods = (
                admin.table("course_modules")
                .select("id, course_id")
                .in_("id", user_attempted_mids)
                .execute()
            )
            for m in (attempted_mods.data or []):
                cid = m.get("course_id")
                if cid:
                    all_course_ids.add(cid)

        course_ids = list(all_course_ids)
        courses_by_id = {}
        modules_by_course: dict[int, list[str]] = {cid: [] for cid in course_ids}
        all_module_ids = []

        # 4. Traer cursos con sus habilidades y módulos en bloque (máx 2 viajes)
        if course_ids:
            courses_resp = (
                admin.table("courses")
                .select("id, title, url, platform, duration_hours, level, is_free, course_skills(skills(slug))")
                .in_("id", course_ids)
                .execute()
            )
            courses_by_id = {c["id"]: c for c in (courses_resp.data or [])}

            # Vincular cursos con actividad a sus skills correspondientes
            for c in (courses_resp.data or []):
                cid = c["id"]
                for cs in (c.get("course_skills") or []):
                    skill_obj = cs.get("skills")
                    if skill_obj and skill_obj.get("slug"):
                        s_slug = skill_obj["slug"]
                        if cid not in user_courses_by_slug.setdefault(s_slug, []):
                            user_courses_by_slug[s_slug].append(cid)

            modules_resp = (
                admin.table("course_modules")
                .select("id, course_id")
                .in_("course_id", course_ids)
                .execute()
            )
            for m in (modules_resp.data or []):
                modules_by_course.setdefault(m["course_id"], []).append(m["id"])
                all_module_ids.append(m["id"])

        summary = []
        for skill in roadmap_skills:
            slug = skill["skill_slug"]
            cids = user_courses_by_slug.get(slug, [])

            if not cids:
                summary.append({
                    "skill_slug": slug,
                    "course_id": None,
                    "course_title": None,
                    "course_url": None,
                    "progress": None,
                    "assigned_courses": [],
                })
                continue

            assigned_courses = []
            for cid in cids:
                course = courses_by_id.get(cid, {})
                mod_ids = modules_by_course.get(cid, [])
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

                assigned_courses.append({
                    "course_id": cid,
                    "course_title": course.get("title") or f"Curso #{cid}",
                    "course_url": course.get("url"),
                    "platform": course.get("platform") or "Online",
                    "duration_hours": course.get("duration_hours"),
                    "level": course.get("level"),
                    "is_free": course.get("is_free", True),
                    "completed_modules": completed,
                    "total_modules": total,
                    "percentage": percentage,
                    "skill_percentage": skill_percentage,
                    "is_completed": total > 0 and completed >= total,
                })

            # Seleccionar curso principal para retrocompatibilidad
            main_course = next((c for c in assigned_courses if 0 < c["percentage"] < 100), None)
            if not main_course:
                main_course = next((c for c in assigned_courses if c["is_completed"]), assigned_courses[0])

            summary.append({
                "skill_slug": slug,
                "course_id": main_course["course_id"],
                "course_title": main_course["course_title"],
                "course_url": main_course["course_url"],
                "completed_modules": main_course["completed_modules"],
                "total_modules": main_course["total_modules"],
                "course_percentage": main_course["percentage"],
                "skill_percentage": main_course["skill_percentage"],
                "progress": {
                    "completed": main_course["completed_modules"],
                    "total": main_course["total_modules"],
                    "percentage": main_course["percentage"],
                    "skill_percentage": main_course["skill_percentage"],
                },
                "assigned_courses": assigned_courses,
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
        admin = get_admin_client()

        user_skill_result = (
            admin.table("user_skills")
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
            admin.table("user_skill_courses")
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