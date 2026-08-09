import re
import unicodedata

import httpx

from core.config import settings
from database.database import get_admin_client


class VacancyService:

    @staticmethod
    def _normalize_salary(value):
        """Convierte un salario válido a entero; si no existe, devuelve None."""
        if value is None:
            return None

        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None

    @staticmethod
    async def search_jobs():
        """Consulta vacantes en la API de TheirStack."""

        headers = {
            "Authorization": f"Bearer {settings.THEIRSTACK_API_KEY}",
            "Content-Type": "application/json",
        }

        body = {
            "job_description_pattern_or": ["analytics"],
            "limit": 25,
            "page": 0,
            "posted_at_max_age_days": 30,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.theirstack.com/v1/jobs/search",
                headers=headers,
                json=body,
            )

        # Produce un error claro si TheirStack responde 401, 402, 422, etc.
        response.raise_for_status()

        return response.json()

    @staticmethod
    async def collect_and_save_jobs():
        """Obtiene las vacantes de TheirStack y las guarda en Supabase."""

        response_data = await VacancyService.search_jobs()
        source_jobs = response_data.get("data", [])

        jobs_to_insert = []

        for job in source_jobs:
            salary = (
                job.get("min_annual_salary")
                or job.get("max_annual_salary")
                or job.get("salary")
            )

            seniority = (
                job.get("seniority")
                or job.get("seniority_level")
            )

            if isinstance(seniority, list):
                seniority = ", ".join(
                    str(value)
                    for value in seniority
                )
            elif seniority is not None:
                seniority = str(seniority)

            jobs_to_insert.append(
                {
                    "company": (
                        job.get("company")
                        or job.get("company_name")
                    ),
                    "position": (
                        job.get("job_title")
                        or job.get("title")
                    ),
                    "salary": VacancyService._normalize_salary(
                        salary
                    ),
                    "seniority": seniority,
                    "description": (
                        job.get("description")
                        or job.get("job_description")
                    ),
                }
            )

        if not jobs_to_insert:
            return {
                "message": "TheirStack no devolvió vacantes.",
                "collected": 0,
                "saved": 0,
            }

        admin_client = get_admin_client()

        result = (
            admin_client
            .table("jobs")
            .insert(jobs_to_insert)
            .execute()
        )

        inserted_jobs = result.data or []

        return {
            "message": (
                "Vacantes recolectadas y guardadas correctamente."
            ),
            "collected": len(source_jobs),
            "saved": len(inserted_jobs),
            "data": inserted_jobs,
        }

    @staticmethod
    def _normalize_text(text: str) -> str:
        """
        Convierte el texto a minúsculas y elimina tildes.

        Ejemplo: 'Visualización' -> 'visualizacion'.
        """
        normalized = unicodedata.normalize(
            "NFD",
            text.lower(),
        )

        return "".join(
            character
            for character in normalized
            if unicodedata.category(character) != "Mn"
        )

    @staticmethod
    def _contains_alias(
        description: str,
        alias: str,
    ) -> bool:
        """
        Busca un alias como palabra o expresión completa.

        Evita encontrar, por ejemplo, 'java' dentro de 'javascript'.
        """
        normalized_description = (
            VacancyService._normalize_text(description)
        )

        normalized_alias = VacancyService._normalize_text(
            alias.strip()
        )

        if not normalized_alias:
            return False

        pattern = (
            rf"(?<!\w){re.escape(normalized_alias)}(?!\w)"
        )

        return (
            re.search(
                pattern,
                normalized_description,
            )
            is not None
        )

    @staticmethod
    async def extract_and_save_job_skills():
        """
        Detecta habilidades en las descripciones de las vacantes
        y guarda las relaciones en job_skills.
        """

        admin_client = get_admin_client()

        jobs_result = (
            admin_client
            .table("jobs")
            .select("id, description")
            .execute()
        )

        skills_result = (
            admin_client
            .table("skills")
            .select("id, name, aliases")
            .execute()
        )

        jobs = jobs_result.data or []
        skills = skills_result.data or []

        if not jobs:
            return {
                "message": "No existen vacantes para analizar.",
                "jobs_analyzed": 0,
                "relations_created": 0,
            }

        if not skills:
            return {
                "message": "La tabla skills está vacía.",
                "jobs_analyzed": 0,
                "relations_created": 0,
            }

        relations = []

        for job in jobs:
            description = job.get("description") or ""

            if not description:
                continue

            for skill in skills:
                aliases = skill.get("aliases") or []

                search_terms = [
                    skill.get("name", ""),
                    *aliases,
                ]

                skill_found = any(
                    VacancyService._contains_alias(
                        description,
                        term,
                    )
                    for term in search_terms
                    if term
                )

                if skill_found:
                    relations.append(
                        {
                            "job_id": job["id"],
                            "skill_id": skill["id"],
                            "priority": 1,
                        }
                    )

        if not relations:
            return {
                "message": (
                    "No se encontraron habilidades técnicas."
                ),
                "jobs_analyzed": len(jobs),
                "relations_created": 0,
            }

        result = (
            admin_client
            .table("job_skills")
            .upsert(
                relations,
                on_conflict="job_id,skill_id",
            )
            .execute()
        )

        saved_relations = result.data or []

        return {
            "message": "Habilidades extraídas correctamente.",
            "jobs_analyzed": len(jobs),
            "relations_detected": len(relations),
            "relations_created": len(saved_relations),
        }
