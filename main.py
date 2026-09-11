import logging
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from api.routes import router as api_router
from core.config import settings

logger = logging.getLogger(__name__)

app = FastAPI(
    title="FastAPI Backend con Supabase para Smartpath",
    description="Estructura modular para verificar autenticación de usuarios desde un frontend independiente",
    version="1.0.0"
)

# El catálogo de cursos y ofertas viaja como JSON de cientos de KB; comprimirlo
# recorta la transferencia sin tocar los endpoints.
app.add_middleware(GZipMiddleware, minimum_size=1024)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error("Excepción no controlada en %s %s: %s", request.method, request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor", "error": str(exc)},
    )


# Registrar rutas
app.include_router(api_router)

@app.get("/")
def root():
    return {"message": "El backend está en línea. Listo para procesar tokens del frontend."}
