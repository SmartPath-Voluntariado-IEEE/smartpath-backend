"""
Bolsa laboral: ofertas recomendadas según la ruta del usuario.

Se apoya en lo que producen HU-57 (ofertas reales recolectadas) y HU-58
(tecnologías y requisitos extraídos de cada aviso) para responder la
pregunta que el usuario se hace de verdad: *de todo lo que hay publicado,
¿qué me sirve a mí, dado el camino que elegí?*

`get_user_job_matches` ya existía y contesta otra cosa: qué porcentaje de lo
que pide una oferta ya sabe el usuario hoy. Eso deja arriba del listado las
ofertas fáciles aunque no tengan nada que ver con su ruta — una oferta que
pide solo Excel da 100% para casi cualquiera. Aquí el puntaje combina dos
señales distintas y las devuelve por separado, para que la interfaz pueda
explicar el porqué en vez de mostrar un número opaco:

- **Alineación**: cuánto tiene que ver la oferta con la ruta elegida.
- **Preparación**: cuánto de lo que la oferta exige ya domina el usuario.

Una oferta muy alineada pero con preparación baja no es un mal resultado: es
justamente hacia donde apunta el roadmap, y se marca como tal.
"""

from database.database import get_admin_client
from services.catalog_service import CatalogService

# Peso de cada señal en el puntaje final. La alineación pesa más porque el
# propósito de la pestaña es orientar la ruta, no listar lo más fácil.
ALIGNMENT_WEIGHT = 0.6
READINESS_WEIGHT = 0.4

# Bonificación por nivel del puesto acorde al momento del usuario. Es un
# ajuste pequeño a propósito: corrige el orden entre ofertas parecidas, no
# debe empujar una oferta irrelevante por encima de una alineada.
SENIORITY_BONUS = 8

# Niveles de puesto apropiados según la experiencia declarada en el perfil.
SENIORITY_FIT: dict[str, set[str]] = {
    "ninguna": {"Practicante", "Junior"},
    "estudiante": {"Practicante", "Junior"},
    "practicas": {"Practicante", "Junior"},
    "junior": {"Junior", "Semi Senior"},
    "intermedio": {"Semi Senior", "Senior"},
    "avanzado": {"Senior", "Lead"},
}

PRIORITY_REQUIRED = 2


class JobRecommendationService:

    @staticmethod
    def _seniority_fit(experience_level: str | None, seniority: str | None) -> bool:
        """True si el nivel del puesto encaja con la experiencia del usuario."""

        if not seniority:
            return False

        normalized = (experience_level or "").strip().lower()

        for key, levels in SENIORITY_FIT.items():
            if key in normalized:
                return seniority in levels

        # Sin experiencia declarada, el público por defecto de SmartPath son
        # estudiantes: se favorecen prácticas y puestos de entrada.
        return seniority in {"Practicante", "Junior"}

    @staticmethod
    def _load_jobs_with_skills() -> list[dict]:
        """
        Ofertas con sus tecnologías y la exigencia de cada una.

        Se consulta aquí en lugar de reusar `CatalogService.get_all_jobs`
        porque ese método aplana las habilidades a una lista de slugs y
        descarta `priority`, que es justamente lo que distingue un requisito
        excluyente de un deseable.
        """

        response = (
            get_admin_client()
            .table("jobs")
            .select("*, job_skills(priority, skills(slug, name))")
            .order("posted_at", desc=True)
            .execute()
        )

        jobs = []

        for row in response.data or []:
            required: list[str] = []
            desirable: list[str] = []
            names: dict[str, str] = {}

            for relation in row.pop("job_skills", None) or []:
                skill = relation.get("skills") or {}
                slug = skill.get("slug")

                if not slug:
                    continue

                names[slug] = skill.get("name") or slug

                if relation.get("priority") == PRIORITY_REQUIRED:
                    required.append(slug)
                else:
                    desirable.append(slug)

            row["required_skills"] = required
            row["desirable_skills"] = desirable
            row["skill_slugs"] = required + desirable
            row["skill_names"] = names

            jobs.append(row)

        return jobs

    @staticmethod
    def _score(
        job: dict,
        route_slugs: set[str],
        user_slugs: set[str],
        experience_level: str | None,
    ) -> dict:
        """Puntúa una oferta contra la ruta y las habilidades del usuario."""

        job_slugs = set(job["skill_slugs"])
        required = set(job["required_skills"])

        route_overlap = job_slugs & route_slugs

        # Alineación: promedio de dos lecturas que se corrigen entre sí.
        # "Qué parte de la oferta es de mi ruta" sola premiaría a un aviso
        # que pide una única tecnología que resulta estar en la ruta; "qué
        # parte de mi ruta cubre la oferta" sola premiaría a los avisos que
        # enumeran veinte tecnologías. Juntas describen una oferta que es
        # a la vez del área correcta y sustancial.
        share_of_job = len(route_overlap) / len(job_slugs) if job_slugs else 0.0
        share_of_route = (
            len(route_overlap) / len(route_slugs) if route_slugs else 0.0
        )
        alignment = (share_of_job + share_of_route) / 2

        # Preparación: se mide contra los requisitos excluyentes cuando la
        # oferta los distingue. Un aviso que exige tres cosas y menciona diez
        # deseables no debería reportar 30% de preparación a quien cumple las
        # tres que de verdad piden.
        yardstick = required or job_slugs
        covered = yardstick & user_slugs
        readiness = len(covered) / len(yardstick) if yardstick else 0.0

        score = (ALIGNMENT_WEIGHT * alignment) + (READINESS_WEIGHT * readiness)

        if JobRecommendationService._seniority_fit(
            experience_level,
            job.get("seniority"),
        ):
            score += SENIORITY_BONUS / 100

        match_percentage = max(0, min(100, round(score * 100)))

        missing = sorted(job_slugs - user_slugs)

        return {
            "match_percentage": match_percentage,
            "alignment_percentage": round(alignment * 100),
            "readiness_percentage": round(readiness * 100),
            "matched_skills": sorted(job_slugs & user_slugs),
            "missing_skills": missing,
            # Lo que falta y además está en la ruta: son las habilidades que
            # el roadmap ya tiene previsto enseñar, y por eso la interfaz las
            # presenta como "esto lo desbloqueas siguiendo tu ruta".
            "missing_from_route": sorted(set(missing) & route_slugs),
            "route_skills": sorted(route_overlap),
            "required_skills": sorted(required),
            "desirable_skills": sorted(job["desirable_skills"]),
            "seniority_fit": JobRecommendationService._seniority_fit(
                experience_level,
                job.get("seniority"),
            ),
        }

    @staticmethod
    def get_recommendations(
        user_id: str,
        token: str | None = None,
        limit: int = 30,
        offset: int = 0,
        min_match: int = 0,
        seniority: str | None = None,
        remote_only: bool = False,
        search: str | None = None,
    ) -> dict:
        """
        Ofertas recomendadas para el usuario, ordenadas por afinidad.

        Devuelve también el rol objetivo y las habilidades de la ruta para
        que la interfaz pueda explicar sobre qué base se recomendó, sin tener
        que pedir el perfil por separado.
        """

        from services.user_service import UserService

        profile = UserService.get_profile(user_id, token=token) or {}
        target_role_id = profile.get("target_role_id") or "fullstack"
        experience_level = profile.get("experience_level")

        roles = CatalogService.get_all_role_targets()

        target_role = next(
            (role for role in roles if role["id"] == target_role_id),
            None,
        )

        route_slugs = set(
            (target_role or {}).get("core_skill_slugs") or []
        )

        user_slugs = {
            item["skill_slug"]
            for item in profile.get("skills") or []
            if item.get("skill_slug")
        }

        jobs = JobRecommendationService._load_jobs_with_skills()

        results = []

        for job in jobs:
            if remote_only and not job.get("is_remote"):
                continue

            if seniority and (job.get("seniority") or "") != seniority:
                continue

            if search:
                haystack = " ".join(
                    str(job.get(field) or "")
                    for field in ("position", "company", "location")
                ).lower()

                if search.lower() not in haystack:
                    continue

            scored = JobRecommendationService._score(
                job,
                route_slugs,
                user_slugs,
                experience_level,
            )

            if scored["match_percentage"] < min_match:
                continue

            job.pop("skill_names", None)

            results.append({"job": job, **scored})

        # Ante empate de afinidad manda la oferta más reciente: entre dos
        # avisos igual de pertinentes, el que se publicó antes tiene más
        # probabilidad de estar ya cerrado. No hace falta ordenar por fecha
        # aquí: la consulta ya vino ordenada por `posted_at` descendente y el
        # sort de Python es estable, así que el desempate se conserva solo.
        results.sort(key=lambda item: -item["match_percentage"])

        total = len(results)

        return {
            "target_role_id": target_role_id,
            "target_role_label": (target_role or {}).get("label"),
            "route_skills": sorted(route_slugs),
            "user_skills": sorted(user_slugs),
            "total": total,
            "results": results[offset : offset + limit],
        }
