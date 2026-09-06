"""
Caché en memoria con expiración (TTL) para datos de catálogo.

El catálogo (habilidades, roles, cursos, ofertas) cambia solo cuando corre
una ingesta o un scraping, pero se consultaba a Supabase en **cada** petición.
Como cada consulta es una llamada de red, las pantallas que combinan varios
catálogos pagaban cientos de milisegundos por recurso y por usuario.

`ttl_cache` guarda el resultado en el proceso durante `ttl_seconds` y lo
reutiliza. Cada función cacheada queda agrupada en un *namespace* para poder
invalidarla explícitamente cuando el backend escribe en esas tablas.
"""

from __future__ import annotations

import functools
import threading
import time
from collections.abc import Callable
from typing import Any

# namespace -> { clave de argumentos: (expira_en, valor) }
_store: dict[str, dict[Any, tuple[float, Any]]] = {}
_lock = threading.Lock()

DEFAULT_TTL_SECONDS = 300


def _make_key(args: tuple, kwargs: dict) -> tuple:
    return (args, tuple(sorted(kwargs.items())))


def ttl_cache(
    namespace: str,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
) -> Callable:
    """
    Cachea el retorno de la función durante `ttl_seconds`, por combinación
    de argumentos. El valor cacheado se comparte entre peticiones, así que
    la función NO debe depender del usuario autenticado.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = _make_key(args, kwargs)
            now = time.monotonic()

            with _lock:
                entry = _store.get(namespace, {}).get(key)

                if entry and entry[0] > now:
                    return entry[1]

            # La función se ejecuta fuera del lock: una consulta lenta no debe
            # bloquear la lectura de caché de otras peticiones.
            value = func(*args, **kwargs)

            with _lock:
                _store.setdefault(namespace, {})[key] = (
                    now + ttl_seconds,
                    value,
                )

            return value

        wrapper.cache_namespace = namespace
        wrapper.cache_clear = lambda: invalidate(namespace)

        return wrapper

    return decorator


def invalidate(*namespaces: str) -> None:
    """Vacía los namespaces indicados; sin argumentos, vacía toda la caché."""

    with _lock:
        if not namespaces:
            _store.clear()
            return

        for namespace in namespaces:
            _store.pop(namespace, None)


def stats() -> dict[str, int]:
    """Cantidad de entradas vivas por namespace (para diagnóstico)."""

    now = time.monotonic()

    with _lock:
        return {
            namespace: sum(
                1
                for expires_at, _ in entries.values()
                if expires_at > now
            )
            for namespace, entries in _store.items()
        }
