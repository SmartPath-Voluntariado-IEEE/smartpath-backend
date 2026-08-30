
import threading
from collections import OrderedDict

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
supabase_admin_client: Client | None = (
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


# Cada create_client() abre un pool HTTP nuevo, así que la primera consulta
# paga handshake TLS. Antes se creaba un cliente por llamada a get_db_client(),
# es decir varias veces por petición. Aquí se reutiliza el cliente por token,
# conservando el aislamiento de RLS (cada token mantiene el suyo).
_TOKEN_CLIENT_LIMIT = 128

_token_clients: "OrderedDict[str, Client]" = OrderedDict()
_token_clients_lock = threading.Lock()


def _build_token_client(token: str) -> Client:
    client = create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_ANON_KEY,
    )
    client.postgrest.auth(token)
    return client


def get_db_client(token: str | None = None) -> Client:
    """
    Retorna un cliente que respeta la sesión y las políticas RLS.

    El cliente administrativo debe solicitarse explícitamente mediante
    get_admin_client() únicamente para procesos internos del backend.
    """

    if not token:
        return supabase_client

    with _token_clients_lock:
        client = _token_clients.get(token)

        if client is not None:
            # Marca el token como usado recientemente (política LRU).
            _token_clients.move_to_end(token)
            return client

    client = _build_token_client(token)

    with _token_clients_lock:
        existing = _token_clients.get(token)

        if existing is not None:
            _token_clients.move_to_end(token)
            return existing

        _token_clients[token] = client

        while len(_token_clients) > _TOKEN_CLIENT_LIMIT:
            _token_clients.popitem(last=False)

    return client


def clear_token_clients() -> None:
    """Descarta los clientes autenticados cacheados (usado en pruebas)."""

    with _token_clients_lock:
        _token_clients.clear()
