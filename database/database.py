from supabase import create_client, Client

from core.config import settings


if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
    raise ValueError(
        "Faltan SUPABASE_URL o SUPABASE_ANON_KEY en el archivo .env"
    )

if not settings.SUPABASE_SECRET_KEY:
    raise ValueError(
        "Falta SUPABASE_SECRET_KEY en el archivo .env"
    )


# Cliente normal: respeta las políticas RLS.
supabase_client: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_ANON_KEY,
)

# Cliente administrativo: usado solo dentro del backend.
supabase_admin_client: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_SECRET_KEY,
)