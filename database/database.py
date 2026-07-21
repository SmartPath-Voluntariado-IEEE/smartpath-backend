from supabase import create_client, Client
from core.config import settings

from typing import Optional

if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
    raise ValueError("Faltan credenciales de Supabase en el archivo .env.local")

supabase_client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)

def get_db_client(token: Optional[str] = None) -> Client:
    """
    Retorna un cliente de Supabase optimizado para operaciones de base de datos.
    Si se configuró SUPABASE_SERVICE_ROLE_KEY, la utiliza para realizar bypass de RLS en el backend.
    Si se proporciona token JWT del usuario, inyecta el token en la cabecera de PostgREST para cumplir RLS.
    De lo contrario, retorna el cliente anon base.
    """
    if settings.SUPABASE_SERVICE_ROLE_KEY:
        return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    
    if token:
        client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
        client.postgrest.auth(token)
        return client
        
    return supabase_client