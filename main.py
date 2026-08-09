from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router as api_router
from core.config import settings

app = FastAPI(
    title="FastAPI Backend con Supabase para Smartpath",
    description="Estructura modular para verificar autenticación de usuarios desde un frontend independiente",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar rutas
app.include_router(api_router)

@app.get("/")
def root():
    return {"message": "El backend está en línea. Listo para procesar tokens del frontend."}
