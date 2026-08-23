"""
HU-58: identificar habilidades, tecnologías y requisitos de cada oferta.

La descripción de un aviso es texto libre. Este módulo la convierte en dos
cosas que sí se pueden consultar y comparar contra la ruta del usuario:

1. **Tecnologías** (`job_skills`), reutilizando `skill_matcher` — el mismo
   criterio que ya usan cursos y vacantes, para que "React" signifique lo
   mismo en todo el backend.

2. **Requisitos no técnicos** (`jobs.requirements`): años de experiencia,
   nivel educativo, idioma y modalidad de contrato.

La distinción entre exigido y deseable es el punto fino. Un aviso que pide
"Python (excluyente)" y menciona "deseable AWS" no está pidiendo lo mismo en
ambos casos, y una recomendación que los trate igual manda al usuario a
postular a puestos para los que no califica. Por eso el análisis es por
línea: cada tecnología hereda la exigencia de la línea o sección donde se
la nombró, y se queda con la más alta si aparece varias veces.
"""

import re
from datetime import datetime

from database.database import get_admin_client
from services.skill_matcher import match_skills, normalize_text


# Prioridad guardada en job_skills.priority.
PRIORITY_REQUIRED = 2
PRIORITY_DESIRABLE = 1


# Encabezados que abren una sección de requisitos excluyentes.
REQUIRED_SECTION_MARKERS = (
    "requisito",
    "requerimiento",
    "que buscamos",
    "lo que buscamos",
    "perfil que buscamos",
    "perfil del puesto",
    "requirements",
    "what you need",
    "must have",
    "indispensable",
    "excluyente",
)

# Encabezados que abren una sección de deseables.
DESIRABLE_SECTION_MARKERS = (
    "deseable",
    "deseables",
    "valorable",
    "nice to have",
    "plus",
    "no excluyente",
    "opcional",
    "bonus",
)

# Marcas que, dentro de una misma línea, degradan la exigencia aunque la
# sección sea de requisitos ("Requisitos: Python. Deseable: Docker").
INLINE_DESIRABLE_MARKERS = (
    "deseable",
    "valorable",
    "nice to have",
    "es un plus",
    "no excluyente",
    "opcional",
)

INLINE_REQUIRED_MARKERS = (
    "excluyente",
    "indispensable",
    "obligatorio",
    "imprescindible",
    "must have",
    "requerido",
)


# Años de experiencia. Cubre las formas en que los avisos peruanos lo
# escriben: "2 años de experiencia", "mínimo 3 años", "de 1 a 3 años",
# "experiencia de 2+ años".
EXPERIENCE_PATTERNS = (
    r"(\d+)\s*(?:\+|o\s+mas|o\s+m[áa]s)?\s*a[nñ]os?\s+de\s+experiencia",
    r"experiencia\s+(?:m[íi]nima\s+)?(?:de\s+)?(\d+)\s*(?:\+)?\s*a[nñ]os?",
    r"m[íi]nimo\s+(?:de\s+)?(\d+)\s*a[nñ]os?",
    r"(?:de\s+)?(\d+)\s*a\s*\d+\s*a[nñ]os?",
    r"(\d+)\s*\+?\s*years?\s+of\s+experience",
)

# Nivel educativo, de mayor a menor especificidad: el primero que aparezca
# en el texto gana, y por eso "titulado" debe ir antes que "universitario"
# (un aviso que pide titulado también dice "universitario").
EDUCATION_LEVELS = (
    ("Postgrado", ("maestr[íi]a", "magister", "mba", "postgrado", "doctorado")),
    ("Titulado", ("titulado", "colegiado", "licenciado", "bachiller")),
    (
        "Universitario",
        ("universitari", "carrera universitaria", "estudios universitarios"),
    ),
    ("Egresado", ("egresad",)),
    ("Estudiante", ("estudiante", "cursando", "[úu]ltimos ciclos", "practicante")),
    ("Técnico", ("t[ée]cnic", "instituto")),
)

# Nivel de inglés pedido explícitamente.
ENGLISH_LEVELS = (
    ("Avanzado", ("ingl[ée]s avanzado", "advanced english", "ingl[ée]s c1", "ingl[ée]s c2")),
    ("Intermedio", ("ingl[ée]s intermedio", "intermediate english", "ingl[ée]s b1", "ingl[ée]s b2")),
    ("Básico", ("ingl[ée]s b[áa]sico", "basic english", "ingl[ée]s a1", "ingl[ée]s a2")),
    ("Requerido", ("ingl[ée]s", "english")),
)

# Modalidad de contrato / jornada.
CONTRACT_TYPES = (
    ("Prácticas", ("pr[áa]cticas pre", "pr[áa]cticas profesionales", "practicante")),
    ("Tiempo completo", ("tiempo completo", "full time", "full-time", "jornada completa")),
    ("Medio tiempo", ("medio tiempo", "part time", "part-time")),
    ("Freelance", ("freelance", "por proyecto", "honorarios")),
)

# Modalidad de trabajo.
WORK_MODES = (
    ("Remoto", ("remoto", "remote", "teletrabajo", "home office")),
    ("Híbrido", ("h[íi]brido", "hybrid", "semipresencial")),
    ("Presencial", ("presencial", "on-site", "onsite")),
)


class JobRequirementsService:

    # ------------------------------------------------
    # Exigencia por línea
    # ------------------------------------------------

    @staticmethod
    def _line_priority(line: str, section_priority: int) -> int:
        """
        Exigencia de una línea, dada la sección en la que está.

        Una marca dentro de la propia línea pesa más que la sección: el aviso
        que abre "Requisitos:" y luego enumera "Deseable: Kubernetes" está
        diciendo, para esa línea, que Kubernetes no es excluyente.
        """

        normalized = normalize_text(line)

        if any(marker in normalized for marker in INLINE_REQUIRED_MARKERS):
            return PRIORITY_REQUIRED

        if any(marker in normalized for marker in INLINE_DESIRABLE_MARKERS):
            return PRIORITY_DESIRABLE

        return section_priority

    @staticmethod
    def _section_priority(line: str, current: int) -> int:
        """
        Actualiza la sección activa si la línea es un encabezado.

        Solo se consideran encabezados las líneas cortas: "Requisitos:" abre
        una sección, pero una frase larga que menciona la palabra requisitos
        en medio de un párrafo no cambia el contexto de lo que sigue.
        """

        normalized = normalize_text(line)

        if len(normalized) > 80:
            return current

        if any(marker in normalized for marker in DESIRABLE_SECTION_MARKERS):
            return PRIORITY_DESIRABLE

        if any(marker in normalized for marker in REQUIRED_SECTION_MARKERS):
            return PRIORITY_REQUIRED

        return current

    @staticmethod
    def extract_skills(description: str, skills_catalog: list[dict]) -> dict[int, int]:
        """
        Tecnologías mencionadas en la descripción, con su exigencia.

        Devuelve {skill_id: priority}. Se recorre línea por línea en lugar de
        analizar el texto entero porque la exigencia es una propiedad del
        lugar donde se nombra la tecnología, no del aviso completo.
        """

        if not description:
            return {}

        found: dict[int, int] = {}
        section = PRIORITY_DESIRABLE

        for raw_line in description.splitlines():
            line = raw_line.strip()

            if not line:
                continue

            section = JobRequirementsService._section_priority(line, section)
            priority = JobRequirementsService._line_priority(line, section)

            for skill in match_skills(line, skills_catalog):
                skill_id = skill.get("id")

                if skill_id is None:
                    continue

                # Si la tecnología aparece en dos sitios, manda el más
                # exigente: pedirla como excluyente en un punto no deja de
                # ser un requisito porque más abajo se la mencione de paso.
                found[skill_id] = max(found.get(skill_id, 0), priority)

        return found

    # ------------------------------------------------
    # Requisitos no técnicos
    # ------------------------------------------------

    @staticmethod
    def _first_match(text: str, table) -> str | None:
        """Primera etiqueta de `table` cuyos patrones aparecen en el texto."""

        for label, patterns in table:
            for pattern in patterns:
                if re.search(pattern, text):
                    return label

        return None

    @staticmethod
    def extract_experience_years(text: str) -> int | None:
        """
        Años de experiencia mínimos pedidos.

        Se queda con el valor más bajo encontrado, no con el primero: un
        aviso que dice "2 años en backend" y "5 años en liderazgo" pide 2
        años para entrar, y tomar el 5 excluiría al usuario de una oferta a
        la que sí puede postular. Se descartan cifras por encima de 20, que
        casi siempre son un año calendario o un número de vacantes mal
        capturado.
        """

        values = []

        for pattern in EXPERIENCE_PATTERNS:
            for raw in re.findall(pattern, text):
                try:
                    value = int(raw)
                except (TypeError, ValueError):
                    continue

                if 0 < value <= 20:
                    values.append(value)

        return min(values) if values else None

    @staticmethod
    def extract_requirements(description: str, position: str = "") -> dict:
        """
        Requisitos no técnicos, listos para guardar en la fila de la oferta.

        `requirements` sale como lista de objetos y no como texto suelto para
        que el frontend pueda pintarlos como chips sin volver a parsear nada.
        """

        text = normalize_text(f"{position}\n{description or ''}")

        experience_years = JobRequirementsService.extract_experience_years(text)
        education = JobRequirementsService._first_match(text, EDUCATION_LEVELS)
        english = JobRequirementsService._first_match(text, ENGLISH_LEVELS)
        contract = JobRequirementsService._first_match(text, CONTRACT_TYPES)
        work_mode = JobRequirementsService._first_match(text, WORK_MODES)

        requirements = []

        if experience_years is not None:
            requirements.append(
                {
                    "type": "experiencia",
                    "label": (
                        f"{experience_years} año de experiencia"
                        if experience_years == 1
                        else f"{experience_years} años de experiencia"
                    ),
                    "value": experience_years,
                }
            )

        for req_type, value in (
            ("educacion", education),
            ("idioma", english),
            ("contrato", contract),
            ("modalidad", work_mode),
        ):
            if value:
                label = (
                    f"Inglés {value.lower()}"
                    if req_type == "idioma" and value != "Requerido"
                    else value
                )

                requirements.append(
                    {"type": req_type, "label": label, "value": value}
                )

        return {
            "experience_years_min": experience_years,
            "education_level": education,
            "english_required": english is not None,
            "requirements": requirements,
        }

    # ------------------------------------------------
    # Persistencia
    # ------------------------------------------------

    @staticmethod
    def extract_and_save(job_ids: list[int] | None = None) -> dict:
        """
        Analiza las ofertas y guarda tecnologías y requisitos.

        Con `job_ids` analiza solo esas (lo que hace el recolector tras cada
        corrida); sin ellos, reanaliza el catálogo completo — útil cuando se
        añaden habilidades nuevas al catálogo y hay que reevaluar lo viejo.
        """

        client = get_admin_client()

        jobs_query = (
            client
            .table("jobs")
            .select("id, position, description")
        )

        if job_ids:
            jobs_query = jobs_query.in_("id", job_ids)

        jobs = jobs_query.execute().data or []

        skills_catalog = (
            client
            .table("skills")
            .select("id, name, aliases")
            .execute()
            .data
            or []
        )

        if not jobs:
            return {
                "message": "No hay ofertas para analizar.",
                "jobs_analyzed": 0,
                "relations_created": 0,
            }

        if not skills_catalog:
            return {
                "message": "El catálogo de habilidades está vacío.",
                "jobs_analyzed": 0,
                "relations_created": 0,
            }

        relations = []
        analyzed_ids = []
        now = datetime.now().isoformat(timespec="seconds")

        for job in jobs:
            job_id = job["id"]
            description = job.get("description") or ""
            position = job.get("position") or ""

            skill_priorities = JobRequirementsService.extract_skills(
                description,
                skills_catalog,
            )

            for skill_id, priority in skill_priorities.items():
                relations.append(
                    {
                        "job_id": job_id,
                        "skill_id": skill_id,
                        "priority": priority,
                    }
                )

            extracted = JobRequirementsService.extract_requirements(
                description,
                position,
            )

            # Se actualiza fila por fila y no en lote porque cada oferta
            # recibe valores distintos; un upsert masivo exigiría reenviar
            # todas las columnas de `jobs` y arriesgaría pisar lo scrapeado.
            (
                client
                .table("jobs")
                .update({**extracted, "requirements_extracted_at": now})
                .eq("id", job_id)
                .execute()
            )

            analyzed_ids.append(job_id)

        relations_created = 0

        if relations:
            # Las relaciones anteriores se borran antes de reinsertar: si una
            # habilidad deja de mencionarse tras reanalizar, debe desaparecer
            # de la oferta, y un upsert solo añade o pisa, nunca quita.
            (
                client
                .table("job_skills")
                .delete()
                .in_("job_id", analyzed_ids)
                .execute()
            )

            result = (
                client
                .table("job_skills")
                .upsert(relations, on_conflict="job_id,skill_id")
                .execute()
            )

            relations_created = len(result.data or [])

        return {
            "message": "Habilidades y requisitos extraídos correctamente.",
            "jobs_analyzed": len(analyzed_ids),
            "relations_created": relations_created,
        }
