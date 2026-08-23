"""
Tests de la verificación local del token de sesión.

Antes, cada petición autenticada pagaba un viaje de red completo a Supabase
Auth. Ahora se verifica localmente contra la clave pública (JWKS) del
proyecto. Lo que importa comprobar es que la verificación local extrae los
mismos datos que antes exponía Supabase (`id`, `email`, `user_metadata`) y
que un token que no puede verificarse localmente sigue rechazándose, no cae
silenciosamente a aceptar cualquier cosa.

Se mockea `jwt.decode` y `PyJWKClient` en vez de usar tokens reales: un
token real requeriría red incluso en tests, y el objetivo de esta HU era
justamente sacar la red del camino.
"""

from unittest.mock import MagicMock, patch

import jwt as pyjwt
import pytest

from services.auth_service import AuthService


def test_verificacion_local_expone_id_email_y_metadata():
    payload = {
        "sub": "11111111-1111-1111-1111-111111111111",
        "email": "user@example.com",
        "user_metadata": {"full_name": "Ana Torres"},
    }

    with patch("services.auth_service._jwks_client") as jwks_client, patch(
        "jwt.decode", return_value=payload
    ):
        jwks_client.get_signing_key_from_jwt.return_value = MagicMock(key="fake-key")

        user = AuthService._verify_locally("cualquier.token.valido")

    assert user.id == payload["sub"]
    assert user.email == payload["email"]
    assert user.user_metadata == {"full_name": "Ana Torres"}


def test_verificacion_local_sin_metadata_devuelve_dict_vacio():
    # user_metadata es opcional en el payload; el resto del backend hace
    # `current_user.user_metadata.get(...)` y necesita que nunca sea None.
    payload = {"sub": "abc", "email": "sin-metadata@example.com"}

    with patch("services.auth_service._jwks_client") as jwks_client, patch(
        "jwt.decode", return_value=payload
    ):
        jwks_client.get_signing_key_from_jwt.return_value = MagicMock(key="fake-key")

        user = AuthService._verify_locally("token")

    assert user.user_metadata == {}


def test_token_invalido_se_rechaza_sin_caer_al_camino_remoto():
    # Un token mal formado falla al analizarse (DecodeError, subclase de
    # InvalidTokenError) antes de llegar a pedir la clave: no debe
    # reintentarse contra Supabase, solo rechazarse.
    with patch(
        "services.auth_service._jwks_client"
    ) as jwks_client, patch.object(
        AuthService, "_verify_remotely"
    ) as verify_remotely:
        jwks_client.get_signing_key_from_jwt.side_effect = pyjwt.DecodeError(
            "token mal formado"
        )

        with pytest.raises(ValueError):
            AuthService.get_user_by_token("no-es-un-jwt")

        verify_remotely.assert_not_called()


def test_falla_de_infraestructura_local_cae_al_camino_remoto():
    # Si el JWKS no se puede resolver (red caída, DNS, lo que sea), no debe
    # dejar a todos los usuarios sin poder autenticarse: se reintenta contra
    # Supabase directamente, como se hacía antes de esta HU.
    with patch("services.auth_service._jwks_client") as jwks_client, patch.object(
        AuthService, "_verify_remotely", return_value="usuario-remoto"
    ) as verify_remotely:
        jwks_client.get_signing_key_from_jwt.side_effect = RuntimeError(
            "JWKS inalcanzable"
        )

        user = AuthService.get_user_by_token("token.estructuralmente.valido")

    assert user == "usuario-remoto"
    verify_remotely.assert_called_once()
