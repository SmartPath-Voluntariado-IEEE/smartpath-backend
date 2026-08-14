import re
import statistics
from typing import Any

from services.course_pricing import is_free_course

# Horas semanales que se asumen cuando el perfil no declara disponibilidad.
DEFAULT_WEEKLY_HOURS = 10

# Plazo por defecto del schema de perfil. La columna `target_months` todavía
# no existe en la tabla `users`, así que en la práctica siempre es este valor.
DEFAULT_TARGET_MONTHS = 6

WEEKS_PER_MONTH = 4.33

# La duración de un curso es tiempo de contenido, no de dominio: un video de
# una hora no equivale a saber Git. Se asume una hora de práctica por cada
# hora de curso, con un piso para que ninguna habilidad quede en "1 hora".
PRACTICE_MULTIPLIER = 2
MIN_SKILL_HOURS = 5

# Pesos del score de prioridad (HU-42). Se exponen como constantes para poder
# recalibrarlos sin tocar la lógica.
PRIORITY_DEMAND_WEIGHT = 40.0
PRIORITY_MISSING_BONUS = 25.0
PRIORITY_PARTIAL_BONUS = 12.5
PRIORITY_FREE_COURSES_BONUS = 15.0
PRIORITY_PAID_COURSES_BONUS = 7.5
PRIORITY_INTEREST_BONUS = 10.0
PRIORITY_TIER_PENALTY = 4.0

# Niveles de inglés que no permiten seguir un curso en ese idioma. El perfil
# todavía no captura este dato (`english_level` llega en NULL), así que la
# regla queda inactiva hasta que el onboarding lo pregunte.
LOW_ENGLISH_LEVELS = {"basico", "básico", "basic", "none", "ninguno", "a1", "a2"}

SKILL_TIER: dict[str, int] = {
    "git": 1, "github": 1, "sql": 1, "linux": 1, "excel": 1, "english": 1,
    "javascript": 2, "typescript": 2, "python": 2, "java": 2, "tailwind": 2, "pandas": 2,
    "react": 3, "nodejs": 3, "springboot": 3, "rest": 3, "powerbi": 3, "django": 3, "fastapi": 3,
    "nextjs": 3, "mongodb": 3, "mysql": 3, "postgres": 3,
    "docker": 4, "redis": 4, "graphql": 4, "scrum": 4,
    "kubernetes": 5, "aws": 5, "gcp": 5, "azure": 5, "tensorflow": 5,
}

def extract_skills_from_text(text: str, skills_catalog: list[dict[str, Any]]) -> list[str]:
    lower = " " + text.lower() + " "
    found = set()
    for s in skills_catalog:
        aliases = s.get("aliases")
        names = [s["name"]] + (aliases if aliases else [])
        for n in names:
            needle = n.lower()
            escaped = re.escape(needle)
            # Asegurar límites de palabra compatibles con caracteres como # o +
            pattern = rf"(^|[^a-z0-9\+#\.])({escaped})([^a-z0-9\+#]|$)"
            if re.search(pattern, lower, re.IGNORECASE):
                found.add(s["slug"])
                break
    return list(found)

class AnalysisService:
    @staticmethod
    def market_skill_frequency(jobs: list[dict[str, Any]], skills_catalog: list[dict[str, Any]]) -> list[dict[str, Any]]:
        counts = {}
        for j in jobs:
            text = f"{j.get('position', '')} {j.get('description', '')}"
            extracted = extract_skills_from_text(text, skills_catalog)
            for slug in extracted:
                counts[slug] = counts.get(slug, 0) + 1

        total = len(jobs)
        stats = []
        for slug, count in counts.items():
            s_info = next((s for s in skills_catalog if s["slug"] == slug), None)
            if s_info:
                stats.append({
                    "skill_slug": slug,
                    "name": s_info["name"],
                    "category": s_info["category"],
                    "count": count,
                    "frequency": count / total if total > 0 else 0.0
                })
        stats.sort(key=lambda x: x["count"], reverse=True)
        return stats

    @staticmethod
    def analyze_gap(user_skills: list[dict[str, Any]], target_role: dict[str, Any], market: list[dict[str, Any]], skills_catalog: list[dict[str, Any]]) -> dict[str, Any]:
        user_map = {us["skill_slug"]: us["level"] for us in user_skills}
        freq_map = {m["skill_slug"]: m["frequency"] for m in market}

        mastered = []
        partial = []
        missing = []

        core_slugs = target_role.get("core_skill_slugs", [])
        for slug in core_slugs:
            s_info = next((s for s in skills_catalog if s["slug"] == slug), None)
            if not s_info:
                continue
            lvl = user_map.get(slug)
            freq = freq_map.get(slug, 0.0)

            if lvl and lvl >= 4:
                mastered.append({
                    "skill_slug": slug,
                    "name": s_info["name"],
                    "level": lvl,
                    "marketFreq": freq
                })
            elif lvl and lvl >= 2:
                partial.append({
                    "skill_slug": slug,
                    "name": s_info["name"],
                    "level": lvl,
                    "marketFreq": freq
                })
            else:
                missing.append({
                    "skill_slug": slug,
                    "name": s_info["name"],
                    "marketFreq": freq,
                    "priority": freq * 100.0 - SKILL_TIER.get(slug, 3)
                })

        # Agregar habilidades top demandadas que no están en el core del rol ni tiene el usuario
        for m in market[:8]:
            slug = m["skill_slug"]
            if slug in core_slugs:
                continue
            if slug in user_map:
                continue
            s_info = next((s for s in skills_catalog if s["slug"] == slug), None)
            if s_info:
                missing.append({
                    "skill_slug": slug,
                    "name": s_info["name"],
                    "marketFreq": m["frequency"],
                    "priority": m["frequency"] * 60.0 - SKILL_TIER.get(slug, 3)
                })

        missing.sort(key=lambda x: x["priority"], reverse=True)

        coverage = 0.0
        if core_slugs:
            coverage = (len(mastered) + len(partial) * 0.5) / len(core_slugs)

        return {
            "target_role": target_role,
            "mastered": mastered,
            "partial": partial,
            "missing": missing,
            "coverage": coverage
        }

    @staticmethod
    def course_stats_by_skill(
        courses_catalog: list[dict[str, Any]] | None,
    ) -> dict[str, dict[str, Any]]:
        """
        Resume la oferta de cursos por habilidad: cuántos hay, cuántos son
        gratuitos y cuánto dura un curso típico gratuito.

        La duración usa la mediana y no el promedio porque el catálogo mezcla
        videos de una hora con cursos de 300, y un solo outlier deformaría la
        estimación del roadmap.
        """

        stats: dict[str, dict[str, Any]] = {}

        for course in courses_catalog or []:
            course_is_free = is_free_course(course)
            hours = course.get("duration_hours")

            for slug in course.get("skill_slugs", []):
                entry = stats.setdefault(
                    slug,
                    {
                        "total": 0,
                        "free": 0,
                        "free_hours": [],
                    },
                )

                entry["total"] += 1

                if course_is_free:
                    entry["free"] += 1

                    if hours:
                        entry["free_hours"].append(hours)

        for entry in stats.values():
            free_hours = entry.pop("free_hours")

            entry["median_free_hours"] = (
                round(statistics.median(free_hours))
                if free_hours
                else None
            )

        return stats

    @staticmethod
    def estimate_skill_hours(
        slug: str,
        skill_stats: dict[str, Any] | None,
    ) -> int:
        """
        Prefiere la duración real de los cursos gratuitos de la habilidad y
        cae a la estimación por tier cuando el catálogo no tiene el dato.
        """

        median_hours = (skill_stats or {}).get("median_free_hours")

        if median_hours:
            return max(
                round(median_hours * PRACTICE_MULTIPLIER),
                MIN_SKILL_HOURS,
            )

        tier = SKILL_TIER.get(slug, 3)
        hours_by_tier = [0, 10, 25, 40, 30, 45]

        return (
            hours_by_tier[tier]
            if tier < len(hours_by_tier)
            else 30
        )

    @staticmethod
    def score_skill_priority(
        slug: str,
        market_freq: float,
        is_missing: bool,
        skill_stats: dict[str, Any] | None,
        interests: list[str],
        category: str | None,
    ) -> float:
        """
        Score de priorización (HU-42).

        Combina la demanda del mercado con la severidad de la brecha, la
        disponibilidad real de cursos y los intereses declarados, penalizando
        el tier para no proponer una tecnología avanzada antes que su base.

        La disponibilidad de cursos entra al score porque una habilidad sin
        cursos no es accionable: recomendarla primero deja al usuario sin
        siguiente paso.
        """

        score = market_freq * PRIORITY_DEMAND_WEIGHT

        score += (
            PRIORITY_MISSING_BONUS
            if is_missing
            else PRIORITY_PARTIAL_BONUS
        )

        free_courses = (skill_stats or {}).get("free", 0)
        total_courses = (skill_stats or {}).get("total", 0)

        if free_courses:
            score += PRIORITY_FREE_COURSES_BONUS
        elif total_courses:
            score += PRIORITY_PAID_COURSES_BONUS

        normalized_interests = {i.lower() for i in interests or []}

        if slug.lower() in normalized_interests or (
            category and category.lower() in normalized_interests
        ):
            score += PRIORITY_INTEREST_BONUS

        score -= SKILL_TIER.get(slug, 3) * PRIORITY_TIER_PENALTY

        return round(score, 2)

    @staticmethod
    def generate_roadmap(
        gap: dict[str, Any],
        profile: dict[str, Any] | None = None,
        courses_catalog: list[dict[str, Any]] | None = None,
        skills_catalog: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        profile = profile or {}

        stats = AnalysisService.course_stats_by_skill(courses_catalog)

        categories = {
            s["slug"]: s.get("category")
            for s in skills_catalog or []
        }

        interests = profile.get("interests") or []

        buckets = {}

        # Combinar missing y partial, conservando de dónde vino cada skill:
        # una habilidad ausente urge más que una a medias.
        all_skills = []
        for m in gap["missing"]:
            all_skills.append({
                "skill_slug": m["skill_slug"],
                "name": m["name"],
                "marketFreq": m["marketFreq"],
                "isMissing": True,
            })
        for p in gap["partial"]:
            all_skills.append({
                "skill_slug": p["skill_slug"],
                "name": p["name"],
                "marketFreq": p["marketFreq"],
                "isMissing": False,
            })

        for m in all_skills:
            slug = m["skill_slug"]
            tier = SKILL_TIER.get(slug, 3)

            if tier not in buckets:
                buckets[tier] = []

            if not any(x["skill_slug"] == slug for x in buckets[tier]):
                skill_stats = stats.get(slug)

                buckets[tier].append({
                    "skill_slug": slug,
                    "name": m["name"],
                    "marketFreq": m["marketFreq"],
                    "estHours": AnalysisService.estimate_skill_hours(
                        slug,
                        skill_stats,
                    ),
                    "priority": AnalysisService.score_skill_priority(
                        slug=slug,
                        market_freq=m["marketFreq"],
                        is_missing=m["isMissing"],
                        skill_stats=skill_stats,
                        interests=interests,
                        category=categories.get(slug),
                    ),
                    "courseCount": (skill_stats or {}).get("total", 0),
                    "freeCourseCount": (skill_stats or {}).get("free", 0),
                })

        labels = {
            1: "Fundamentos",
            2: "Lenguajes base",
            3: "Frameworks & datos",
            4: "Contenedores & prácticas",
            5: "Cloud & especialización",
        }

        # Presupuesto de horas del usuario. El roadmap no se recorta: marca
        # hasta dónde alcanza el plazo para que el usuario decida si amplía
        # el plazo o sube sus horas semanales.
        weekly_hours = (
            profile.get("weekly_hours")
            or DEFAULT_WEEKLY_HOURS
        )
        target_months = (
            profile.get("target_months")
            or DEFAULT_TARGET_MONTHS
        )
        budget_hours = weekly_hours * target_months * WEEKS_PER_MONTH

        roadmap = []
        cumulative_hours = 0

        for lvl in sorted(buckets.keys()):
            skills = buckets[lvl]
            skills.sort(key=lambda x: x["priority"], reverse=True)

            level_hours = sum(s["estHours"] for s in skills)
            cumulative_hours += level_hours

            roadmap.append({
                "level": lvl,
                "label": labels.get(lvl, f"Nivel {lvl}"),
                "skills": skills,
                "estHours": level_hours,
                "cumulativeHours": cumulative_hours,
                "estimatedWeeks": max(
                    1,
                    round(cumulative_hours / max(weekly_hours, 1)),
                ),
                "withinTarget": cumulative_hours <= budget_hours,
            })

        return roadmap

    @staticmethod
    def recommend_courses(skill_slug: str, user_level: int, availability: int, preferences: list[str], target_role: str, courses_catalog: list[dict[str, Any]], skill_name: str, english_level: str | None = None) -> list[dict[str, Any]]:
        # Filtrar los cursos que contienen la skill seleccionada
        matched = [c for c in courses_catalog if skill_slug in c.get("skill_slugs", [])]

        user_prefs_lower = [p.lower() for p in preferences] if preferences else ["video"]
        primary_style = user_prefs_lower[0] if user_prefs_lower else "video"

        # La oferta gratuita es mayoritariamente en inglés, así que un usuario
        # que no lo domina necesita ver primero lo que está en español.
        # `english_level` llega en NULL mientras el onboarding no lo pregunte:
        # ante la duda no se penaliza ningún idioma.
        prefers_spanish = (
            english_level is not None
            and english_level.strip().lower() in LOW_ENGLISH_LEVELS
        )

        recs = []
        for c in matched:
            course_title = c.get("title", "").lower()
            course_hours = c.get("duration_hours")
            course_is_free = is_free_course(c)

            # Determinar coincidencia de formato (HU1)
            is_matched = any(p in course_title or (p == "video" and "video" in course_title) for p in user_prefs_lower)
            format_style = primary_style if is_matched else "general"

            # Calcular semanas estimadas según la disponibilidad semanal (HU2).
            # La mayoría de cursos no trae duración, y en ese caso se omite en
            # vez de inventar una estimación.
            if course_hours:
                weeks_est = max(1, round(course_hours / max(availability, 1)))
                effort_note = f" (~{weeks_est} sem a {availability}h/sem)"
            else:
                effort_note = ""

            institution = c.get("institution")
            if course_is_free:
                price_note = f"Gratis en {institution}. " if institution else "Gratis. "
            else:
                price_note = ""

            language = c.get("language")

            is_understandable = not prefers_spanish or (
                language is not None
                and language.strip().lower() in ("spanish", "español", "es")
            )

            recs.append({
                "title": c["title"],
                "platform": c["platform"],
                "institution": institution,
                "url": c["url"],
                "price": c["price"],
                "is_free": course_is_free,
                "language": language,
                "rating": c["rating"],
                "hours": course_hours,
                "level": c["level"],
                "style": format_style,
                "why": f"{price_note}Curso recomendado en formato {format_style}{effort_note} enfocado en tu meta de {target_role or 'Desarrollador'}.",
                "_matched": 1 if is_matched else 0,
                "_understandable": 1 if is_understandable else 0,
            })

        # Ordenar: primero el idioma que el usuario puede seguir (de nada
        # sirve un curso que no entiende), luego la gratuidad —el objetivo de
        # SmartPath es que no tenga que pagar para cerrar su brecha—, después
        # la preferencia de formato (HU1) y por último el rating.
        recs.sort(
            key=lambda x: (
                x["_understandable"],
                x["is_free"],
                x["_matched"],
                x["rating"] or 0,
            ),
            reverse=True,
        )

        # Remover campos auxiliares internos
        for r in recs:
            r.pop("_matched", None)
            r.pop("_understandable", None)

        return recs
