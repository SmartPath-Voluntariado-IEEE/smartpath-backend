from database.database import get_admin_client


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
    def get_all_jobs():
        client = get_admin_client()

        response = (
            client
            .table("jobs")
            .select("*")
            .execute()
        )

        return response.data if response.data else []

    @staticmethod
    def get_all_courses(skill_slug: str = None):
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

            response = (
                client
                .table("courses")
                .select("*, course_skills(skills(slug))")
                .in_("id", course_ids)
                .execute()
            )

        else:
            response = (
                client
                .table("courses")
                .select("*, course_skills(skills(slug))")
                .execute()
            )

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
                    "title": item["title"],
                    "duration_hours": item["duration_hours"],
                    "price": item["price"],
                    "rating": item["rating"],
                    "level": item["level"],
                    "url": item["url"],
                    "skill_slugs": slugs,
                })

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
