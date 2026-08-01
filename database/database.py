from typing import Optional

from supabase import Client, create_client

from core.config import settings


if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
    raise ValueError(
        "Faltan SUPABASE_URL o SUPABASE_ANON_KEY en el archivo .env"
    )


# Cliente normal: utiliza la clave anon y respeta las políticas RLS.
supabase_client: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_ANON_KEY,
)


# Aceptamos cualquiera de las dos formas de clave administrativa:
# - SUPABASE_SECRET_KEY: clave moderna sb_secret_...
# - SUPABASE_SERVICE_ROLE_KEY: clave legacy service_role
supabase_backend_key = (
    settings.SUPABASE_SECRET_KEY
    or settings.SUPABASE_SERVICE_ROLE_KEY
)


# Se crea solo cuando existe alguna clave administrativa.
supabase_admin_client: Optional[Client] = (
    create_client(
        settings.SUPABASE_URL,
        supabase_backend_key,
    )
    if supabase_backend_key
    else None
)


def get_admin_client() -> Client:
    """
    Retorna el cliente administrativo utilizado por procesos internos
    del backend, como almacenar vacantes y relaciones de habilidades.
    """

    if supabase_admin_client is None:
        raise ValueError(
            "Falta SUPABASE_SECRET_KEY o "
            "SUPABASE_SERVICE_ROLE_KEY en el archivo .env"
        )

    return supabase_admin_client


def get_db_client(token: Optional[str] = None) -> Client:
    """
    Retorna el cliente adecuado según el tipo de operación.

    - Si existe una clave administrativa, puede hacer bypass de RLS.
    - Si se recibe el token de un usuario, trabaja respetando su sesión.
    - Si no, devuelve el cliente anon base.
    """

    if supabase_backend_key:
        return get_admin_client()

    if token:
        client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_ANON_KEY,
        )
        client.postgrest.auth(token)
        return client

    return supabase_client