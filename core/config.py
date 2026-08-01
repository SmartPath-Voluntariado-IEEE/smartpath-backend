import os

from dotenv import load_dotenv


# Cargar .env.local si existe; de lo contrario, cargar .env
env_path = ".env.local" if os.path.exists(".env.local") else ".env"
load_dotenv(dotenv_path=env_path)


class Settings:
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")

    # Compatibilidad con claves nuevas y claves legacy de Supabase
    SUPABASE_SECRET_KEY: str = os.getenv("SUPABASE_SECRET_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv(
        "SUPABASE_SERVICE_ROLE_KEY",
        "",
    )

    FRONTEND_URL: str = os.getenv(
        "FRONTEND_URL",
        "http://localhost:3000",
    )

    THEIRSTACK_API_KEY: str = os.getenv(
        "THEIRSTACK_API_KEY",
        "",
    )


settings = Settings()