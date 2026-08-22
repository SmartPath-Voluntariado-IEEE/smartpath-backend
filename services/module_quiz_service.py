from datetime import UTC, datetime

from database.database import get_admin_client, get_db_client
from services.gemini_client import generate_quiz_for_module

PASSING_SCORE_RATIO = 0.8  # 8 de 10


class ModuleQuizService:

    @staticmethod
    def get_or_generate_quiz(module_id: str) -> list[dict]:
        supabase = get_admin_client()

        existing = (
            supabase.table("module_quiz_questions")
            .select("id, question, options")
            .eq("module_id", module_id)
            .execute()
        )

        if existing.data:
            return existing.data

        module_result = (
            supabase.table("course_modules")
            .select("title, content_summary")
            .eq("id", module_id)
            .limit(1)
            .execute()
        )

        if not module_result.data:
            raise LookupError(f"No existe el módulo con id {module_id}.")

        module = module_result.data[0]

        questions = generate_quiz_for_module(
            module["title"], module["content_summary"] or ""
        )

        rows_to_insert = [
            {
                "module_id": module_id,
                "question": q["question"],
                "options": q["options"],
                "correct_option": q["correct_option"],
            }
            for q in questions
        ]

        result = (
            supabase.table("module_quiz_questions")
            .insert(rows_to_insert)
            .execute()
        )

        # No devolvemos correct_option al frontend
        return [
            {"id": row["id"], "question": row["question"], "options": row["options"]}
            for row in result.data
        ]

    @staticmethod
    def submit_module_attempt(
        user_id: str,
        module_id: str,
        answers: list[dict],
        token: str,
    ) -> dict:
        admin = get_admin_client()

        questions_result = (
            admin.table("module_quiz_questions")
            .select("id, correct_option")
            .eq("module_id", module_id)
            .execute()
        )

        questions = questions_result.data or []

        if not questions:
            raise LookupError("Este módulo no tiene un examen generado todavía.")

        question_map = {q["id"]: q["correct_option"] for q in questions}
        answer_ids = [a["question_id"] for a in answers]

        if (
            len(set(answer_ids)) != len(answer_ids)
            or set(answer_ids) != set(question_map.keys())
        ):
            raise ValueError(
                "Debes responder exactamente las 10 preguntas del examen."
            )

        correct = sum(
            1
            for a in answers
            if question_map[a["question_id"]] == a["selected_option"]
        )

        total = len(questions)
        score = round((correct / total) * 100, 2)
        passed = correct >= round(total * PASSING_SCORE_RATIO)

        supabase = get_db_client(token)

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

        return {
            "module_id": module_id,
            "score": score,
            "correct_answers": correct,
            "total_questions": total,
            "passed": passed or was_passed_before,
        }