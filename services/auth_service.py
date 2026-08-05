from database.database import supabase_client


class AuthService:
    @staticmethod
    def get_user_by_token(token: str):
        """
        Valida el access token directamente mediante Supabase Auth.
        """

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