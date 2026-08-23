from database.database import get_admin_client
from services.course_pricing import is_free_course


class CatalogService:
    @staticmethod
    def get_all_skills():
        client = get_admin_client()

        response = (
            client
            .table("skills")
            .select("*")
            .execute()
        )

        return response.data if response.data else []

    @staticmethod
    def _extract_skills_from_text(text: str, all_skills: list[dict]) -> list[str]:
        import re
        lower = " " + (text or "").lower() + " "
        found = set()
        for s in all_skills:
            names = [s.get("name", ""), *(s.get("aliases") or [])]
            for n in names:
                if not n:
                    continue
                needle = n.lower()
                pattern = rf"(^|[^a-z0-9\+#\.]){re.escape(needle)}([^a-z0-9\+#]|$)"
                if re.search(pattern, lower, re.IGNORECASE):
                    found.add(s["slug"])
                    break
        return list(found)

    @staticmethod
    def get_all_jobs():
        client = get_admin_client()

        # Fetch jobs with their associated skills via job_skills join
        response = (
            client
            .table("jobs")
            .select("*, job_skills(skills(slug))")
            .order("posted_at", desc=True)
            .execute()
        )

        all_skills = None
        jobs = []
        if response.data:
            for item in response.data:
                slugs = []
                for js in item.get("job_skills", []):
                    skill_info = js.get("skills")
                    if skill_info and skill_info.get("slug"):
                        slugs.append(skill_info.get("slug"))

                # Fallback: si no hay job_skills en BD, extraer del título y descripción
                if not slugs:
                    if all_skills is None:
                        all_skills = CatalogService.get_all_skills()
                    text = f"{item.get('position', '')} {item.get('description', '')}"
                    slugs = CatalogService._extract_skills_from_text(text, all_skills)

                jobs.append({
                    "id": item["id"],
                    "company": item.get("company"),
                    "position": item.get("position"),
                    "salary": item.get("salary"),
                    "seniority": item.get("seniority"),
                    "description": item.get("description"),
                    "location": item.get("location"),
                    "posted_at": item.get("posted_at"),
                    "skill_slugs": slugs,
                })

        return jobs

    @staticmethod
    def get_market_overview():
        """Aggregate market data: skill demand, salary ranges, top companies."""

        # 1. Get all jobs (with skill_slugs computed)
        jobs = CatalogService.get_all_jobs()
        total_jobs = len(jobs)

        # 2. Skill demand: count how many jobs require each skill
        all_skills = CatalogService.get_all_skills()
        skills_map = {s["slug"]: s for s in all_skills}

        skill_counts: dict[str, dict] = {}
        for job in jobs:
            for slug in job.get("skill_slugs", []):
                if slug not in skill_counts:
                    s_info = skills_map.get(slug, {"name": slug.title(), "category": "other"})
                    skill_counts[slug] = {
                        "slug": slug,
                        "name": s_info.get("name", slug.title()),
                        "category": s_info.get("category", "other"),
                        "count": 0,
                    }
                skill_counts[slug]["count"] += 1

        skill_demand = []
        for item in sorted(skill_counts.values(), key=lambda x: -x["count"]):
            item["frequency"] = round(item["count"] / total_jobs, 2) if total_jobs else 0
            skill_demand.append(item)

        # 3. Salary ranges by seniority
        salary_data: dict[str, list[int]] = {}
        for job in jobs:
            seniority = job.get("seniority") or "Sin especificar"
            salary = job.get("salary")
            if salary is not None:
                salary_data.setdefault(seniority, []).append(salary)

        salary_ranges = {}
        for seniority, salaries in salary_data.items():
            salary_ranges[seniority] = {
                "min": min(salaries),
                "max": max(salaries),
                "avg": round(sum(salaries) / len(salaries)),
                "count": len(salaries),
            }

        # 4. Top companies (by number of open positions)
        company_counts: dict[str, int] = {}
        for job in jobs:
            comp = job.get("company") or "Sin especificar"
            company_counts[comp] = company_counts.get(comp, 0) + 1
        top_companies = [
            c for c, _ in sorted(company_counts.items(), key=lambda x: -x[1])[:10]
        ]

        return {
            "total_jobs": total_jobs,
            "skill_demand": skill_demand,
            "salary_ranges": salary_ranges,
            "top_companies": top_companies,
        }

    @staticmethod
    def get_user_job_matches(user_id: str):
        """Calculate compatibility % between user skills and each job."""
        client = get_admin_client()

        # 1. Get user's skills using proper foreign key relation
        user_skills_resp = (
            client
            .table("user_skills")
            .select("level, skills(slug)")
            .eq("user_id", user_id)
            .execute()
        )
        user_slugs = set()
        if user_skills_resp.data:
            for us in user_skills_resp.data:
                s_info = us.get("skills")
                if s_info and s_info.get("slug"):
                    user_slugs.add(s_info["slug"])

        # 2. Get all jobs with their skill_slugs
        jobs = CatalogService.get_all_jobs()

        # 3. Calculate match for each job
        matches = []
        for job in jobs:
            required = job.get("skill_slugs", [])
            matched = [s for s in required if s in user_slugs]
            missing = [s for s in required if s not in user_slugs]
            pct = round((len(matched) / len(required)) * 100) if required else 0

            matches.append({
                "job": job,
                "match_percentage": pct,
                "matched_skills": matched,
                "missing_skills": missing,
            })

        # Sort by highest match first
        matches.sort(key=lambda m: -m["match_percentage"])
        return matches

    @staticmethod
    def get_all_courses(
        skill_slug: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ):
        client = get_admin_client()
        if skill_slug:
            skill_resp = (
                client
                .table("skills")
                .select("id")
                .eq("slug", skill_slug)
                .execute()
            )

            if not skill_resp.data:
                return []

            skill_id = skill_resp.data[0]["id"]

            course_skill_response = (
                client
                .table("course_skills")
                .select("course_id")
                .eq("skill_id", skill_id)
                .execute()
            )

            if not course_skill_response.data:
                return []

            course_ids = [
                item["course_id"]
                for item in course_skill_response.data
            ]

            query = (
                client
                .table("courses")
                .select("*, course_skills(skills(slug))")
                .in_("id", course_ids)
            )

        else:
            query = (
                client
                .table("courses")
                .select("*, course_skills(skills(slug))")
            )

        if limit is not None:
            query = query.range(offset, offset + limit - 1)

        response = query.execute()

        courses = []

        if response.data:
            for item in response.data:
                slugs = []

                for course_skill in item.get("course_skills", []):
                    skill_info = course_skill.get("skills")

                    if skill_info:
                        slugs.append(skill_info.get("slug"))

                courses.append({
                    "id": item["id"],
                    "platform": item["platform"],
                    "institution": item.get("institution"),
                    "title": item["title"],
                    "instructor": item.get("instructor"),
                    "duration_hours": item["duration_hours"],
                    "language": item.get("language"),
                    "price": item["price"],
                    "is_free": is_free_course(item),
                    "rating": item["rating"],
                    "level": item["level"],
                    "certificate": item.get("certificate", False),
                    "url": item["url"],
                    "skill_slugs": slugs,
                })

        # Los cursos gratuitos encabezan el catálogo; dentro de cada grupo
        # manda el rating (los cursos sin rating quedan al final).
        courses.sort(
            key=lambda c: (
                not c["is_free"],
                -(c["rating"] or 0),
            )
        )

        return courses

    @staticmethod
    def get_role_skills(role_id: str):
        client = get_admin_client()

        role_response = (
            client
            .table("role_targets")
            .select("id")
            .eq("id", role_id)
            .execute()
        )

        if not role_response.data:
            return None

        response = (
            client
            .table("role_target_skills")
            .select("skills(*)")
            .eq("role_id", role_id)
            .order("skill_slug")
            .execute()
        )

        role_skills = []

        if response.data:
            for relationship in response.data:
                skill = relationship.get("skills")

                if skill:
                    role_skills.append(skill)

        return role_skills

    @staticmethod
    def get_all_role_targets():
        client = get_admin_client()

        response = (
            client
            .table("role_targets")
            .select("*, role_target_skills(skill_slug)")
            .execute()
        )

        roles = []

        if response.data:
            for item in response.data:
                slugs = [
                    relationship.get("skill_slug")
                    for relationship
                    in item.get("role_target_skills", [])
                    if relationship.get("skill_slug")
                ]

                roles.append({
                    "id": item["id"],
                    "label": item["label"],
                    "core_skill_slugs": slugs,
                })

        return roles
