from services.module_quiz_service import ModuleQuizService


def test_submit_module_attempt_aprueba_con_80_por_ciento(monkeypatch):
    class FakeQuery:
        def __init__(self, data=None):
            self.data = data or []

        def select(self, *args):
            return self

        def eq(self, *args):
            return self

        def limit(self, *args):
            return self

        def execute(self):
            return self

        def insert(self, row):
            self.inserted = row
            return self

        def update(self, row):
            self.updated = row
            return self

    class FakeSupabase:
        def table(self, name):
            query = FakeQuery()

            if name == "module_quiz_questions":
                query.data = [
                    {"id": 1, "correct_option": 0},
                    {"id": 2, "correct_option": 1},
                    {"id": 3, "correct_option": 2},
                    {"id": 4, "correct_option": 0},
                    {"id": 5, "correct_option": 1},
                    {"id": 6, "correct_option": 2},
                    {"id": 7, "correct_option": 0},
                    {"id": 8, "correct_option": 1},
                    {"id": 9, "correct_option": 2},
                    {"id": 10, "correct_option": 0},
                ]

            return query

    monkeypatch.setattr(
        "services.module_quiz_service.get_admin_client",
        lambda: FakeSupabase(),
    )

    answers = [
        {"question_id": 1, "selected_option": 0},
        {"question_id": 2, "selected_option": 1},
        {"question_id": 3, "selected_option": 2},
        {"question_id": 4, "selected_option": 0},
        {"question_id": 5, "selected_option": 1},
        {"question_id": 6, "selected_option": 2},
        {"question_id": 7, "selected_option": 0},
        {"question_id": 8, "selected_option": 1},
        {"question_id": 9, "selected_option": 0},
        {"question_id": 10, "selected_option": 1},
    ]

    result = ModuleQuizService.submit_module_attempt(
        user_id="test-user",
        module_id="test-module",
        answers=answers,
        token="",
    )

    assert result["score"] == 80.0
    assert result["correct_answers"] == 8
    assert result["total_questions"] == 10
    assert result["passed"] is True


def test_submit_module_attempt_rechaza_con_menos_de_80_por_ciento(monkeypatch):
    class FakeQuery:
        def select(self, *args):
            return self

        def eq(self, *args):
            return self

        def execute(self):
            return self

    class FakeSupabase:
        def table(self, name):
            query = FakeQuery()

            if name == "module_quiz_questions":
                query.data = [
                    {"id": 1, "correct_option": 0},
                    {"id": 2, "correct_option": 1},
                    {"id": 3, "correct_option": 2},
                    {"id": 4, "correct_option": 0},
                    {"id": 5, "correct_option": 1},
                    {"id": 6, "correct_option": 2},
                    {"id": 7, "correct_option": 0},
                    {"id": 8, "correct_option": 1},
                    {"id": 9, "correct_option": 2},
                    {"id": 10, "correct_option": 0},
                ]

            return query

    monkeypatch.setattr(
        "services.module_quiz_service.get_admin_client",
        lambda: FakeSupabase(),
    )

    answers = [
        {"question_id": i, "selected_option": 0}
        for i in range(1, 11)
    ]

    result = ModuleQuizService.submit_module_attempt(
        user_id="test-user",
        module_id="test-module",
        answers=answers,
        token="",
    )

    assert result["score"] == 40.0
    assert result["correct_answers"] == 4
    assert result["total_questions"] == 10
    assert result["passed"] is False