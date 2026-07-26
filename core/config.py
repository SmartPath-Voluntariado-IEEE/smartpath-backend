import os
from dotenv import load_dotenv

# Cargar .env.local si existe, de lo contrario .env
env_path = ".env.local" if os.path.exists(".env.local") else ".env"
load_dotenv(dotenv_path=env_path)

class Settings:
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SECRET_KEY: str = os.getenv("SUPABASE_SECRET_KEY", "")
    # La dirección del servidor Frontend
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    THEIRSTACK_API_KEY: str = os.getenv("THEIRSTACK_API_KEY", "")

settings = Settings()