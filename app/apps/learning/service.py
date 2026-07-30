from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.learning.models import Certificate, Homework, LessonProgress, PracticeAttempt, Question, QuestionOption, Quiz
from app.apps.learning.repository import LearningRepository
from app.apps.learning.schemas import AttemptReview, AttemptSubmit, HomeworkCreate, OptionCreate, ProgressOut, QuestionCreate, QuizCreate
from app.common.exceptions import ConflictError, ForbiddenError, NotFoundError


class LearningService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = LearningRepository(db)

    async def assert_lesson_staff(self, lesson_id: UUID, user_id: UUID):
        lesson = await self.repo.get_lesson(lesson_id)
        if not lesson:
            raise NotFoundError("Lesson topilmadi")
        course = await self.repo.get_course(lesson.course_id)
        if not course or not await self.repo.get_staff_member(course.school_id, user_id):
            raise ForbiddenError("Staff access kerak")
        return lesson

    async def require_course_access(self, lesson_id: UUID, user_id: UUID):
        lesson = await self.repo.get_lesson(lesson_id)
        if not lesson:
            raise NotFoundError("Lesson topilmadi")
        if lesson.is_preview:
            return lesson
        if not await self.repo.get_enrollment(lesson.course_id, user_id):
            raise ForbiddenError("Kursga yozilmagansiz")
        return lesson

    async def create_quiz(self, payload: QuizCreate, user_id: UUID) -> dict:
        await self.assert_lesson_staff(payload.lesson_id, user_id)
        quiz = self.repo.add(Quiz(**payload.model_dump()))
        await self.db.commit()
        await self.db.refresh(quiz)
        return {"id": quiz.id, "title": quiz.title}

    async def list_lesson_quizzes(self, lesson_id: UUID, user_id: UUID):
        await self.assert_lesson_staff(lesson_id, user_id)
        return await self.repo.list_lesson_quizzes(lesson_id)

    async def create_question(self, payload: QuestionCreate, user_id: UUID) -> dict:
        quiz = await self.repo.get_quiz(payload.quiz_id)
        if not quiz:
            raise NotFoundError("Quiz topilmadi")
        await self.assert_lesson_staff(quiz.lesson_id, user_id)
        question = self.repo.add(Question(**payload.model_dump()))
        await self.db.commit()
        await self.db.refresh(question)
        return {"id": question.id, "text": question.text}

    async def list_quiz_questions(self, quiz_id: UUID, user_id: UUID):
        quiz = await self.repo.get_quiz(quiz_id)
        if not quiz:
            raise NotFoundError("Quiz topilmadi")
        await self.assert_lesson_staff(quiz.lesson_id, user_id)
        return await self.repo.list_quiz_questions(quiz_id)

    async def create_option(self, payload: OptionCreate, user_id: UUID) -> dict:
        question = await self.repo.get_question(payload.question_id)
        if not question:
            raise NotFoundError("Question topilmadi")
        quiz = await self.repo.get_quiz(question.quiz_id)
        await self.assert_lesson_staff(quiz.lesson_id, user_id)
        option = self.repo.add(QuestionOption(**payload.model_dump()))
        await self.db.commit()
        await self.db.refresh(option)
        return {"id": option.id, "text": option.text}

    async def list_question_options(self, question_id: UUID, user_id: UUID):
        question = await self.repo.get_question(question_id)
        if not question:
            raise NotFoundError("Question topilmadi")
        quiz = await self.repo.get_quiz(question.quiz_id)
        await self.assert_lesson_staff(quiz.lesson_id, user_id)
        return await self.repo.list_question_options(question_id)

    async def create_homework(self, payload: HomeworkCreate, user_id: UUID) -> dict:
        await self.assert_lesson_staff(payload.lesson_id, user_id)
        homework = self.repo.add(Homework(**payload.model_dump()))
        await self.db.commit()
        await self.db.refresh(homework)
        return {"id": homework.id, "title": homework.title}

    async def list_lesson_homeworks(self, lesson_id: UUID, user_id: UUID):
        await self.assert_lesson_staff(lesson_id, user_id)
        return await self.repo.list_lesson_homeworks(lesson_id)

    async def score_quiz(self, quiz_id: UUID, answers: dict) -> int:
        total = 0
        for question in await self.repo.list_quiz_questions(quiz_id):
            answer = str(answers.get(str(question.id), ""))
            if question.question_type in ("single_choice", "multiple_choice") and question.correct_answer and answer == question.correct_answer:
                total += question.score
        return total

    async def submit_attempt(self, payload: AttemptSubmit, user_id: UUID) -> PracticeAttempt:
        await self.require_course_access(payload.lesson_id, user_id)
        if payload.homework_id:
            homework = await self.repo.get_homework(payload.homework_id)
            if not homework:
                raise NotFoundError("Homework topilmadi")
            if await self.repo.count_attempts_for_homework(payload.homework_id, user_id) >= homework.max_attempts:
                raise ConflictError("Max attempts tugagan")
        attempt = self.repo.add(
            PracticeAttempt(
                user_id=user_id,
                lesson_id=payload.lesson_id,
                quiz_id=payload.quiz_id,
                homework_id=payload.homework_id,
                status="waiting_review" if payload.homework_id else "graded",
                answer_text=payload.answer_text,
                file_url=payload.file_url,
                answers=payload.answers,
                score=await self.score_quiz(payload.quiz_id, payload.answers) if payload.quiz_id else 0,
                submitted_at=datetime.now(UTC),
            )
        )
        await self.db.commit()
        await self.db.refresh(attempt)
        return attempt

    async def list_lesson_attempts(self, lesson_id: UUID, user_id: UUID):
        await self.assert_lesson_staff(lesson_id, user_id)
        return await self.repo.list_lesson_attempts(lesson_id)

    async def review_attempt(self, attempt_id: UUID, payload: AttemptReview, user_id: UUID) -> PracticeAttempt:
        attempt = await self.repo.get_attempt(attempt_id)
        if not attempt:
            raise NotFoundError("Attempt topilmadi")
        await self.assert_lesson_staff(attempt.lesson_id, user_id)
        attempt.score = payload.score
        attempt.status = payload.status
        attempt.review_comment = payload.comment
        attempt.reviewer_id = user_id
        attempt.graded_at = datetime.now(UTC)
        await self.db.commit()
        await self.db.refresh(attempt)
        return attempt

    async def complete_lesson(self, lesson, user_id: UUID) -> dict:
        progress = await self.repo.get_lesson_progress(lesson.id, user_id)
        if not progress:
            self.repo.add(LessonProgress(lesson_id=lesson.id, course_id=lesson.course_id, user_id=user_id, completed_at=datetime.now(UTC)))
        await self.db.commit()
        return {"success": True, "code": "OK", "payload": {"lesson_id": str(lesson.id), "completed": True}}

    async def course_progress(self, course_id: UUID, user_id: UUID) -> ProgressOut:
        total = await self.repo.count_published_lessons(course_id)
        done = await self.repo.count_completed_lessons(course_id, user_id)
        percent = round((done / total) * 100, 2) if total else 0
        if total and done >= total and not await self.repo.get_certificate(course_id, user_id):
            self.repo.add(Certificate(course_id=course_id, user_id=user_id, status="eligible"))
            await self.db.commit()
        return ProgressOut(course_id=course_id, completed_lessons=done, total_lessons=total, percent=percent)

    async def my_certificates(self, user_id: UUID) -> list[dict]:
        return [{"id": row.id, "course_id": row.course_id, "status": row.status, "issued_at": row.issued_at} for row in await self.repo.list_certificates(user_id)]

    async def lesson_player(self, lesson) -> dict:
        block = await self.repo.first_video_block(lesson.id)
        if not block or not block.video_asset_id:
            raise NotFoundError("Video block topilmadi")
        asset = await self.repo.get_video_asset(block.video_asset_id)
        if not asset:
            raise NotFoundError("Video asset topilmadi")
        return {
            "lesson_id": lesson.id,
            "video_asset_id": asset.id,
            "provider": asset.provider,
            "status": asset.status,
            "player_url": asset.player_url,
            "embed_url": asset.embed_url,
        }
