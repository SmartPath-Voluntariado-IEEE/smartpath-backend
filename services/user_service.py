from typing import Optional
from database.database import get_db_client
from schemas.user import UserProfileUpdate

class UserService:
    @staticmethod
    def get_user_skills(user_id: str, token: Optional[str] = None):
        client = get_db_client(token)
        response = client.table("user_skills").select("level, skills(slug)").eq("user_id", user_id).execute()
        skills = []
        if response.data:
            for item in response.data:
                skill_info = item.get("skills")
                if skill_info:
                    skills.append({
                        "skill_slug": skill_info.get("slug"),
                        "level": item.get("level")
                    })
        return skills

    @staticmethod
    def save_user_skills(user_id: str, skills_list, token: Optional[str] = None):
        if skills_list is None:
            return
            
        client = get_db_client(token)
        client.table("user_skills").delete().eq("user_id", user_id).execute()
        
        if not skills_list:
            return
            
        skills_resp = client.table("skills").select("id, slug").execute()
        slug_to_id = {}
        if skills_resp.data:
            slug_to_id = {item["slug"]: item["id"] for item in skills_resp.data}
            
        insert_data = []
        for sk in skills_list:
            slug = sk.skill_slug if hasattr(sk, "skill_slug") else sk.get("skill_slug")
            level = sk.level if hasattr(sk, "level") else sk.get("level", 1)
            
            skill_id = slug_to_id.get(slug)
            if skill_id:
                insert_data.append({
                    "user_id": user_id,
                    "skill_id": skill_id,
                    "level": level
                })
        
        if insert_data:
            client.table("user_skills").insert(insert_data).execute()

    @staticmethod
    def get_profile(user_id: str, token: Optional[str] = None):
        client = get_db_client(token)
        response = client.table("users").select("*").eq("id", user_id).execute()
        if response.data:
            profile = response.data[0]
            if profile.get("target_months") is None:
                profile["target_months"] = 6
            profile["skills"] = UserService.get_user_skills(user_id, token=token)
            return profile
        return None

    @staticmethod
    def upsert_profile(user_id: str, email: str, default_name: str, profile_data: UserProfileUpdate, token: Optional[str] = None):
        try:
            client = get_db_client(token)
            data = {
                "id": user_id,
                "email": email
            }
            
            update_dict = profile_data.model_dump(exclude_none=True)
            skills_list = update_dict.pop("skills", None)
            data.update(update_dict)
            
            if data.get("target_months") is None:
                data["target_months"] = 6
            
            if not data.get("full_name"):
                data["full_name"] = default_name or (email.split("@")[0] if email else "Usuario de SmartPath")
            
            if data.get("professional_goal"):
                data["professional_goal"] = str(data["professional_goal"])[:100]
            if data.get("full_name"):
                data["full_name"] = str(data["full_name"])[:150]
            if data.get("career"):
                data["career"] = str(data["career"])[:120]
            if data.get("university"):
                data["university"] = str(data["university"])[:150]
            if data.get("experience_level"):
                data["experience_level"] = str(data["experience_level"])[:50]
            if data.get("english_level"):
                data["english_level"] = str(data["english_level"])[:30]

            target_months_val = data.get("target_months", 6)
            try:
                response = client.table("users").upsert(data).execute()
            except Exception as upsert_err:
                print(f"⚠️ Aviso al hacer upsert con target_months: {upsert_err}. Reintentando compatibilidad...")
                if "target_months" in data:
                    data.pop("target_months", None)
                    response = client.table("users").upsert(data).execute()
                else:
                    raise upsert_err

            if response.data:
                if skills_list is not None:
                    UserService.save_user_skills(user_id, skills_list, token=token)
                    
                profile = response.data[0]
                if profile.get("target_months") is None:
                    profile["target_months"] = target_months_val
                profile["skills"] = UserService.get_user_skills(user_id, token=token)
                return profile
            return None
        except Exception as e:
            print(f"Error crítico en UserService.upsert_profile: {e}")
            raise e
