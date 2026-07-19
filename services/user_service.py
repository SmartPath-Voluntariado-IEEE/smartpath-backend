from database.database import supabase_client
from schemas.user import UserProfileUpdate

class UserService:
    @staticmethod
    def get_profile(user_id: str):
        response = supabase_client.table("users").select("*").eq("id", user_id).execute()
        if response.data:
            return response.data[0]
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
        data.update(update_dict)
        
        # Si 'full_name' no está presente y el usuario no existe en la BD, asignamos el nombre por defecto
        if "full_name" not in data or not data["full_name"]:
            existing = UserService.get_profile(user_id)
            if not existing:
                data["full_name"] = default_name or "Usuario de SmartPath"
        
        response = supabase_client.table("users").upsert(data).execute()
        if response.data:
            return response.data[0]
        return None
