"""
Validación de la sesión del usuario.

Antes, cada petición autenticada llamaba a
`supabase_client.auth.get_user(token)`, que hace un viaje de red completo a
los servidores de Supabase Auth para validar el token. Con decenas de
peticiones autenticadas por página (roadmap, cursos, bolsa laboral...), ese
costo se pagaba una vez por cada una — es la causa principal de que todas
las pestañas se sintieran lentas.

Este proyecto firma sus tokens con ES256 (clave asimétrica) y publica la
clave pública en `/auth/v1/.well-known/jwks.json`. Eso permite verificar la
firma **localmente**: no hace falta ningún secreto nuevo ni confiar menos en
el token — es la misma firma, verificada con la misma clave pública que usa
Supabase, solo que sin el viaje de red. `PyJWKClient` cachea la clave en
memoria (`lifespan=3600`, se refresca cada hora), así que a partir de la
primera verificación todo el trabajo es local.
"""

from types import SimpleNamespace

import jwt
from jwt import PyJWKClient

from core.config import settings
from database.database import supabase_client


_JWKS_URL = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"

# Un solo cliente para todo el proceso: es el que mantiene la clave pública
# en caché entre peticiones.
_jwks_client = PyJWKClient(_JWKS_URL, cache_keys=True, lifespan=3600)


class AuthService:
    @staticmethod
    def get_user_by_token(token: str):
        """
        Valida el access token y devuelve el usuario.

        Se intenta primero la verificación local (rápida); si falla por
        cualquier motivo que no sea "el token es inválido" —el JWKS
        inalcanzable, una clave nueva que el caché todavía no tiene,
        cualquier cosa que no se haya previsto—, se cae de vuelta a
        preguntarle a Supabase directamente. Así una corrida real de
        producción no se queda sin poder autenticar a nadie por un problema
        del lado de la verificación local.
        """

        try:
            return AuthService._verify_locally(token)
        except jwt.InvalidTokenError as error:
            raise ValueError(
                "Token de sesión inválido, expirado o no verificable."
            ) from error
        except Exception:
            return AuthService._verify_remotely(token)

    @staticmethod
    def _verify_locally(token: str):
        signing_key = _jwks_client.get_signing_key_from_jwt(token)

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256"],
            audience="authenticated",
        )

        return SimpleNamespace(
            id=payload["sub"],
            email=payload.get("email"),
            user_metadata=payload.get("user_metadata") or {},
        )

    @staticmethod
    def _verify_remotely(token: str):
        try:
            response = supabase_client.auth.get_user(token)
        except Exception as error:
            raise ValueError(
                "Token de sesión inválido, expirado o no verificable."
            ) from error

        if not response or not response.user:
            raise ValueError(
                "Supabase no encontró un usuario asociado al token."
            )

        return response.user
