from database.database import supabase_client

class CatalogService:
    @staticmethod
    def get_all_skills():
        response = supabase_client.table("skills").select("*").execute()
        return response.data if response.data else []

    @staticmethod
    def get_all_jobs():
        response = supabase_client.table("jobs").select("*").execute()
        return response.data if response.data else []

    @staticmethod
    def get_all_courses(skill_slug: str = None):
        if skill_slug:
            # Filtrar cursos por skill slug
            # Primero buscamos el skill_id de ese slug
            skill_resp = supabase_client.table("skills").select("id").eq("slug", skill_slug).execute()
            if not skill_resp.data:
                return []
            skill_id = skill_resp.data[0]["id"]
            
            # Buscamos los course_id en course_skills
            cs_resp = supabase_client.table("course_skills").select("course_id").eq("skill_id", skill_id).execute()
            if not cs_resp.data:
                return []
            course_ids = [item["course_id"] for item in cs_resp.data]
            
            # Obtenemos los cursos con sus correspondientes slugs de skills
            response = supabase_client.table("courses").select("*, course_skills(skills(slug))").in_("id", course_ids).execute()
        else:
            response = supabase_client.table("courses").select("*, course_skills(skills(slug))").execute()
            
        courses = []
        if response.data:
            for item in response.data:
                # Mapear la relación anidada a un array plano de skill_slugs
                slugs = []
                for cs in item.get("course_skills", []):
                    skill_info = cs.get("skills")
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
                    "skill_slugs": slugs
                })
        return courses

    @staticmethod
    def get_all_role_targets():
        response = supabase_client.table("role_targets").select("*, role_target_skills(skill_slug)").execute()
        roles = []
        if response.data:
            for item in response.data:
                slugs = [rts.get("skill_slug") for rts in item.get("role_target_skills", []) if rts.get("skill_slug")]
                roles.append({
                    "id": item["id"],
                    "label": item["label"],
                    "core_skill_slugs": slugs
                })
        return roles
