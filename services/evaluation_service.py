from datetime import UTC, datetime

from database.database import get_admin_client, get_db_client

PASSING_SCORE = 70.0


class EvaluationService:

    @staticmethod
    def get_questions(skill_slug: str) -> list[dict]:
        supabase = get_admin_client()

        result = (
            supabase.table("evaluation_questions")
            .select("id, skill_slug, question, options")
            .eq("skill_slug", skill_slug)
            .order("id")
            .execute()
        )

        return result.data or []

    @staticmethod
    def submit_evaluation(
        user_id: str,
        skill_slug: str,
        answers: list[dict],
        token: str,
    ) -> dict:
        admin = get_admin_client()

        questions_result = (
            admin.table("evaluation_questions")
            .select("id, correct_option")
            .eq("skill_slug", skill_slug)
            .execute()
        )

        questions = questions_result.data or []

        if not questions:
            raise LookupError(
                "No existe una evaluación para este módulo."
            )

        question_map = {
            int(question["id"]): int(question["correct_option"])
            for question in questions
        }

        answer_ids = [
            answer["question_id"]
            for answer in answers
        ]

        if (
            len(set(answer_ids)) != len(answer_ids)
            or set(answer_ids) != set(question_map.keys())
        ):
            raise ValueError(
                "Debes responder exactamente todas las preguntas "
                "de la evaluación."
            )

        correct_answers = sum(
            1
            for answer in answers
            if question_map[answer["question_id"]]
            == answer["selected_option"]
        )

        total_questions = len(questions)

        score = round(
            (correct_answers / total_questions) * 100,
            2,
        )

        passed = score >= PASSING_SCORE

        supabase = get_db_client(token)

        (
            supabase.table("evaluation_attempts")
            .insert(
                {
                    "user_id": user_id,
                    "skill_slug": skill_slug,
                    "score": score,
                    "correct_answers": correct_answers,
                    "total_questions": total_questions,
                    "passed": passed,
                }
            )
            .execute()
        )

        existing = (
            supabase.table("user_module_progress")
            .select("status, best_score, completed_at")
            .eq("user_id", user_id)
            .eq("skill_slug", skill_slug)
            .limit(1)
            .execute()
        )

        previous = existing.data[0] if existing.data else None

        previous_best = (
            float(previous["best_score"])
            if previous and previous["best_score"] is not None
            else 0.0
        )

        best_score = max(previous_best, score)

        was_completed = (
            previous is not None
            and previous["status"] == "completed"
        )

        module_status = (
            "completed"
            if passed or was_completed
            else "in_progress"
        )

        completed_at = (
            previous["completed_at"]
            if was_completed
            else (
                datetime.now(UTC).isoformat()
                if passed
                else None
            )
        )

        progress_data = {
            "user_id": user_id,
            "skill_slug": skill_slug,
            "status": module_status,
            "best_score": best_score,
            "completed_at": completed_at,
            "updated_at": datetime.now(UTC).isoformat(),
        }

        if previous:
            (
                supabase.table("user_module_progress")
                .update(progress_data)
                .eq("user_id", user_id)
                .eq("skill_slug", skill_slug)
                .execute()
            )
        else:
            (
                supabase.table("user_module_progress")
                .insert(progress_data)
                .execute()
            )

        return {
            "skill_slug": skill_slug,
            "score": score,
            "correct_answers": correct_answers,
            "total_questions": total_questions,
            "passed": passed,
            "module_status": module_status,
            "best_score": best_score,
        }

    @staticmethod
    def calculate_roadmap_progress(
        user_id: str,
        roadmap_skills: list[str],
        token: str,
    ) -> dict:
        unique_skills = set(roadmap_skills)

        if not unique_skills:
            return {
                "completed_modules": 0,
                "total_modules": 0,
                "roadmap_progress_percentage": 0.0,
            }

        supabase = get_db_client(token)

        result = (
            supabase.table("user_module_progress")
            .select("skill_slug, status")
            .eq("user_id", user_id)
            .eq("status", "completed")
            .execute()
        )

        completed = {
            row["skill_slug"]
            for row in (result.data or [])
            if row["skill_slug"] in unique_skills
        }

        total = len(unique_skills)
        completed_count = len(completed)

        return {
            "completed_modules": completed_count,
            "total_modules": total,
            "roadmap_progress_percentage": round(
                completed_count / total * 100,
                2,
            ),
        }