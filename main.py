from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from api.routes import router as api_router

app = FastAPI(
    title="FastAPI Backend con Supabase para Smartpath",
    description="Estructura modular para verificar autenticación de usuarios desde un frontend independiente",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar rutas
app.include_router(api_router)

@app.get("/")
def root():
    return {"message": "El backend está en línea. Listo para procesar tokens del frontend."}