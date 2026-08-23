from datetime import UTC, datetime

from database.database import get_admin_client, get_db_client
from services.gemini_client import generate_quiz_for_module

PASSING_SCORE_RATIO = 0.8  # 8 de 10


class ModuleQuizService:

    @staticmethod
    def get_or_generate_quiz(module_id: str) -> list[dict]:
        try:
            supabase = get_admin_client()

            existing = (
                supabase.table("module_quiz_questions")
                .select("id, question, options")
                .eq("module_id", module_id)
                .execute()
            )

            if existing.data and len(existing.data) > 0:
                return existing.data

            module_result = (
                supabase.table("course_modules")
                .select("title, content_summary")
                .eq("id", module_id)
                .limit(1)
                .execute()
            )

            module_title = module_result.data[0]["title"] if module_result.data else f"Módulo {module_id}"
            content_summary = module_result.data[0]["content_summary"] if module_result.data else ""

            questions = generate_quiz_for_module(module_title, content_summary)

            rows_to_insert = [
                {
                    "module_id": module_id,
                    "question": q["question"],
                    "options": q["options"],
                    "correct_option": q.get("correct_option", 0),
                }
                for q in questions
            ]

            try:
                result = (
                    supabase.table("module_quiz_questions")
                    .insert(rows_to_insert)
                    .execute()
                )
                if result.data:
                    return [
                        {"id": row["id"], "question": row["question"], "options": row["options"]}
                        for row in result.data
                    ]
            except Exception as insert_err:
                print(f"⚠️ [QUIZ] Error al guardar preguntas en BD ({insert_err}), usando IDs virtuales.")
        except Exception as e:
            print(f"⚠️ [QUIZ] Error general en get_or_generate_quiz: {e}")
            questions = generate_quiz_for_module(f"Módulo {module_id}", "")

        # Retorna preguntas con IDs virtuales si no se guardaron en BD
        return [
            {"id": f"{module_id}-q{i}", "question": q["question"], "options": q["options"]}
            for i, q in enumerate(questions, start=1)
        ]

    @staticmethod
    def submit_module_attempt(
        user_id: str,
        module_id: str,
        answers: list[dict],
        token: str,
    ) -> dict:
        correct = 0
        total = len(answers) if answers else 10

        try:
            admin = get_admin_client()
            questions_result = (
                admin.table("module_quiz_questions")
                .select("id, correct_option")
                .eq("module_id", module_id)
                .execute()
            )
            questions = questions_result.data or []
            question_map = {q["id"]: q["correct_option"] for q in questions}

            if question_map:
                correct = sum(
                    1
                    for a in answers
                    if question_map.get(a["question_id"], 0) == a.get("selected_option")
                )
            else:
                # Opción 0 es la correcta por defecto
                correct = sum(1 for a in answers if a.get("selected_option") == 0)
        except Exception as e:
            print(f"⚠️ [QUIZ SUBMIT] Error consultando preguntas ({e}), evaluando localmente.")
            correct = sum(1 for a in answers if a.get("selected_option") == 0)

        score = round((correct / total) * 100, 2) if total > 0 else 0
        passed = correct >= round(total * PASSING_SCORE_RATIO)

        try:
            supabase = get_db_client(token) if token else get_admin_client()

            existing = (
                supabase.table("user_module_completion")
                .select("attempts, passed, best_score")
                .eq("user_id", user_id)
                .eq("module_id", module_id)
                .limit(1)
                .execute()
            )

            previous = existing.data[0] if existing.data else None
            was_passed_before = bool(previous and previous["passed"])
            attempts = (previous["attempts"] if previous else 0) + 1

            previous_best = (
                float(previous["best_score"])
                if previous and previous.get("best_score") is not None
                else 0.0
            )
            best_score = max(previous_best, score)

            row = {
                "user_id": user_id,
                "module_id": module_id,
                "score": score,
                "best_score": best_score,
                "passed": passed or was_passed_before,
                "completed_at": (
                    datetime.now(UTC).isoformat()
                    if (passed or was_passed_before)
                    else None
                ),
                "attempts": attempts,
            }

            if previous:
                supabase.table("user_module_completion").update(row).eq(
                    "user_id", user_id
                ).eq("module_id", module_id).execute()
            else:
                supabase.table("user_module_completion").insert(row).execute()
        except Exception as db_err:
            print(f"⚠️ [QUIZ SUBMIT] No se pudo guardar progreso en user_module_completion: {db_err}")

        return {
            "module_id": module_id,
            "score": score,
            "correct_answers": correct,
            "total_questions": total,
            "passed": passed,
        }