from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional

from services.auth_service import AuthService
from services.user_service import UserService
from services.catalog_service import CatalogService
from services.analysis_service import AnalysisService

from schemas.auth import UserMeResponse
from schemas.user import UserProfileUpdate, UserProfileResponse
from schemas.catalog import SkillResponse, JobResponse, CourseResponse, RoleTargetResponse
from schemas.analysis import GapAnalysisResponse, RoadmapLevel, CourseRecommendation, MarketSkillStat

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

# ============================================
# RUTAS DE AUTENTICACIÓN Y PERFIL
# ============================================

@router.get("/users/me", response_model=UserMeResponse, summary="Obtener usuario autenticado")
def get_dashboard_info(current_user=Depends(get_current_user)):
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
    profile = UserService.get_profile(current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil de usuario no encontrado en la base de datos."
        )
    return profile

@router.post("/users/profile", response_model=UserProfileResponse, summary="Crear o actualizar el perfil del usuario")
def upsert_user_profile(profile_data: UserProfileUpdate, current_user=Depends(get_current_user)):
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

# ============================================
# RUTAS DE CATÁLOGOS PÚBLICOS
# ============================================

@router.get("/catalog/skills", response_model=List[SkillResponse], summary="Obtener catálogo de habilidades")
def get_catalog_skills():
    return CatalogService.get_all_skills()

@router.get("/catalog/jobs", response_model=List[JobResponse], summary="Obtener catálogo de ofertas laborales")
def get_catalog_jobs():
    return CatalogService.get_all_jobs()

@router.get("/catalog/courses", response_model=List[CourseResponse], summary="Obtener catálogo de cursos")
def get_catalog_courses(skill: Optional[str] = Query(None, description="Slug de la habilidad a filtrar")):
    return CatalogService.get_all_courses(skill_slug=skill)

@router.get("/catalog/roles", response_model=List[RoleTargetResponse], summary="Obtener catálogo de roles objetivos")
def get_catalog_roles():
    return CatalogService.get_all_role_targets()

# ============================================
# RUTAS DE ANÁLISIS Y ROADMAP
# ============================================

@router.get("/users/gap-analysis", response_model=GapAnalysisResponse, summary="Analizar brecha de habilidades del usuario")
def get_user_gap_analysis(current_user=Depends(get_current_user)):
    profile = UserService.get_profile(current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil de usuario no configurado."
        )
        
    target_role_id = profile.get("target_role_id")
    if not target_role_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El perfil del usuario no tiene un rol objetivo (target_role_id) configurado."
        )
        
    roles = CatalogService.get_all_role_targets()
    target_role = next((r for r in roles if r["id"] == target_role_id), None)
    if not target_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol objetivo no encontrado en el catálogo."
        )
        
    jobs = CatalogService.get_all_jobs()
    skills_catalog = CatalogService.get_all_skills()
    
    market = AnalysisService.market_skill_frequency(jobs, skills_catalog)
    user_skills = profile.get("skills", [])
    
    analysis = AnalysisService.analyze_gap(user_skills, target_role, market, skills_catalog)
    return analysis

@router.get("/users/roadmap", response_model=List[RoadmapLevel], summary="Generar roadmap personalizado para el usuario")
def get_user_roadmap(current_user=Depends(get_current_user)):
    # Reutiliza el gap analysis para generar el roadmap
    gap = get_user_gap_analysis(current_user)
    # Convertimos de modelo de respuesta a dict básico si es necesario,
    # pero como es pydantic podemos pasarlo directo o usar dict
    gap_dict = gap if isinstance(gap, dict) else gap.model_dump()
    return AnalysisService.generate_roadmap(gap_dict)

@router.get("/users/course-recommendations", response_model=List[CourseRecommendation], summary="Recomendar cursos personalizados para una habilidad")
def get_user_course_recommendations(
    skill: str = Query(..., description="Slug de la habilidad"),
    current_user=Depends(get_current_user)
):
    profile = UserService.get_profile(current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil de usuario no configurado."
        )
        
    skills_catalog = CatalogService.get_all_skills()
    s_info = next((s for s in skills_catalog if s["slug"] == skill), None)
    if not s_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Habilidad '{skill}' no encontrada en el catálogo."
        )
        
    courses_catalog = CatalogService.get_all_courses()
    
    user_skills = profile.get("skills", [])
    user_level = next((us["level"] for us in user_skills if us["skill_slug"] == skill), 0)
    
    roles = CatalogService.get_all_role_targets()
    target_role_id = profile.get("target_role_id")
    target_role = next((r["label"] for r in roles if r["id"] == target_role_id), "")
    
    recommendations = AnalysisService.recommend_courses(
        skill_slug=skill,
        user_level=user_level,
        availability=profile.get("weekly_hours", 10),
        preferences=profile.get("learning_preferences", []),
        target_role=target_role,
        courses_catalog=courses_catalog,
        skill_name=s_info["name"]
    )
    return recommendations