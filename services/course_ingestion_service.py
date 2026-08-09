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
    ) -> dict:

        # 1. Recolectar cursos desde Apify
        raw_courses = CourseCollectorService.collect_courses(
            search_query=search_query,
            max_items=max_items,
        )

        results = []

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

            results.append(result)

        # 3. Contar qué ocurrió
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
            "collected": len(raw_courses),
            "created": created,
            "already_exists": already_exists,
            "results": results,
        }