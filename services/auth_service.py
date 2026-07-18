from database.database import supabase_client

class AuthService:
    @staticmethod
    def get_user_by_token(token: str):
        """
        Valida el JWT directamente contra Supabase.
        Si el token es inválido o expiró, levantará una excepción.
        """
        response = supabase_client.auth.get_user(token)
        return response.user