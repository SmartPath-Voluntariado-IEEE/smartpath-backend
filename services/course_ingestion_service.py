from services.course_collector_service import (
    CourseCollectorService,
)
from services.course_normalizer_service import (
    CourseNormalizerService,
)
from services.course_storage_service import (
    CourseStorageService,
)


class CourseIngestionService:

    @staticmethod
    def ingest_courses(
        search_query: str,
        max_items: int = 10,
        language: str = "spanish",
        skill_slug: str | None = None,
    ) -> dict:

        # 0. Resolver el skill_id antes de procesar
        skill_id = None

        if skill_slug:
            skill_id = CourseStorageService.get_skill_id_by_slug(
                skill_slug
            )

            if not skill_id:
                raise ValueError(
                    f"No se encontró la habilidad con slug "
                    f"'{skill_slug}' en el catálogo de skills."
                )

        # 1. Recolectar cursos desde Apify
        raw_courses = CourseCollectorService.collect_courses(
            search_query=search_query,
            max_items=max_items,
            language=language,
        )

        results = []
        linked_count = 0

        # 2. Procesar cada curso
        for raw_course in raw_courses:

            # Normalizar
            normalized_course = (
                CourseNormalizerService.normalize_course(
                    raw_course
                )
            )

            # Guardar
            result = CourseStorageService.save_course(
                normalized_course
            )

            # 3. Vincular con la habilidad, si corresponde
            if skill_id and result.get("course_id"):
                was_linked = CourseStorageService.link_course_skill(
                    course_id=result["course_id"],
                    skill_id=skill_id,
                )

                if was_linked:
                    linked_count += 1

            results.append(result)

        # 4. Contar qué ocurrió
        created = sum(
            1
            for result in results
            if result["status"] == "created"
        )

        already_exists = sum(
            1
            for result in results
            if result["status"] == "already_exists"
        )

        return {
            "query": search_query,
            "language": language,
            "skill_slug": skill_slug,
            "collected": len(raw_courses),
            "created": created,
            "already_exists": already_exists,
            "linked_to_skill": linked_count,
            "results": results,
        }