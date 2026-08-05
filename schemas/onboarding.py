from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ============================================
# REQUESTS
# ============================================

class OnboardingNameRequest(BaseModel):
    full_name: str = Field(
        ...,
        description="Nombre con el que el usuario quiere ser llamado",
    )


class OnboardingCareerRequest(BaseModel):
    career: str = Field(
        ...,
        description="Carrera que estudia o estudió el usuario",
    )


class OnboardingStageRequest(BaseModel):
    academic_cycle: Optional[int] = Field(
        None,
        ge=1,
        le=12,
        description="Ciclo actual (1 a 12). Se omite si ya egresó.",
    )
    is_graduated: bool = Field(
        False,
        description="True si el usuario ya egresó de su carrera",
    )


class OnboardingInterestsRequest(BaseModel):
    interest_ids: List[str] = Field(
        ...,
        description="Ids de las áreas de tecnología elegidas",
    )


class OnboardingTargetRoleRequest(BaseModel):
    target_role_id: str = Field(
        ...,
        description="Id del rol objetivo elegido del catálogo role_targets",
    )


# ============================================
# RESPONSES
# ============================================

class InterestAreaResponse(BaseModel):
    id: str
    label: str
    description: str


class OnboardingStepResponse(BaseModel):
    """Respuesta uniforme de todos los pasos del chatbot."""

    step: str = Field(
        ...,
        description=(
            "Paso actual: ask_name, ask_career, ask_cycle, ask_interests, "
            "ask_target_role o completed"
        ),
    )
    message: str = Field(
        ...,
        description="Lo que dice el chatbot al usuario",
    )
    question: Optional[str] = Field(
        None,
        description="Pregunta del paso actual. Es null si ya terminó.",
    )
    options: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Opciones que el frontend puede mostrar como botones",
    )
    profile: Optional[Dict[str, Any]] = Field(
        None,
        description="Perfil del usuario tras guardar la respuesta",
    )
