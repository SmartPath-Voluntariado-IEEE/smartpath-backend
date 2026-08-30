import time

import pytest

from core import cache
from database.database import clear_token_clients, get_db_client


@pytest.fixture(autouse=True)
def _clean():
    cache.invalidate()
    yield
    cache.invalidate()


def test_ttl_cache_avoids_recomputing_within_ttl():
    calls = []

    @cache.ttl_cache("test:demo", ttl_seconds=60)
    def expensive():
        calls.append(1)
        return "valor"

    assert expensive() == "valor"
    assert expensive() == "valor"
    assert len(calls) == 1


def test_ttl_cache_separates_by_arguments():
    calls = []

    @cache.ttl_cache("test:args", ttl_seconds=60)
    def fetch(skill=None, limit=None):
        calls.append((skill, limit))
        return skill

    fetch(skill="python", limit=12)
    fetch(skill="python", limit=12)
    fetch(skill="react", limit=12)

    assert calls == [("python", 12), ("react", 12)]


def test_ttl_cache_expires():
    calls = []

    @cache.ttl_cache("test:expira", ttl_seconds=0)
    def fetch():
        calls.append(1)
        return 1

    fetch()
    time.sleep(0.01)
    fetch()

    assert len(calls) == 2


def test_invalidate_clears_only_the_given_namespace():
    @cache.ttl_cache("test:a", ttl_seconds=60)
    def a():
        return 1

    @cache.ttl_cache("test:b", ttl_seconds=60)
    def b():
        return 2

    a()
    b()
    cache.invalidate("test:a")

    stats = cache.stats()
    assert "test:a" not in stats
    assert stats["test:b"] == 1


def test_catalog_invalidate_cache_empties_catalog_namespaces():
    from services.catalog_service import CatalogService

    @cache.ttl_cache("catalog:skills", ttl_seconds=60)
    def skills():
        return []

    skills()
    assert cache.stats().get("catalog:skills") == 1

    CatalogService.invalidate_cache()
    assert "catalog:skills" not in cache.stats()


def test_get_db_client_reuses_the_client_for_the_same_token():
    clear_token_clients()

    first = get_db_client("token-de-prueba")
    second = get_db_client("token-de-prueba")
    other = get_db_client("otro-token")

    assert first is second
    assert first is not other

    clear_token_clients()


def test_get_db_client_without_token_returns_the_shared_client():
    from database.database import supabase_client

    assert get_db_client() is supabase_client
