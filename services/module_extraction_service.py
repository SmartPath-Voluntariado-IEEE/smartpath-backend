from database.database import get_admin_client, get_db_client
from services.gemini_client import extract_modules_from_content
from services.web_scraper_service import WebScraperService


class ModuleExtractionService:

    @staticmethod
    def get_or_extract_modules(
        course_id: int,
        user_id: str | None = None,
        token: str | None = None,
    ) -> list[dict]:
        supabase = get_admin_client()

        existing = (
            supabase.table("course_modules")
            .select("*")
            .eq("course_id", course_id)
            .order("module_order")
            .execute()
        )

        if existing.data:
            modules = existing.data
        else:
            course_result = (
                supabase.table("courses")
                .select("title, url")
                .eq("id", course_id)
                .limit(1)
                .execute()
            )

            course = course_result.data[0] if course_result.data else {"title": f"Curso #{course_id}", "url": "#"}

            scraped_text = WebScraperService.scrape_course_page(course.get("url", "#"))
            extracted = extract_modules_from_content(course["title"], scraped_text)

            rows_to_insert = [
                {
                    "course_id": course_id,
                    "module_order": module["order"],
                    "title": module["title"],
                    "content_summary": module["content_summary"],
                }
                for module in extracted
            ]

            try:
                result = (
                    supabase.table("course_modules")
                    .insert(rows_to_insert)
                    .execute()
                )
                modules = result.data or []
            except Exception as insert_err:
                print(f"⚠️ [MODULES] Error insertando en course_modules ({insert_err}), usando IDs virtuales.")
                modules = [
                    {
                        "id": f"c{course_id}-m{m['order']}",
                        "course_id": course_id,
                        "module_order": m["order"],
                        "title": m["title"],
                        "content_summary": m["content_summary"],
                    }
                    for m in extracted
                ]

        if user_id:
            modules = ModuleExtractionService._attach_progress(
                modules, user_id, token
            )

        return modules

    @staticmethod
    def _attach_progress(
        modules: list[dict], user_id: str, token: str | None
    ) -> list[dict]:
        """
        Agrega score/passed/attempts de cada módulo para este usuario,
        consultando user_module_completion.
        """
        try:
            supabase = get_db_client(token) if token else get_admin_client()
            module_ids = [m["id"] for m in modules]

            completion_result = (
                supabase.table("user_module_completion")
                .select("module_id, score, passed, attempts, best_score")
                .eq("user_id", user_id)
                .in_("module_id", module_ids)
                .execute()
            )

            completion_map = {
                row["module_id"]: row for row in (completion_result.data or [])
            }

            for module in modules:
                record = completion_map.get(module["id"])
                module["score"] = record["score"] if record else None
                module["best_score"] = record["best_score"] if record else None
                module["passed"] = bool(record["passed"]) if record else False
                module["attempts"] = record["attempts"] if record else 0
        except Exception as e:
            print(f"⚠️ [ATTACH PROGRESS] Error al leer progreso de usuario: {e}")
            for module in modules:
                module["score"] = None
                module["best_score"] = None
                module["passed"] = False
                module["attempts"] = 0

        return modules