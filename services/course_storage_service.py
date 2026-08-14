from database.database import get_admin_client

# Columnas agregadas por docs/migrations/001_courses_free_metadata.sql. Hasta
# que la migración corra en Supabase, se descartan al insertar para no romper
# la ingesta. Cachea el resultado porque el esquema no cambia en caliente.
OPTIONAL_COLUMNS = ("institution", "is_free")

_missing_columns_cache: set[str] | None = None


def _get_missing_columns() -> set[str]:
    global _missing_columns_cache

    if _missing_columns_cache is not None:
        return _missing_columns_cache

    supabase = get_admin_client()
    missing = set()

    for column in OPTIONAL_COLUMNS:
        try:
            (
                supabase.table("courses")
                .select(column)
                .limit(1)
                .execute()
            )
        except Exception:
            missing.add(column)

    _missing_columns_cache = missing

    return missing


class CourseStorageService:

    @staticmethod
    def save_course(course: dict) -> dict:

        supabase = get_admin_client()

        missing = _get_missing_columns()

        if missing:
            course = {
                key: value
                for key, value in course.items()
                if key not in missing
            }

        course_url = course.get("url")

        # Revisar si el curso ya existe
        if course_url:
            existing = (
                supabase.table("courses")
                .select("id")
                .eq("url", course_url)
                .limit(1)
                .execute()
            )

            if existing.data:
                return {
                    "status": "already_exists",
                    "course_id": existing.data[0]["id"],
                    "title": course.get("title"),
                }

        # Si no existe, guardarlo
        result = (
            supabase.table("courses")
            .insert(course)
            .execute()
        )

        return {
            "status": "created",
            "course_id": result.data[0]["id"],
            "course": result.data[0],
        }

    @staticmethod
    def get_skill_id_by_slug(skill_slug: str) -> str | None:
        supabase = get_admin_client()

        response = (
            supabase
            .table("skills")
            .select("id")
            .eq("slug", skill_slug)
            .limit(1)
            .execute()
        )

        if response.data:
            return response.data[0]["id"]

        return None

    @staticmethod
    def link_course_skills(
        course_id: str,
        skill_ids: list[str],
    ) -> int:
        """
        Vincula un curso con varias habilidades y devuelve cuántos vínculos
        son nuevos.

        Un curso cubre más de una habilidad ('React y Node.js desde cero'),
        así que la unidad de trabajo es la lista, no el par suelto. Consulta
        los vínculos existentes una sola vez para no pagar una ida y vuelta
        por habilidad durante el backfill.
        """

        if not skill_ids:
            return 0

        supabase = get_admin_client()

        existing = (
            supabase
            .table("course_skills")
            .select("skill_id")
            .eq("course_id", course_id)
            .execute()
        )

        already_linked = {
            row["skill_id"]
            for row in (existing.data or [])
        }

        # `dict.fromkeys` descarta repetidos conservando el orden: el mismo
        # slug puede llegar dos veces desde el título y desde la query.
        new_ids = [
            skill_id
            for skill_id in dict.fromkeys(skill_ids)
            if skill_id not in already_linked
        ]

        if not new_ids:
            return 0

        supabase.table("course_skills").insert([
            {"course_id": course_id, "skill_id": skill_id}
            for skill_id in new_ids
        ]).execute()

        return len(new_ids)

    @staticmethod
    def get_courses_for_linking() -> list[dict]:
        """Cursos existentes con el texto que el matcher necesita."""

        supabase = get_admin_client()

        response = (
            supabase
            .table("courses")
            .select("id, title")
            .execute()
        )

        return response.data or []