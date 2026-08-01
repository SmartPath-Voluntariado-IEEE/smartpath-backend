from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from schemas.analysis import (
    CourseRecommendation,
    GapAnalysisResponse,
    MarketSkillStat,
    RoadmapLevel,
)
from schemas.auth import UserMeResponse
from schemas.catalog import (
    CourseResponse,
    JobResponse,
    RoleTargetResponse,
    SkillResponse,
)
from schemas.user import UserProfileResponse, UserProfileUpdate
from services.analysis_service import AnalysisService
from services.auth_service import AuthService
from services.catalog_service import CatalogService
from services.user_service import UserService
from services.vacancy_service import VacancyService


router = APIRouter()
security = HTTPBearer()


# ============================================
# AUTENTICACIÓN
# ============================================

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials

    try:
        # Validamos el token obtenido del frontend con Supabase.
        user = AuthService.get_user_by_token(token)
        return user

    except Exception as error:
        print(
            "❌ [AUTH REJECTED 401]: "
            f"Token de usuario no válido o expirado: {error}"
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Sesión inválida o expirada en el backend: "
                f"{str(error)}"
            ),
            headers={"WWW-Authenticate": "Bearer"},
        )


# ============================================
# RUTAS DE AUTENTICACIÓN Y PERFIL
# ============================================

@router.get(
    "/users/me",
    response_model=UserMeResponse,
    summary="Obtener usuario autenticado",
)
def get_dashboard_info(current_user=Depends(get_current_user)):
    return UserMeResponse(
        status="authorized",
        message="Estás autenticado correctamente dentro del sistema.",
        user_details={
            "id": current_user.id,
            "email": current_user.email,
            "name": (
                current_user.user_metadata.get("full_name")
                if current_user.user_metadata
                else None
            ),
            "avatar": (
                current_user.user_metadata.get("avatar_url")
                if current_user.user_metadata
                else None
            ),
        },
    )


@router.get(
    "/users/profile",
    response_model=UserProfileResponse,
    summary="Obtener el perfil del usuario",
)
def get_user_profile(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user=Depends(get_current_user),
):
    profile = UserService.get_profile(
        current_user.id,
        token=credentials.credentials,
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil de usuario no encontrado en la base de datos.",
        )

    return profile


@router.post(
    "/users/profile",
    response_model=UserProfileResponse,
    summary="Crear o actualizar el perfil del usuario",
)
def upsert_user_profile(
    profile_data: UserProfileUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user=Depends(get_current_user),
):
    default_name = (
        current_user.user_metadata.get("full_name")
        if current_user.user_metadata
        else None
    )

    profile = UserService.upsert_profile(
        user_id=current_user.id,
        email=current_user.email,
        default_name=default_name,
        profile_data=profile_data,
        token=credentials.credentials,
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo crear o actualizar el perfil del usuario.",
        )

    return profile


# ============================================
# RUTAS DE VACANTES
# ============================================

@router.get(
    "/jobs/search",
    summary="Buscar ofertas de empleo",
)
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


# ============================================
# RUTAS DE CATÁLOGOS PÚBLICOS
# ============================================

@router.get(
    "/catalog/skills",
    response_model=List[SkillResponse],
    summary="Obtener catálogo de habilidades",
)
def get_catalog_skills():
    return CatalogService.get_all_skills()


@router.get(
    "/catalog/jobs",
    response_model=List[JobResponse],
    summary="Obtener catálogo de ofertas laborales",
)
def get_catalog_jobs():
    return CatalogService.get_all_jobs()


@router.get(
    "/catalog/courses",
    response_model=List[CourseResponse],
    summary="Obtener catálogo de cursos",
)
def get_catalog_courses(
    skill: Optional[str] = Query(
        None,
        description="Slug de la habilidad a filtrar",
    ),
):
    return CatalogService.get_all_courses(skill_slug=skill)


@router.get(
    "/catalog/roles",
    response_model=List[RoleTargetResponse],
    summary="Obtener catálogo de roles objetivos",
)
def get_catalog_roles():
    return CatalogService.get_all_role_targets()


# ============================================
# RUTAS DE ANÁLISIS Y ROADMAP
# ============================================

@router.get(
    "/users/gap-analysis",
    response_model=GapAnalysisResponse,
    summary="Analizar brecha de habilidades del usuario",
)
def get_user_gap_analysis(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user=Depends(get_current_user),
):
    profile = UserService.get_profile(
        current_user.id,
        token=credentials.credentials,
    )

    if not profile:
        profile = {
            "target_role_id": "fullstack",
            "skills": [],
        }

    target_role_id = profile.get("target_role_id") or "fullstack"

    roles = CatalogService.get_all_role_targets()

    target_role = next(
        (
            role
            for role in roles
            if role["id"] == target_role_id
        ),
        None,
    )

    if not target_role and roles:
        target_role = roles[0]

    if not target_role:
        target_role = {
            "id": target_role_id,
            "label": "Full Stack Developer",
            "core_skill_slugs": [
                "typescript",
                "react",
                "nodejs",
                "postgres",
                "git",
                "rest",
                "docker",
            ],
        }

    jobs = CatalogService.get_all_jobs()
    skills_catalog = CatalogService.get_all_skills()

    market = AnalysisService.market_skill_frequency(
        jobs,
        skills_catalog,
    )

    user_skills = profile.get("skills", [])

    analysis = AnalysisService.analyze_gap(
        user_skills,
        target_role,
        market,
        skills_catalog,
    )

    return analysis


@router.get(
    "/users/roadmap",
    response_model=List[RoadmapLevel],
    summary="Generar roadmap personalizado para el usuario",
)
def get_user_roadmap(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user=Depends(get_current_user),
):
    gap = get_user_gap_analysis(
        credentials,
        current_user,
    )

    gap_dict = (
        gap
        if isinstance(gap, dict)
        else gap.model_dump()
    )

    return AnalysisService.generate_roadmap(gap_dict)


@router.get(
    "/users/course-recommendations",
    response_model=List[CourseRecommendation],
    summary="Recomendar cursos personalizados para una habilidad",
)
def get_user_course_recommendations(
    skill: str = Query(
        ...,
        description="Slug de la habilidad",
    ),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user=Depends(get_current_user),
):
    profile = UserService.get_profile(
        current_user.id,
        token=credentials.credentials,
    )

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil de usuario no configurado.",
        )

    skills_catalog = CatalogService.get_all_skills()

    skill_info = next(
        (
            skill_item
            for skill_item in skills_catalog
            if skill_item["slug"] == skill
        ),
        None,
    )

    if not skill_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Habilidad '{skill}' no encontrada en el catálogo.",
        )

    courses_catalog = CatalogService.get_all_courses()
    user_skills = profile.get("skills", [])

    user_level = next(
        (
            user_skill["level"]
            for user_skill in user_skills
            if user_skill["skill_slug"] == skill
        ),
        0,
    )

    roles = CatalogService.get_all_role_targets()
    target_role_id = profile.get("target_role_id")

    target_role = next(
        (
            role["label"]
            for role in roles
            if role["id"] == target_role_id
        ),
        "",
    )

    recommendations = AnalysisService.recommend_courses(
        skill_slug=skill,
        user_level=user_level,
        availability=profile.get("weekly_hours", 10),
        preferences=profile.get("learning_preferences", []),
        target_role=target_role,
        courses_catalog=courses_catalog,
        skill_name=skill_info["name"],
    )

    return recommendations