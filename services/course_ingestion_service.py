from services.catalog_service import CatalogService
from services.course_collector_service import (
    CourseCollectorService,
)
from services.course_normalizer_service import (
    CourseNormalizerService,
)
from services.course_storage_service import (
    CourseStorageService,
)
from services.skill_matcher import match_skills


class CourseIngestionService:

    @staticmethod
    def resolve_course_skills(
        title: str | None,
        skills_catalog: list[dict],
        fallback_skill_id: str | None = None,
    ) -> tuple[list[str], bool]:
        """
        Decide con qué habilidades se vincula un curso.

        El criterio principal es el contenido: las habilidades que el título
        menciona por nombre o alias. Vincular por la query de búsqueda dejaba
        'Introduction to R' colgando de `python` solo porque esa fue la
        búsqueda, y el motor de recomendaciones filtra estricto por
        `skill_slugs`, así que ese error llega hasta el usuario.

        La query queda como respaldo para los títulos que no mencionan
        ninguna habilidad del catálogo ('CS50', 'Bootcamp Full Stack'): en una
        ingesta dirigida es preferible un vínculo aproximado a un curso
        huérfano, invisible para el recomendador.

        Devuelve los ids a vincular y si se usó el respaldo.
        """

        matched = match_skills(title or "", skills_catalog)

        if matched:
            return [skill["id"] for skill in matched], False

        if fallback_skill_id:
            return [fallback_skill_id], True

        return [], False

    @staticmethod
    def ingest_courses(
        search_query: str,
        max_items: int = 10,
        language: str = "spanish",
        skill_slug: str | None = None,
        free_only: bool = True,
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

        # El catálogo de habilidades se lee una vez por corrida: no cambia
        # mientras se procesan los cursos.
        skills_catalog = CatalogService.get_all_skills()

        # 1. Recolectar cursos desde Apify
        raw_courses = CourseCollectorService.collect_courses(
            search_query=search_query,
            max_items=max_items,
            language=language,
            free_only=free_only,
        )

        results = []
        linked_count = 0
        fallback_count = 0

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

            # 3. Vincular con las habilidades que el título menciona
            if result.get("course_id"):
                skill_ids, used_fallback = (
                    CourseIngestionService.resolve_course_skills(
                        title=normalized_course.get("title"),
                        skills_catalog=skills_catalog,
                        fallback_skill_id=skill_id,
                    )
                )

                new_links = CourseStorageService.link_course_skills(
                    course_id=result["course_id"],
                    skill_ids=skill_ids,
                )

                linked_count += new_links
                result["skills_linked"] = len(skill_ids)

                if used_fallback:
                    fallback_count += 1

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
            "free_only": free_only,
            "skill_slug": skill_slug,
            "collected": len(raw_courses),
            "created": created,
            "already_exists": already_exists,
            "linked_to_skill": linked_count,
            "linked_by_fallback": fallback_count,
            "results": results,
        }
