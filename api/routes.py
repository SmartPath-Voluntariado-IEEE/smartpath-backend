
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from schemas.analysis import (
    CourseRecommendation,
    GapAnalysisResponse,
    RoadmapLevel,
)
from schemas.auth import UserMeResponse
from schemas.catalog import (
    CourseResponse,
    JobResponse,
    RoleTargetResponse,
    SkillResponse,
)
from schemas.onboarding import (
    InterestAreaResponse,
    OnboardingCareerRequest,
    OnboardingInterestsRequest,
    OnboardingNameRequest,
    OnboardingStageRequest,
    OnboardingStepResponse,
    OnboardingTargetRoleRequest,
)
from schemas.user import UserProfileResponse, UserProfileUpdate
from services.analysis_service import AnalysisService
from services.auth_service import AuthService
from services.catalog_service import CatalogService
from services.course_collector_service import CourseCollectorService
from services.course_ingestion_service import CourseIngestionService
from services.onboarding import ChatbotOnboarding
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
                f"{error!s}"
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
# RUTAS DEL CHATBOT DE ONBOARDING
# ============================================

@router.get(
    "/onboarding/start",
    response_model=OnboardingStepResponse,
    summary="Iniciar o retomar la conversación de onboarding",
)
def start_onboarding(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user=Depends(get_current_user),
):
    default_name = (
        current_user.user_metadata.get("full_name")
        if current_user.user_metadata
        else None
    )

    return ChatbotOnboarding.start(
        user_id=current_user.id,
        default_name=default_name,
        token=credentials.credentials,
    )


@router.post(
    "/onboarding/name",
    response_model=OnboardingStepResponse,
    summary="Guardar el nombre del usuario (HU-29)",
)
def save_onboarding_name(
    payload: OnboardingNameRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user=Depends(get_current_user),
):
    return ChatbotOnboarding.save_name(
        user_id=current_user.id,
        email=current_user.email,
        full_name=payload.full_name,
        token=credentials.credentials,
    )


@router.post(
    "/onboarding/career",
    response_model=OnboardingStepResponse,
    summary="Guardar la carrera del usuario (HU-29)",
)
def save_onboarding_career(
    payload: OnboardingCareerRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user=Depends(get_current_user),
):
    return ChatbotOnboarding.save_career(
        user_id=current_user.id,
        email=current_user.email,
        career=payload.career,
        token=credentials.credentials,
    )


@router.post(
    "/onboarding/stage",
    response_model=OnboardingStepResponse,
    summary="Guardar el ciclo académico o marcar como egresado (HU-29)",
)
def save_onboarding_stage(
    payload: OnboardingStageRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user=Depends(get_current_user),
):
    if payload.academic_cycle is None and not payload.is_graduated:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Debes enviar 'academic_cycle' o marcar "
                "'is_graduated' como true."
            ),
        )

    return ChatbotOnboarding.save_academic_stage(
        user_id=current_user.id,
        email=current_user.email,
        academic_cycle=payload.academic_cycle,
        is_graduated=payload.is_graduated,
        token=credentials.credentials,
    )


@router.get(
    "/onboarding/interest-areas",
    response_model=list[InterestAreaResponse],
    summary="Obtener las áreas de tecnología disponibles (HU-30)",
)
def get_onboarding_interest_areas():
    return ChatbotOnboarding.get_interest_areas()


@router.post(
    "/onboarding/interests",
    response_model=OnboardingStepResponse,
    summary="Guardar áreas de interés y sugerir líneas de carrera (HU-30)",
)
def save_onboarding_interests(
    payload: OnboardingInterestsRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user=Depends(get_current_user),
):
    return ChatbotOnboarding.save_interests(
        user_id=current_user.id,
        email=current_user.email,
        interest_ids=payload.interest_ids,
        token=credentials.credentials,
    )


@router.post(
    "/onboarding/target-role",
    response_model=OnboardingStepResponse,
    summary="Guardar el objetivo profesional del usuario (HU-31)",
)
def save_onboarding_target_role(
    payload: OnboardingTargetRoleRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user=Depends(get_current_user),
):
    return ChatbotOnboarding.save_target_role(
        user_id=current_user.id,
        email=current_user.email,
        target_role_id=payload.target_role_id,
        token=credentials.credentials,
    )


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
    response_model=list[SkillResponse],
    summary="Obtener catálogo de habilidades",
)
def get_catalog_skills():
    return CatalogService.get_all_skills()


@router.get(
    "/catalog/jobs",
    response_model=list[JobResponse],
    summary="Obtener catálogo de ofertas laborales",
)
def get_catalog_jobs():
    return CatalogService.get_all_jobs()

@router.get(
    "/courses/collect",
    summary="Recolectar cursos desde fuentes externas",
)
@router.post(
    "/courses/ingest",
    summary="Recolectar, normalizar y almacenar cursos",
)
def ingest_courses(
    query: str = Query(
        ...,
        min_length=1,
        description="Tema o habilidad a buscar",
    ),
    max_items: int = Query(
        10,
        ge=1,
        le=50,
        description="Cantidad máxima de cursos a procesar",
    ),
    _current_user=Depends(get_current_user),
):
    return CourseIngestionService.ingest_courses(
        search_query=query,
        max_items=max_items,
    )
def collect_courses(
    query: str = Query(
        ...,
        min_length=1,
        description="Tema o habilidad a buscar",
    ),
    max_items: int = Query(
        10,
        ge=1,
        le=50,
        description="Cantidad máxima de cursos a recolectar",
    ),
    _current_user=Depends(get_current_user),

):
    return CourseCollectorService.collect_courses(
        search_query=query,
        max_items=max_items,
    )

@router.get(
    "/catalog/courses",
    response_model=list[CourseResponse],
    summary="Obtener catálogo de cursos",
)
def get_catalog_courses(
    skill: str | None = Query(
        None,
        description="Slug de la habilidad a filtrar",
    ),
):
    return CatalogService.get_all_courses(skill_slug=skill)


@router.get(
    "/catalog/roles",
    response_model=list[RoleTargetResponse],
    summary="Obtener catálogo de roles objetivos",
)
def get_catalog_roles():
    return CatalogService.get_all_role_targets()

@router.get(
    "/catalog/roles/{role_id}/skills",
    response_model=list[SkillResponse],
    summary="Obtener habilidades relacionadas con un rol",
)
def get_catalog_role_skills(role_id: str):
    role_skills = CatalogService.get_role_skills(role_id)

    if role_skills is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El rol '{role_id}' no existe.",
        )

    return role_skills

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
    response_model=list[RoadmapLevel],
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
    response_model=list[CourseRecommendation],
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
