from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from app.core.exceptions import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
)
from app.models.research_members import MemberRole, ResearchMember
from app.models.research_task import ResearchTask, TaskPriority, TaskStatus
from app.schemas.research_task import ResearchTaskCreate, ResearchTaskUpdate
from app.services.research_project import ResearchProjectService


class ResearchTaskService:
    @staticmethod
    def _validate_assignee(
        db: Session, project_id: int, assignee_id: int | None
    ) -> None:
        """Gom lỗi kiểm tra Assignee: nếu không phải member trong đề tài thì ném BadRequestException."""
        if assignee_id is not None:
            assignee_member = (
                db.query(ResearchMember)
                .filter(
                    ResearchMember.project_id == project_id,
                    ResearchMember.user_id == assignee_id,
                )
                .first()
            )
            if not assignee_member:
                raise BadRequestException(
                    "Người được giao việc phải là thành viên của đề tài nghiên cứu"
                )

    @staticmethod
    def _get_task(db: Session, task_id: int) -> ResearchTask:
        """Gom lỗi tìm Task: nếu không tồn tại thì ném NotFoundException."""
        task = db.query(ResearchTask).filter(ResearchTask.id == task_id).first()
        if not task:
            raise NotFoundException("Không tìm thấy nhiệm vụ nghiên cứu")
        return task

    @staticmethod
    def create_task(
        db: Session, project_id: int, task_in: ResearchTaskCreate, user_id: int
    ) -> ResearchTask:
        ResearchProjectService._check_permission(db, project_id, user_id)
        ResearchTaskService._validate_assignee(db, project_id, task_in.assignee_id)

        task = ResearchTask(
            project_id=project_id,
            title=task_in.title,
            description=task_in.description,
            assignee_id=task_in.assignee_id,
            status=task_in.status,
            priority=task_in.priority,
            due_date=task_in.due_date,
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def get_project_tasks(
        db: Session,
        project_id: int,
        user_id: int,
        search: str | None = None,
        task_status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        assignee_id: int | None = None,
        sort_by: str = "created_at",
        order: str = "desc",
        page: int = 1,
        size: int = 10,
    ) -> list[ResearchTask]:
        ResearchProjectService._check_permission(db, project_id, user_id)

        query = db.query(ResearchTask).filter(ResearchTask.project_id == project_id)

        if search:
            query = query.filter(ResearchTask.title.ilike(f"%{search.strip()}%"))
        if task_status:
            query = query.filter(ResearchTask.status == task_status)
        if priority:
            query = query.filter(ResearchTask.priority == priority)
        if assignee_id is not None:
            query = query.filter(ResearchTask.assignee_id == assignee_id)

        sort_col = getattr(ResearchTask, sort_by, ResearchTask.created_at)
        query = query.order_by(
            asc(sort_col) if order.lower() == "asc" else desc(sort_col)
        )

        return query.offset((page - 1) * size).limit(size).all()

    @staticmethod
    def get_task_by_id(db: Session, task_id: int, user_id: int) -> ResearchTask:
        task = ResearchTaskService._get_task(db, task_id)
        ResearchProjectService._check_permission(db, task.project_id, user_id)
        return task

    @staticmethod
    def update_task(
        db: Session, task_id: int, task_in: ResearchTaskUpdate, user_id: int
    ) -> ResearchTask:
        task = ResearchTaskService._get_task(db, task_id)
        _, member = ResearchProjectService._check_permission(
            db, task.project_id, user_id
        )

        update_data = task_in.model_dump(exclude_unset=True)
        if not update_data:
            return task

        is_owner = member.role == MemberRole.OWNER
        is_assignee = task.assignee_id == user_id

        if not is_owner and not is_assignee:
            raise ForbiddenException("Bạn không có quyền chỉnh sửa nhiệm vụ này")

        if not is_owner and is_assignee:
            restricted = {"assignee_id", "priority", "due_date", "title"}
            if set(update_data.keys()).intersection(restricted):
                raise ForbiddenException(
                    "Assignee chỉ có quyền cập nhật trạng thái hoặc mô tả"
                )

        if "assignee_id" in update_data:
            ResearchTaskService._validate_assignee(
                db, task.project_id, update_data["assignee_id"]
            )

        for key, value in update_data.items():
            setattr(task, key, value)

        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def delete_task(db: Session, task_id: int, user_id: int) -> None:
        task = ResearchTaskService._get_task(db, task_id)
        ResearchProjectService._check_permission(
            db, task.project_id, user_id, require_owner=True
        )
        db.delete(task)
        db.commit()
