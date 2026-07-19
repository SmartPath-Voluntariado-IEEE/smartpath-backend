from database.database import supabase_client
from schemas.user import UserProfileUpdate

class UserService:
    @staticmethod
    def get_user_skills(user_id: str):
        # Consulta para traer el nivel y el slug de la skill asociada
        response = supabase_client.table("user_skills").select("level, skills(slug)").eq("user_id", user_id).execute()
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
    def save_user_skills(user_id: str, skills_list):
        if skills_list is None:
            return
            
        # 1. Borrar todas las skills existentes del usuario para evitar duplicados
        supabase_client.table("user_skills").delete().eq("user_id", user_id).execute()
        
        if not skills_list:
            return
            
        # 2. Obtener un mapeo de skill_slug -> skill_id
        skills_resp = supabase_client.table("skills").select("id, slug").execute()
        slug_to_id = {}
        if skills_resp.data:
            slug_to_id = {item["slug"]: item["id"] for item in skills_resp.data}
            
        # 3. Preparar e insertar las nuevas relaciones
        insert_data = []
        for sk in skills_list:
            # En caso de que venga como diccionario u objeto Pydantic
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
            supabase_client.table("user_skills").insert(insert_data).execute()

    @staticmethod
    def get_profile(user_id: str):
        response = supabase_client.table("users").select("*").eq("id", user_id).execute()
        if response.data:
            profile = response.data[0]
            profile["skills"] = UserService.get_user_skills(user_id)
            return profile
        return None

    @staticmethod
    def upsert_profile(user_id: str, email: str, default_name: str, profile_data: UserProfileUpdate):
        # Preparar los datos básicos
        data = {
            "id": user_id,
            "email": email
        }
        
        # Filtrar campos no nulos del perfil
        update_dict = profile_data.model_dump(exclude_none=True)
        
        # Quitar la lista de skills ya que pertenece a otra tabla
        skills_list = update_dict.pop("skills", None)
        
        data.update(update_dict)
        
        # Si 'full_name' no está presente y el usuario no existe en la BD, asignamos el nombre por defecto
        if "full_name" not in data or not data["full_name"]:
            existing = UserService.get_profile(user_id)
            if not existing:
                data["full_name"] = default_name or "Usuario de SmartPath"
        
        # Upsert en la tabla 'users'
        response = supabase_client.table("users").upsert(data).execute()
        if response.data:
            # Si se proporcionó la lista de skills, guardarla
            if skills_list is not None:
                UserService.save_user_skills(user_id, skills_list)
                
            profile = response.data[0]
            profile["skills"] = UserService.get_user_skills(user_id)
            return profile
        return None
