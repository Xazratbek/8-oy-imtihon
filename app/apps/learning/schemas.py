from uuid import UUID

from pydantic import BaseModel, Field

from app.common.schemas import ORMModel


class QuizCreate(BaseModel):
    lesson_id: UUID
    title: str
    passing_score: int = 60


class QuizOut(ORMModel):
    id: UUID
    lesson_id: UUID
    title: str
    passing_score: int


class QuestionCreate(BaseModel):
    quiz_id: UUID
    question_type: str = "single_choice"
    text: str
    correct_answer: str | None = None
    score: int = 1
    sort_order: int = 0


class QuestionOut(ORMModel):
    id: UUID
    quiz_id: UUID
    question_type: str
    text: str
    correct_answer: str | None
    score: int
    sort_order: int


class OptionCreate(BaseModel):
    question_id: UUID
    text: str
    is_correct: bool = False
    sort_order: int = 0


class OptionOut(ORMModel):
    id: UUID
    question_id: UUID
    text: str
    is_correct: bool
    sort_order: int


class HomeworkCreate(BaseModel):
    lesson_id: UUID
    title: str
    description: str = ""
    max_attempts: int = 1
    max_score: int = 100
    review_required: bool = True


class HomeworkOut(ORMModel):
    id: UUID
    lesson_id: UUID
    title: str
    description: str
    max_attempts: int
    max_score: int
    review_required: bool


class AttemptSubmit(BaseModel):
    lesson_id: UUID
    quiz_id: UUID | None = None
    homework_id: UUID | None = None
    answer_text: str = ""
    file_url: str | None = None
    answers: dict = Field(default_factory=dict)


class AttemptReview(BaseModel):
    score: int
    status: str = "graded"
    comment: str = ""


class AttemptOut(ORMModel):
    id: UUID
    user_id: UUID
    lesson_id: UUID
    quiz_id: UUID | None
    homework_id: UUID | None
    status: str
    score: int
    answer_text: str
    file_url: str | None
    review_comment: str


class ProgressOut(BaseModel):
    course_id: UUID
    completed_lessons: int
    total_lessons: int
    percent: float
