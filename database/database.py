from supabase import create_client, Client
from core.config import settings

if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
    raise ValueError("Faltan credenciales de Supabase en el archivo .env.local")

supabase_client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)