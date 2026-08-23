import os
from typing import ClassVar

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

    APIFY_API_TOKEN: str = os.getenv(
        "APIFY_API_TOKEN",
        "",
    )

    APIFY_ACTOR_ID: str = os.getenv(
        "APIFY_ACTOR_ID",
        "crawlerbros~class-central-scraper",
    )
    GEMINI_API_KEY: str = os.getenv(
        "GEMINI_API_KEY",
        "",
    )

    # ------------------------------------------------
    # HU-57: recolección de ofertas laborales (JobSpy)
    # ------------------------------------------------

    # Portales a consultar. Indeed es el que mejor cobertura tiene en Perú;
    # LinkedIn se deja fuera por defecto porque limita por IP muy rápido y
    # una corrida bloqueada deja el lote entero vacío.
    JOBSPY_SITES: ClassVar[list[str]] = [
        site.strip()
        for site in os.getenv("JOBSPY_SITES", "indeed").split(",")
        if site.strip()
    ]

    JOBSPY_COUNTRY: str = os.getenv("JOBSPY_COUNTRY", "peru")

    JOBSPY_LOCATION: str = os.getenv("JOBSPY_LOCATION", "Peru")

    # Resultados por término de búsqueda y por portal.
    JOBSPY_RESULTS_PER_TERM: int = int(
        os.getenv("JOBSPY_RESULTS_PER_TERM", "25")
    )

    # Antigüedad máxima de una oferta, en horas (720 = 30 días).
    JOBSPY_HOURS_OLD: int = int(os.getenv("JOBSPY_HOURS_OLD", "720"))

    # Pausa entre búsquedas para no gatillar el rate limit del portal.
    JOBSPY_DELAY_SECONDS: float = float(
        os.getenv("JOBSPY_DELAY_SECONDS", "3")
    )

    JOBSPY_PROXIES: ClassVar[list[str]] = [
        proxy.strip()
        for proxy in os.getenv("JOBSPY_PROXIES", "").split(",")
        if proxy.strip()
    ]


settings = Settings()
