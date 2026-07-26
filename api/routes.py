from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services.auth_service import AuthService
from services.user_service import UserService
from schemas.auth import UserMeResponse
from schemas.user import UserProfileUpdate, UserProfileResponse
from services.vacancy_service import VacancyService

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

@router.get("/users/profile", response_model=UserProfileResponse, summary="Obtener el perfil del usuario")
def get_user_profile(current_user=Depends(get_current_user)):
    """
    Retorna el perfil del usuario en la base de datos relacional de Supabase.
    """
    profile = UserService.get_profile(current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil de usuario no encontrado en la base de datos."
        )
    return profile

@router.post("/users/profile", response_model=UserProfileResponse, summary="Crear o actualizar el perfil del usuario")
def upsert_user_profile(profile_data: UserProfileUpdate, current_user=Depends(get_current_user)):
    """
    Crea o actualiza los datos del perfil del usuario (onboarding y configuraciones del perfil).
    """
    default_name = current_user.user_metadata.get("full_name") if current_user.user_metadata else None
    profile = UserService.upsert_profile(
        user_id=current_user.id,
        email=current_user.email,
        default_name=default_name,
        profile_data=profile_data
    )
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo crear o actualizar el perfil del usuario."
        )
    return profile

@router.get("/jobs/search", summary="Buscar ofertas de empleo")
async def search_jobs():
    return await VacancyService.search_jobs()

@router.post(
    "/jobs/collect",
    summary="Recolectar y guardar ofertas de empleo",
)
async def collect_jobs():
    return await VacancyService.collect_and_save_jobs()

@router.post(
    "/jobs/extract-skills",
    summary="Extraer habilidades técnicas de las ofertas",
)
async def extract_job_skills():
    return await VacancyService.extract_and_save_job_skills()