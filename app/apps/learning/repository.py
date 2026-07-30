from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.apps.courses.models import Course, Lesson, LessonBlock
from app.apps.learning.models import Certificate, Enrollment, Homework, LessonProgress, PracticeAttempt, Question, QuestionOption, Quiz
from app.apps.media.models import VideoAsset
from app.apps.schools.models import SchoolMember


class LearningRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_lesson(self, lesson_id: UUID) -> Lesson | None:
        return await self.db.get(Lesson, lesson_id)

    async def get_course(self, course_id: UUID) -> Course | None:
        return await self.db.get(Course, course_id)

    async def get_quiz(self, quiz_id: UUID) -> Quiz | None:
        return await self.db.get(Quiz, quiz_id)

    async def get_question(self, question_id: UUID) -> Question | None:
        return await self.db.get(Question, question_id)

    async def get_homework(self, homework_id: UUID) -> Homework | None:
        return await self.db.get(Homework, homework_id)

    async def get_attempt(self, attempt_id: UUID) -> PracticeAttempt | None:
        return await self.db.get(PracticeAttempt, attempt_id)

    async def get_video_asset(self, video_id: UUID) -> VideoAsset | None:
        return await self.db.get(VideoAsset, video_id)

    async def get_staff_member(self, school_id: UUID, user_id: UUID) -> SchoolMember | None:
        result = await self.db.execute(
            select(SchoolMember).where(
                SchoolMember.school_id == school_id,
                SchoolMember.user_id == user_id,
                SchoolMember.role.in_(("owner", "admin", "instructor", "curator")),
                SchoolMember.is_active.is_(True),
            )
        )
        return result.scalar_one_or_none()

    async def get_enrollment(self, course_id: UUID, user_id: UUID) -> Enrollment | None:
        result = await self.db.execute(select(Enrollment).where(Enrollment.course_id == course_id, Enrollment.user_id == user_id, Enrollment.status == "active"))
        return result.scalar_one_or_none()

    async def list_lesson_quizzes(self, lesson_id: UUID) -> list[Quiz]:
        result = await self.db.execute(select(Quiz).where(Quiz.lesson_id == lesson_id).order_by(Quiz.created_at))
        return list(result.scalars())

    async def list_quiz_questions(self, quiz_id: UUID) -> list[Question]:
        result = await self.db.execute(select(Question).where(Question.quiz_id == quiz_id).order_by(Question.sort_order, Question.created_at))
        return list(result.scalars())

    async def list_question_options(self, question_id: UUID) -> list[QuestionOption]:
        result = await self.db.execute(
            select(QuestionOption).where(QuestionOption.question_id == question_id).order_by(QuestionOption.sort_order, QuestionOption.created_at)
        )
        return list(result.scalars())

    async def list_lesson_homeworks(self, lesson_id: UUID) -> list[Homework]:
        result = await self.db.execute(select(Homework).where(Homework.lesson_id == lesson_id).order_by(Homework.created_at))
        return list(result.scalars())

    async def count_attempts_for_homework(self, homework_id: UUID, user_id: UUID) -> int:
        return await self.db.scalar(
            select(func.count(PracticeAttempt.id)).where(PracticeAttempt.homework_id == homework_id, PracticeAttempt.user_id == user_id)
        ) or 0

    async def list_lesson_attempts(self, lesson_id: UUID) -> list[PracticeAttempt]:
        result = await self.db.execute(select(PracticeAttempt).where(PracticeAttempt.lesson_id == lesson_id).order_by(PracticeAttempt.submitted_at.desc()))
        return list(result.scalars())

    async def get_lesson_progress(self, lesson_id: UUID, user_id: UUID) -> LessonProgress | None:
        result = await self.db.execute(select(LessonProgress).where(LessonProgress.lesson_id == lesson_id, LessonProgress.user_id == user_id))
        return result.scalar_one_or_none()

    async def count_published_lessons(self, course_id: UUID) -> int:
        return await self.db.scalar(select(func.count(Lesson.id)).where(Lesson.course_id == course_id, Lesson.status == "published")) or 0

    async def count_completed_lessons(self, course_id: UUID, user_id: UUID) -> int:
        return await self.db.scalar(select(func.count(LessonProgress.id)).where(LessonProgress.course_id == course_id, LessonProgress.user_id == user_id)) or 0

    async def get_certificate(self, course_id: UUID, user_id: UUID) -> Certificate | None:
        result = await self.db.execute(select(Certificate).where(Certificate.course_id == course_id, Certificate.user_id == user_id))
        return result.scalar_one_or_none()

    async def list_certificates(self, user_id: UUID) -> list[Certificate]:
        result = await self.db.execute(select(Certificate).where(Certificate.user_id == user_id))
        return list(result.scalars())

    async def first_video_block(self, lesson_id: UUID) -> LessonBlock | None:
        result = await self.db.execute(
            select(LessonBlock).where(LessonBlock.lesson_id == lesson_id, LessonBlock.block_type == "video").order_by(LessonBlock.sort_order)
        )
        return result.scalar_one_or_none()

    def add(self, entity):
        self.db.add(entity)
        return entity
