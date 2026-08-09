"""
Servicio del chatbot de onboarding.

Cubre las historias de usuario:
- HU-29: saludar y pedir nombre, carrera y ciclo (o si ya egresó).
- HU-30: preguntar qué áreas de tecnología le apasionan y sugerir
         posibles líneas de carrera.
- HU-31: confirmar el objetivo profesional y guardar el rol sugerido.

El estado de la conversación NO se guarda en una tabla aparte: se deduce
de qué campos del perfil ya están completos. Así el backend sigue siendo
stateless y el usuario puede retomar el onboarding donde lo dejó.
"""

from typing import Any

from schemas.user import UserProfileUpdate
from services.catalog_service import CatalogService
from services.user_service import UserService

# Pasos de la conversación, en orden.
STEP_ASK_NAME = "ask_name"
STEP_ASK_CAREER = "ask_career"
STEP_ASK_CYCLE = "ask_cycle"
STEP_ASK_INTERESTS = "ask_interests"
STEP_ASK_TARGET_ROLE = "ask_target_role"
STEP_COMPLETED = "completed"


# Valor que guardamos en experience_level cuando el usuario ya egresó.
GRADUATED_LABEL = "Egresado"


# Áreas de tecnología ofrecidas en la HU-30, con los roles de la tabla
# role_targets que se sugieren para cada una.
INTEREST_AREAS: list[dict[str, Any]] = [
    {
        "id": "data-analytics",
        "label": "Data Analytics",
        "description": "Analizar datos y construir reportes que apoyen decisiones.",
        "suggested_role_ids": ["data-analyst", "data-engineer"],
    },
    {
        "id": "frontend",
        "label": "Desarrollo Frontend",
        "description": "Construir interfaces web que la gente usa a diario.",
        "suggested_role_ids": ["frontend", "fullstack"],
    },
    {
        "id": "backend",
        "label": "Desarrollo Backend",
        "description": "Diseñar APIs, bases de datos y la lógica del servidor.",
        "suggested_role_ids": ["backend", "fullstack"],
    },
    {
        "id": "cloud-devops",
        "label": "Cloud & DevOps",
        "description": "Automatizar despliegues e infraestructura en la nube.",
        "suggested_role_ids": ["devops", "backend"],
    },
    {
        "id": "machine-learning",
        "label": "Inteligencia Artificial",
        "description": "Entrenar modelos que aprenden de los datos.",
        "suggested_role_ids": ["ml", "data-engineer"],
    },
    {
        "id": "cybersecurity",
        "label": "Ciberseguridad",
        "description": "Proteger sistemas y datos frente a ataques.",
        # Todavía no existe un role_target de ciberseguridad en la BD,
        # así que sugerimos los roles más cercanos.
        "suggested_role_ids": ["devops", "backend"],
    },
]


class ChatbotOnboarding:
    """Conduce la conversación de onboarding paso a paso."""

    # ============================================
    # ESTADO DE LA CONVERSACIÓN
    # ============================================

    @staticmethod
    def get_current_step(profile: dict[str, Any] | None) -> str:
        """Deduce en qué paso va el usuario a partir de su perfil."""

        if not profile:
            return STEP_ASK_NAME

        if not profile.get("full_name"):
            return STEP_ASK_NAME

        if not profile.get("career"):
            return STEP_ASK_CAREER

        cycle_answered = (
            profile.get("academic_cycle") is not None
            or profile.get("experience_level")
        )

        if not cycle_answered:
            return STEP_ASK_CYCLE

        if not profile.get("interests"):
            return STEP_ASK_INTERESTS

        if not profile.get("target_role_id"):
            return STEP_ASK_TARGET_ROLE

        return STEP_COMPLETED

    @staticmethod
    def start(
        user_id: str,
        default_name: str | None = None,
        token: str | None = None,
    ) -> dict[str, Any]:
        """
        HU-29: saluda al usuario y le hace la primera pregunta pendiente.

        Si el usuario ya avanzó antes, retoma donde se quedó en lugar de
        empezar de cero.
        """

        profile = UserService.get_profile(user_id, token=token)
        step = ChatbotOnboarding.get_current_step(profile)

        if step == STEP_ASK_NAME:
            greeting = (
                "¡Bienvenido a SmartPath! Soy tu guía y voy a acompañarte "
                "a armar tu ruta de aprendizaje. ¿Listo para esta nueva "
                "aventura?"
            )
        elif step == STEP_COMPLETED:
            greeting = "¡Qué bueno verte de nuevo! Tu perfil ya está completo."
        else:
            greeting = "¡Hola de nuevo! Continuemos donde lo dejamos."

        return {
            "step": step,
            "message": greeting,
            "question": ChatbotOnboarding._question_for_step(
                step,
                default_name=default_name,
            ),
            "options": ChatbotOnboarding._options_for_step(step),
            "profile": profile,
        }

    # ============================================
    # HU-29: NOMBRE, CARRERA Y CICLO
    # ============================================

    @staticmethod
    def save_name(
        user_id: str,
        email: str,
        full_name: str,
        token: str | None = None,
    ) -> dict[str, Any]:
        """HU-29: guarda el nombre del usuario y pregunta por su carrera."""

        full_name = (full_name or "").strip()

        if not full_name:
            return ChatbotOnboarding._retry(
                STEP_ASK_NAME,
                "No alcancé a leer tu nombre. ¿Me lo repites, por favor?",
            )

        profile = ChatbotOnboarding._update_profile(
            user_id=user_id,
            email=email,
            token=token,
            full_name=full_name,
        )

        first_name = full_name.split(" ")[0]

        return ChatbotOnboarding._advance(
            profile,
            f"¡Mucho gusto, {first_name}! Empecemos con tu camino profesional.",
        )

    @staticmethod
    def save_career(
        user_id: str,
        email: str,
        career: str,
        token: str | None = None,
    ) -> dict[str, Any]:
        """HU-29: guarda la carrera y pregunta por el ciclo."""

        career = (career or "").strip()

        if not career:
            return ChatbotOnboarding._retry(
                STEP_ASK_CAREER,
                "¿Qué carrera estás estudiando o estudiaste?",
            )

        profile = ChatbotOnboarding._update_profile(
            user_id=user_id,
            email=email,
            token=token,
            career=career,
        )

        return ChatbotOnboarding._advance(
            profile,
            f"Anotado: {career}.",
        )

    @staticmethod
    def save_academic_stage(
        user_id: str,
        email: str,
        token: str | None = None,
        academic_cycle: int | None = None,
        is_graduated: bool = False,
    ) -> dict[str, Any]:
        """
        HU-29: guarda el ciclo actual o marca al usuario como egresado.

        Se espera uno de los dos: `academic_cycle` (1 a 12) o
        `is_graduated=True`.
        """

        if is_graduated:
            profile = ChatbotOnboarding._update_profile(
                user_id=user_id,
                email=email,
                token=token,
                experience_level=GRADUATED_LABEL,
            )

            return ChatbotOnboarding._advance(
                profile,
                "¡Felicidades por haber egresado! Sigamos.",
            )

        if academic_cycle is None or not 1 <= academic_cycle <= 12:
            return ChatbotOnboarding._retry(
                STEP_ASK_CYCLE,
                "Indícame un ciclo entre 1 y 12, o dime si ya egresaste.",
            )

        profile = ChatbotOnboarding._update_profile(
            user_id=user_id,
            email=email,
            token=token,
            academic_cycle=academic_cycle,
            experience_level=f"Ciclo {academic_cycle}",
        )

        return ChatbotOnboarding._advance(
            profile,
            f"Perfecto, vas en el ciclo {academic_cycle}.",
        )

    # ============================================
    # HU-30: ÁREAS DE INTERÉS Y LÍNEAS DE CARRERA
    # ============================================

    @staticmethod
    def get_interest_areas() -> list[dict[str, Any]]:
        """HU-30: catálogo de áreas de tecnología que puede elegir."""

        return [
            {
                "id": area["id"],
                "label": area["label"],
                "description": area["description"],
            }
            for area in INTEREST_AREAS
        ]

    @staticmethod
    def suggest_roles(interest_ids: list[str]) -> list[dict[str, Any]]:
        """
        HU-30: traduce las áreas elegidas en líneas de carrera concretas.

        Solo devuelve roles que existan en la tabla role_targets, porque el
        gap-analysis y el roadmap dependen de ese id.
        """

        roles = CatalogService.get_all_role_targets()
        roles_by_id = {role["id"]: role for role in roles}

        # Cuántas de las áreas elegidas apuntan a cada rol: mientras más
        # coincidencias, más arriba aparece la sugerencia.
        scores: dict[str, int] = {}

        for interest_id in interest_ids:
            area = next(
                (
                    item
                    for item in INTEREST_AREAS
                    if item["id"] == interest_id
                ),
                None,
            )

            if not area:
                continue

            for role_id in area["suggested_role_ids"]:
                if role_id in roles_by_id:
                    scores[role_id] = scores.get(role_id, 0) + 1

        suggestions = [
            {
                "id": role_id,
                "label": roles_by_id[role_id]["label"],
                "core_skill_slugs": roles_by_id[role_id]["core_skill_slugs"],
                "match_score": score,
            }
            for role_id, score in scores.items()
        ]

        suggestions.sort(
            key=lambda item: item["match_score"],
            reverse=True,
        )

        # Si no hubo coincidencias, ofrecemos el catálogo completo para que
        # el usuario nunca se quede sin opciones.
        if not suggestions:
            return [
                {
                    "id": role["id"],
                    "label": role["label"],
                    "core_skill_slugs": role["core_skill_slugs"],
                    "match_score": 0,
                }
                for role in roles
            ]

        return suggestions

    @staticmethod
    def save_interests(
        user_id: str,
        email: str,
        interest_ids: list[str],
        token: str | None = None,
    ) -> dict[str, Any]:
        """HU-30: guarda las áreas elegidas y sugiere líneas de carrera."""

        valid_ids = {area["id"] for area in INTEREST_AREAS}

        selected = [
            interest_id
            for interest_id in (interest_ids or [])
            if interest_id in valid_ids
        ]

        if not selected:
            return ChatbotOnboarding._retry(
                STEP_ASK_INTERESTS,
                "Elige al menos un área de tecnología que te llame la atención.",
                options=ChatbotOnboarding.get_interest_areas(),
            )

        profile = ChatbotOnboarding._update_profile(
            user_id=user_id,
            email=email,
            token=token,
            interests=selected,
        )

        suggestions = ChatbotOnboarding.suggest_roles(selected)

        labels = ", ".join(
            area["label"]
            for area in INTEREST_AREAS
            if area["id"] in selected
        )

        return {
            "step": ChatbotOnboarding.get_current_step(profile),
            "message": (
                f"Con lo que me cuentas sobre {labels}, estas líneas de "
                "carrera encajan contigo."
            ),
            "question": "¿Cuál de estas quieres tener como objetivo profesional?",
            "options": suggestions,
            "profile": profile,
        }

    # ============================================
    # HU-31: OBJETIVO PROFESIONAL
    # ============================================

    @staticmethod
    def save_target_role(
        user_id: str,
        email: str,
        target_role_id: str,
        token: str | None = None,
    ) -> dict[str, Any]:
        """HU-31: guarda el rol objetivo elegido y cierra el onboarding."""

        roles = CatalogService.get_all_role_targets()

        target_role = next(
            (
                role
                for role in roles
                if role["id"] == target_role_id
            ),
            None,
        )

        if not target_role:
            return ChatbotOnboarding._retry(
                STEP_ASK_TARGET_ROLE,
                "Ese rol no está en nuestro catálogo. Elige uno de la lista.",
                options=roles,
            )

        profile = ChatbotOnboarding._update_profile(
            user_id=user_id,
            email=email,
            token=token,
            target_role_id=target_role["id"],
            professional_goal=target_role["label"],
        )

        return {
            "step": ChatbotOnboarding.get_current_step(profile),
            "message": (
                f"¡Listo! Tu objetivo es ser {target_role['label']}. "
                "Ya puedo armar tu ruta de aprendizaje."
            ),
            "question": None,
            "options": [],
            "profile": profile,
        }

    # ============================================
    # HELPERS INTERNOS
    # ============================================

    @staticmethod
    def _update_profile(
        user_id: str,
        email: str,
        token: str | None = None,
        **fields: Any,
    ) -> dict[str, Any] | None:
        """
        Guarda campos parciales del perfil reutilizando UserService.

        Se usa upsert porque el usuario ya existe en Supabase Auth pero su
        fila en `users` puede no haberse creado todavía.
        """

        default_name = fields.get("full_name")

        # upsert_profile rellena full_name cuando no se lo enviamos, así que
        # le pasamos el nombre ya guardado para no sobrescribirlo en las
        # actualizaciones parciales (carrera, ciclo, intereses, rol).
        if not default_name:
            current = UserService.get_profile(user_id, token=token)

            if current:
                default_name = current.get("full_name")

        return UserService.upsert_profile(
            user_id=user_id,
            email=email,
            default_name=default_name,
            profile_data=UserProfileUpdate(**fields),
            token=token,
        )

    @staticmethod
    def _advance(
        profile: dict[str, Any] | None,
        message: str,
    ) -> dict[str, Any]:
        """Arma la respuesta del siguiente paso tras guardar un dato."""

        step = ChatbotOnboarding.get_current_step(profile)

        return {
            "step": step,
            "message": message,
            "question": ChatbotOnboarding._question_for_step(step),
            "options": ChatbotOnboarding._options_for_step(step),
            "profile": profile,
        }

    @staticmethod
    def _retry(
        step: str,
        message: str,
        options: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Repite el paso actual cuando la respuesta no fue válida."""

        return {
            "step": step,
            "message": message,
            "question": ChatbotOnboarding._question_for_step(step),
            "options": (
                options
                if options is not None
                else ChatbotOnboarding._options_for_step(step)
            ),
            "profile": None,
        }

    @staticmethod
    def _question_for_step(
        step: str,
        default_name: str | None = None,
    ) -> str | None:
        """Texto de la pregunta que corresponde a cada paso."""

        if step == STEP_ASK_NAME:
            if default_name:
                return f"¿Te llamo {default_name} o prefieres otro nombre?"
            return "Para empezar, ¿cómo te llamas?"

        if step == STEP_ASK_CAREER:
            return "¿Qué carrera estudias o estudiaste?"

        if step == STEP_ASK_CYCLE:
            return "¿En qué ciclo vas? Si ya egresaste, también dímelo."

        if step == STEP_ASK_INTERESTS:
            return (
                "¿Qué áreas de tecnología te apasionan más? "
                "Puedes elegir más de una."
            )

        if step == STEP_ASK_TARGET_ROLE:
            return "¿Cuál quieres que sea tu objetivo profesional?"

        return None

    @staticmethod
    def _options_for_step(step: str) -> list[dict[str, Any]]:
        """Opciones que el frontend puede mostrar como botones."""

        if step == STEP_ASK_INTERESTS:
            return ChatbotOnboarding.get_interest_areas()

        if step == STEP_ASK_TARGET_ROLE:
            return CatalogService.get_all_role_targets()

        return []
