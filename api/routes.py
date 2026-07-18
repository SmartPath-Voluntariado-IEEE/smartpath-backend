from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services.auth_service import AuthService
from schemas.auth import UserMeResponse

router = APIRouter()
security = HTTPBearer()

# Dependencia para proteger rutas del backend
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        # Validamos el token obtenido del frontend con Supabase
        user = AuthService.get_user_by_token(token)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Sesión inválida o expirada en el backend: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.get("/users/me", response_model=UserMeResponse, summary="Obtener usuario autenticado")
def get_dashboard_info(current_user=Depends(get_current_user)):
    """
    Ruta protegida para usuarios logueados. El frontend envía el token de Google/Supabase
    en las cabeceras HTTP de la petición, permitiendo verificar que el usuario está dentro del sistema.
    """
    return UserMeResponse(
        status="authorized",
        message="Estás autenticado correctamente dentro del sistema.",
        user_details={
            "id": current_user.id,
            "email": current_user.email,
            "name": current_user.user_metadata.get("full_name") if current_user.user_metadata else None,
            "avatar": current_user.user_metadata.get("avatar_url") if current_user.user_metadata else None,
        }
    )