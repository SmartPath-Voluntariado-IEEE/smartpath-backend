import os

# Set default test environment variables before importing app modules
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "dummy_anon_key_for_testing_purposes_only")
os.environ.setdefault("REDIRECT_URI", "http://localhost:3000")

import pytest


@pytest.fixture(autouse=True)
def _clear_runtime_caches():
    """
    La caché de catálogo y el pool de clientes viven en el proceso, así que
    se limpian entre pruebas para que una no vea los datos de otra.
    """

    from core.cache import invalidate
    from database.database import clear_token_clients

    invalidate()
    clear_token_clients()
    yield
    invalidate()
    clear_token_clients()
