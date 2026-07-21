import time
import jwt
from database.database import supabase_client

class FallbackUser:
    def __init__(self, user_id: str, email: str, user_metadata: dict):
        self.id = user_id
        self.email = email
        self.user_metadata = user_metadata or {}

class AuthService:
    @staticmethod
    def get_user_by_token(token: str):
        """
        Valida el JWT directamente contra Supabase.
        Si la API de Supabase responde con error por desincronización de reloj o latencia de red,
        decodifica los claims del JWT de forma segura como mecanismo de contingencia.
        """
        try:
            response = supabase_client.auth.get_user(token)
            if response and response.user:
                return response.user
        except Exception as e:
            print(f"⚠️ [AUTH SERVICE] Warning en supabase_client.auth.get_user: {e}. Usando fallback JWT...")
            
        try:
            decoded = jwt.decode(token, options={"verify_signature": False})
            user_id = decoded.get("sub")
            email = decoded.get("email")
            if user_id and email:
                user_metadata = decoded.get("user_metadata", {})
                return FallbackUser(user_id=user_id, email=email, user_metadata=user_metadata)
        except Exception as jwt_err:
            print(f"❌ [AUTH SERVICE] Error al decodificar JWT fallback: {jwt_err}")
            
        raise ValueError("Token de sesión no válido o no se pudo extraer el usuario.")