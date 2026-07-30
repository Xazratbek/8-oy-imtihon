from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_course_access
from app.apps.auth.models import User
from app.apps.courses.models import Lesson
from app.apps.learning.models import Homework, PracticeAttempt, Question, QuestionOption, Quiz
from app.apps.learning.schemas import (
    AttemptOut,
    AttemptReview,
    AttemptSubmit,
    HomeworkCreate,
    HomeworkOut,
    OptionCreate,
    OptionOut,
    ProgressOut,
    QuestionCreate,
    QuestionOut,
    QuizCreate,
    QuizOut,
)
from app.apps.learning.service import LearningService
from app.db.session import get_db

router = APIRouter(tags=["Learning"])


def get_learning_service(db: AsyncSession = Depends(get_db)) -> LearningService:
    return LearningService(db)


@router.post("/quizzes", summary="Quiz yaratish")
async def create_quiz(payload: QuizCreate, user: User = Depends(get_current_user), service: LearningService = Depends(get_learning_service)) -> dict:
    return await service.create_quiz(payload, user.id)


@router.get("/lessons/{lesson_id}/quizzes", response_model=list[QuizOut], summary="Lesson quizlari")
async def list_lesson_quizzes(lesson_id: UUID, user: User = Depends(get_current_user), service: LearningService = Depends(get_learning_service)) -> list[Quiz]:
    return await service.list_lesson_quizzes(lesson_id, user.id)


@router.post("/questions", summary="Quiz question yaratish")
async def create_question(payload: QuestionCreate, user: User = Depends(get_current_user), service: LearningService = Depends(get_learning_service)) -> dict:
    return await service.create_question(payload, user.id)


@router.get("/quizzes/{quiz_id}/questions", response_model=list[QuestionOut], summary="Quiz questionlari")
async def list_quiz_questions(quiz_id: UUID, user: User = Depends(get_current_user), service: LearningService = Depends(get_learning_service)) -> list[Question]:
    return await service.list_quiz_questions(quiz_id, user.id)


@router.post("/question-options", summary="Question option yaratish")
async def create_option(payload: OptionCreate, user: User = Depends(get_current_user), service: LearningService = Depends(get_learning_service)) -> dict:
    return await service.create_option(payload, user.id)


@router.get("/questions/{question_id}/options", response_model=list[OptionOut], summary="Question optionlari")
async def list_question_options(question_id: UUID, user: User = Depends(get_current_user), service: LearningService = Depends(get_learning_service)) -> list[QuestionOption]:
    return await service.list_question_options(question_id, user.id)


@router.post("/homeworks", summary="Homework yaratish")
async def create_homework(payload: HomeworkCreate, user: User = Depends(get_current_user), service: LearningService = Depends(get_learning_service)) -> dict:
    return await service.create_homework(payload, user.id)


@router.get("/lessons/{lesson_id}/homeworks", response_model=list[HomeworkOut], summary="Lesson homeworklari")
async def list_lesson_homeworks(lesson_id: UUID, user: User = Depends(get_current_user), service: LearningService = Depends(get_learning_service)) -> list[Homework]:
    return await service.list_lesson_homeworks(lesson_id, user.id)


@router.post("/attempts", response_model=AttemptOut, summary="Quiz/homework attempt submit")
async def submit_attempt(
    payload: AttemptSubmit,
    user: User = Depends(get_current_user),
    service: LearningService = Depends(get_learning_service),
) -> PracticeAttempt:
    return await service.submit_attempt(payload, user.id)


@router.get("/lessons/{lesson_id}/attempts", response_model=list[AttemptOut], summary="Lesson attemptlari")
async def list_lesson_attempts(lesson_id: UUID, user: User = Depends(get_current_user), service: LearningService = Depends(get_learning_service)) -> list[PracticeAttempt]:
    return await service.list_lesson_attempts(lesson_id, user.id)


@router.patch("/attempts/{attempt_id}/review", response_model=AttemptOut, summary="Attempt review")
async def review_attempt(
    attempt_id: UUID,
    payload: AttemptReview,
    user: User = Depends(get_current_user),
    service: LearningService = Depends(get_learning_service),
) -> PracticeAttempt:
    return await service.review_attempt(attempt_id, payload, user.id)


@router.post("/lessons/{lesson_id}/complete", summary="Lesson complete")
async def complete_lesson(
    lesson: Lesson = Depends(require_course_access),
    user: User = Depends(get_current_user),
    service: LearningService = Depends(get_learning_service),
) -> dict:
    return await service.complete_lesson(lesson, user.id)


@router.get("/me/courses/{course_id}/progress", response_model=ProgressOut, summary="Course progress")
async def course_progress(course_id: UUID, user: User = Depends(get_current_user), service: LearningService = Depends(get_learning_service)) -> ProgressOut:
    return await service.course_progress(course_id, user.id)


@router.get("/me/certificates", summary="Mening certificate eligibility")
async def my_certificates(user: User = Depends(get_current_user), service: LearningService = Depends(get_learning_service)) -> list[dict]:
    return await service.my_certificates(user.id)


@router.get("/learn/lessons/{lesson_id}/player", summary="Lesson video player config")
async def lesson_player(lesson: Lesson = Depends(require_course_access), service: LearningService = Depends(get_learning_service)) -> dict:
    return await service.lesson_player(lesson)
