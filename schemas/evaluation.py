from pydantic import BaseModel, Field


class EvaluationQuestionResponse(BaseModel):
    id: int
    skill_slug: str
    question: str
    options: list[str]


class EvaluationAnswer(BaseModel):
    question_id: int
    selected_option: int = Field(ge=0)


class EvaluationSubmitRequest(BaseModel):
    answers: list[EvaluationAnswer] = Field(min_length=1)


class EvaluationResultResponse(BaseModel):
    skill_slug: str
    score: float
    correct_answers: int
    total_questions: int
    passed: bool
    module_status: str
    best_score: float
    completed_modules: int
    total_modules: int
    roadmap_progress_percentage: float