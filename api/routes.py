
from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from schemas.achievement import (
    AchievementResponse,
    SyncAchievementsRequest,
    UnlockAchievementRequest,
    UserAchievementResponse,
)
from schemas.analysis import (
    CourseRecommendation,
    GapAnalysisResponse,
    RoadmapLevel,
)
from schemas.auth import UserMeResponse
from schemas.catalog import (
    CourseResponse,
    JobMatchResponse,
    JobRecommendationsResponse,
    JobResponse,
    JobScrapeResponse,
    MarketOverviewResponse,
    RoleTargetResponse,
    SkillResponse,
)
from schemas.evaluation import (
    EvaluationQuestionResponse,
    EvaluationResultResponse,
    EvaluationSubmitRequest,
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
from services.achievement_service import AchievementService
from services.analysis_service import AnalysisService
from services.auth_service import AuthService
from services.catalog_service import CatalogService
from services.course_collector_service import CourseCollectorService
from services.course_ingestion_service import CourseIngestionService
from services.evaluation_service import EvaluationService
from services.onboarding import ChatbotOnboarding
from services.user_service import UserService
from services.job_recommendation_service import JobRecommendationService
from services.job_requirements_service import JobRequirementsService
from services.job_scraping_service import JobScrapingService
from services.module_extraction_service import ModuleExtractionService
from services.module_quiz_service import ModuleQuizService
from services.course_progress_service import CourseProgressService

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
    summary="Previsualizar ofertas de un término, sin guardarlas (HU-57)",
)
def search_jobs(
    search_term: str = Query(
        ...,
        description="Término a buscar, p. ej. 'desarrollador backend'",
    ),
    results_wanted: int = Query(10, ge=1, le=100),
    hours_old: int | None = Query(
        None,
        description="Antigüedad máxima en horas. Por defecto, la configurada.",
    ),
):
    """
    Sirve para verificar qué devuelve un portal antes de recolectar en serio.

    Es síncrona a propósito: JobSpy hace peticiones bloqueantes, y declarada
    con `def` FastAPI la ejecuta en su pool de hilos en vez de dejar clavado
    el event loop mientras el portal responde.
    """

    return {
        "search_term": search_term,
        "results": JobScrapingService.scrape_term(
            search_term,
            results_wanted=results_wanted,
            hours_old=hours_old,
        ),
    }


@router.post(
    "/jobs/collect",
    response_model=JobScrapeResponse,
    summary="Recolectar ofertas por scraping y guardarlas (HU-57)",
)
def collect_jobs(
    roles: str | None = Query(
        None,
        description=(
            "Roles objetivo separados por coma (backend, frontend, "
            "fullstack, data-analyst, data-engineer, ml, devops). "
            "Si se omite, se recolecta para todos."
        ),
    ),
    results_wanted: int | None = Query(None, ge=1, le=100),
    hours_old: int | None = Query(None, ge=1),
    extract_requirements: bool = Query(
        True,
        description="Ejecutar también la extracción de HU-58 al terminar.",
    ),
):
    role_ids = (
        [role.strip() for role in roles.split(",") if role.strip()]
        if roles
        else None
    )

    result = JobScrapingService.collect_and_save_jobs(
        role_ids=role_ids,
        results_wanted=results_wanted,
        hours_old=hours_old,
        extract_requirements=extract_requirements,
    )

    # El catálogo queda cacheado en memoria: sin esto, las ofertas recién
    # guardadas no aparecerían hasta que venciera el TTL.
    CatalogService.invalidate_cache()

    return result


@router.post(
    "/jobs/extract-requirements",
    summary="Extraer habilidades, tecnologías y requisitos de las ofertas (HU-58)",
)
def extract_job_requirements(
    job_ids: str | None = Query(
        None,
        description=(
            "IDs de ofertas separados por coma. Si se omite, se reanaliza "
            "todo el catálogo."
        ),
    ),
):
    parsed_ids = None

    if job_ids:
        parsed_ids = [
            int(value.strip())
            for value in job_ids.split(",")
            if value.strip().isdigit()
        ]

    result = JobRequirementsService.extract_and_save(job_ids=parsed_ids)

    CatalogService.invalidate_cache()

    return result


@router.get(
    "/users/job-recommendations",
    response_model=JobRecommendationsResponse,
    summary="Bolsa laboral: ofertas alineadas con la ruta del usuario",
)
def get_user_job_recommendations(
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0),
    min_match: int = Query(
        0,
        ge=0,
        le=100,
        description="Descarta las ofertas por debajo de esta afinidad.",
    ),
    seniority: str | None = Query(
        None,
        description="Practicante | Junior | Semi Senior | Senior | Lead",
    ),
    remote_only: bool = Query(False),
    search: str | None = Query(
        None,
        description="Filtra por puesto, empresa o ubicación.",
    ),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user=Depends(get_current_user),
):
    return JobRecommendationService.get_recommendations(
        current_user.id,
        token=credentials.credentials,
        limit=limit,
        offset=offset,
        min_match=min_match,
        seniority=seniority,
        remote_only=remote_only,
        search=search,
    )


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
    "/market/overview",
    response_model=MarketOverviewResponse,
    summary="Resumen del mercado laboral: demanda de skills, salarios y empresas top",
)
def get_market_overview():
    return CatalogService.get_market_overview()


@router.get(
    "/users/job-matches",
    response_model=list[JobMatchResponse],
    summary="Compatibilidad del usuario con ofertas laborales",
)
def get_user_job_matches(current_user=Depends(get_current_user)):
    return CatalogService.get_user_job_matches(current_user.id)


@router.get(
    "/courses/collect",
    summary="Recolectar cursos desde fuentes externas (sin guardar)",
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
    language: str = Query(
        "spanish",
        description="Idioma de los cursos (ej. 'spanish', 'english')",
    ),
    free_only: bool = Query(
        True,
        description=(
            "Recolectar solo cursos gratuitos. SmartPath prioriza la "
            "oferta gratuita, así que se desactiva únicamente para "
            "completar habilidades sin cursos gratis disponibles."
        ),
    ),
    _current_user=Depends(get_current_user),
):
    return CourseCollectorService.collect_courses(
        search_query=query,
        max_items=max_items,
        language=language,
        free_only=free_only,
    )


@router.post(
    "/courses/ingest",
    summary="Recolectar, normalizar, almacenar y vincular cursos a una habilidad",
)
def ingest_courses(
    query: str = Query(
        ...,
        min_length=1,
        description="Tema o habilidad a buscar (texto libre)",
    ),
    max_items: int = Query(
        10,
        ge=1,
        le=50,
        description="Cantidad máxima de cursos a procesar",
    ),
    language: str = Query(
        "spanish",
        description="Idioma de los cursos (ej. 'spanish', 'english')",
    ),
    skill_slug: str | None = Query(
        None,
        description=(
            "Slug exacto de la habilidad en el catálogo (ej. 'python'), "
            "para vincular los cursos en course_skills"
        ),
    ),
    free_only: bool = Query(
        True,
        description=(
            "Ingerir solo cursos gratuitos. SmartPath prioriza la oferta "
            "gratuita, así que se desactiva únicamente para completar "
            "habilidades sin cursos gratis disponibles."
        ),
    ),
    _current_user=Depends(get_current_user),
):
    result = CourseIngestionService.ingest_courses(
        search_query=query,
        max_items=max_items,
        language=language,
        skill_slug=skill_slug,
        free_only=free_only,
    )

    CatalogService.invalidate_cache()

    return result
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
    limit: int = Query(
        12,
        ge=1,
        le=50,
        description="Cantidad máxima de cursos por página",
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Cantidad de cursos a omitir para paginar",
    ),
):
    return CatalogService.get_all_courses(
        skill_slug=skill,
        limit=limit,
        offset=offset,
    )


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
# EVALUACIONES Y PROGRESO
# ============================================


@router.get(
    "/evaluations/{skill_slug}",
    response_model=list[EvaluationQuestionResponse],
    summary="Obtener evaluación de un módulo",
)
def get_module_evaluation(
    skill_slug: str,
    _current_user=Depends(get_current_user),
):
    questions = EvaluationService.get_questions(skill_slug)

    if not questions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No existe una evaluación para este módulo.",
        )

    return questions


@router.post(
    "/evaluations/{skill_slug}/submit",
    response_model=EvaluationResultResponse,
    summary="Enviar evaluación y actualizar progreso",
)
def submit_module_evaluation(
    skill_slug: str,
    payload: EvaluationSubmitRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user=Depends(get_current_user),
):
    try:
        result = EvaluationService.submit_evaluation(
            user_id=current_user.id,
            skill_slug=skill_slug,
            answers=[
                answer.model_dump()
                for answer in payload.answers
            ],
            token=credentials.credentials,
        )

    except LookupError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    roadmap = get_user_roadmap(
        credentials,
        current_user,
    )

    roadmap_skills = [
        skill["skill_slug"]
        for level in roadmap
        for skill in level["skills"]
    ]

    progress = EvaluationService.calculate_roadmap_progress(
        user_id=current_user.id,
        roadmap_skills=roadmap_skills,
        token=credentials.credentials,
    )

    return {
        **result,
        **progress,
    }


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

    return _build_gap_analysis(profile)


def _build_gap_analysis(profile: dict | None) -> dict:
    """
    Calcula la brecha de habilidades a partir de un perfil ya cargado.

    Se separó del endpoint porque /users/roadmap y /dashboard/course-progress
    también la necesitan: antes reutilizaban el endpoint y eso volvía a pedir
    el perfil a la base de datos una segunda vez en la misma petición.
    """

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
    # El roadmap se refina con el perfil (disponibilidad, plazo, intereses) y
    # con la oferta real de cursos, no solo con la brecha de habilidades. El
    # perfil se lee una sola vez y se comparte con el cálculo de la brecha.
    profile = UserService.get_profile(
        current_user.id,
        token=credentials.credentials,
    )

    gap_dict = _build_gap_analysis(profile)

    return AnalysisService.generate_roadmap(
        gap_dict,
        profile=profile,
        courses_catalog=CatalogService.get_all_courses(),
        skills_catalog=CatalogService.get_all_skills(),
    )


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
        english_level=profile.get("english_level"),
    )

    return recommendations


@router.post(
    "/roadmap/skills/{skill_slug}/select-course",
    summary="Vincula un curso a una skill del roadmap",
)
def select_course_for_skill(
    skill_slug: str,
    course_id: int = Query(...),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user=Depends(get_current_user),
):
    return CourseProgressService.select_course_for_skill(
        user_id=current_user.id,
        skill_slug=skill_slug,
        course_id=course_id,
        token=credentials.credentials,
    )


@router.delete(
    "/roadmap/skills/{skill_slug}/course",
    summary="Desvincula el curso de una skill y resetea su progreso",
)
def unlink_course_from_skill(
    skill_slug: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user=Depends(get_current_user),
):
    CourseProgressService.unlink_course_from_skill(
        user_id=current_user.id,
        skill_slug=skill_slug,
        token=credentials.credentials,
    )
    return {"status": "unlinked"}


@router.get(
    "/courses/{course_id}/modules",
    summary="Obtiene (o extrae si no existen) los módulos de un curso",
)
def get_course_modules(
    course_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user=Depends(get_current_user),
):
    try:
        return ModuleExtractionService.get_or_extract_modules(
            course_id,
            user_id=current_user.id,
            token=credentials.credentials,
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except RuntimeError as error:
        raise HTTPException(status_code=502, detail=str(error))


@router.get(
    "/modules/{module_id}/quiz",
    summary="Obtiene (o genera) el examen de 10 preguntas de un módulo",
)
def get_module_quiz(
    module_id: str,
    _current_user=Depends(get_current_user),
):
    try:
        return ModuleQuizService.get_or_generate_quiz(module_id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error))


@router.post(
    "/modules/{module_id}/submit",
    summary="Envía las respuestas del examen de un módulo",
)
def submit_module_quiz(
    module_id: str,
    answers: list[dict] = Body(...),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user=Depends(get_current_user),
):
    try:
        return ModuleQuizService.submit_module_attempt(
            user_id=current_user.id,
            module_id=module_id,
            answers=answers,
            token=credentials.credentials,
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))


@router.get(
    "/dashboard/course-progress",
    summary="Resumen de progreso de cursos por skill para el dashboard",
)
def get_dashboard_course_progress(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user=Depends(get_current_user),
):
    profile = UserService.get_profile(
        current_user.id,
        token=credentials.credentials,
    )
    roadmap = AnalysisService.generate_roadmap(_build_gap_analysis(profile))
    all_skills = [s for level in roadmap for s in level["skills"]]

    return CourseProgressService.get_dashboard_summary(
        user_id=current_user.id,
        roadmap_skills=all_skills,
        token=credentials.credentials,
    )


# ============================================
# RUTAS DE LOGROS Y GAMIFICACIÓN
# ============================================

@router.get(
    "/catalog/achievements",
    response_model=list[AchievementResponse],
    summary="Obtener catálogo maestro de logros e insignias",
)
def get_catalog_achievements():
    return AchievementService.get_all_achievements()


@router.get(
    "/users/achievements",
    response_model=list[UserAchievementResponse],
    summary="Obtener logros desbloqueados del usuario actual",
)
def get_user_achievements(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user=Depends(get_current_user),
):
    return AchievementService.get_user_achievements(
        user_id=current_user.id,
        token=credentials.credentials,
    )


@router.post(
    "/users/achievements/unlock",
    summary="Desbloquear manualmente un logro para el usuario actual",
)
def unlock_user_achievement(
    payload: UnlockAchievementRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user=Depends(get_current_user),
):
    success = AchievementService.unlock_achievement(
        user_id=current_user.id,
        achievement_id=payload.achievement_id,
        metadata=payload.metadata,
        token=credentials.credentials,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No se pudo desbloquear el logro {payload.achievement_id}",
        )
    return {"status": "success", "unlocked": payload.achievement_id}


@router.post(
    "/users/achievements/sync",
    response_model=list[UserAchievementResponse],
    summary="Sincronizar y evaluar hitos del usuario actual",
)
def sync_user_achievements(
    payload: SyncAchievementsRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user=Depends(get_current_user),
):
    return AchievementService.sync_and_evaluate(
        user_id=current_user.id,
        sync_req=payload,
        token=credentials.credentials,
    )
