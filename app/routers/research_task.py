from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.dependencies.deps import get_current_user, get_db
from app.models.research_task import TaskPriority, TaskStatus
from app.models.user import User
from app.schemas.research_task import (
    ResearchTaskCreate,
    ResearchTaskResponse,
    ResearchTaskUpdate,
)
from app.services.research_task import ResearchTaskService

router = APIRouter(tags=["Research Tasks"])


@router.post(
    "/research-projects/{project_id}/research-tasks",
    response_model=ResearchTaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo nhiệm vụ nghiên cứu mới",
)
def create_task(
    project_id: int,
    task_in: ResearchTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Thành viên trong đề tài tạo nhiệm vụ mới."""
    return ResearchTaskService.create_task(
        db=db,
        project_id=project_id,
        task_in=task_in,
        user_id=current_user.id,
    )


@router.get(
    "/research-projects/{project_id}/research-tasks",
    response_model=list[ResearchTaskResponse],
    summary="Danh sách nhiệm vụ theo đề tài",
)
def get_project_tasks(
    project_id: int,
    search: str | None = Query(None, description="Tìm kiếm theo tiêu đề nhiệm vụ"),
    task_status: TaskStatus | None = Query(  # noqa: B008
        None,
        alias="status",
        description="Lọc theo trạng thái (TODO, IN_PROGRESS, DONE)",
    ),
    priority: TaskPriority | None = Query(  # noqa: B008
        None, description="Lọc theo độ ưu tiên (LOW, MEDIUM, HIGH)"
    ),
    assignee_id: int | None = Query(None, description="Lọc theo ID người được giao"),
    sort_by: str = Query(
        "created_at",
        pattern="^(created_at|due_date)$",
        description="Sắp xếp theo: created_at hoặc due_date",
    ),
    order: str = Query(
        "desc", pattern="^(asc|desc)$", description="Thứ tự sắp xếp: asc hoặc desc"
    ),
    page: int = Query(1, ge=1, description="Số trang (bắt đầu từ 1)"),
    size: int = Query(10, ge=1, le=100, description="Số lượng mỗi trang"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lấy danh sách nhiệm vụ của đề tài (chỉ thành viên trong đề tài mới xem được)."""
    return ResearchTaskService.get_project_tasks(
        db=db,
        project_id=project_id,
        user_id=current_user.id,
        search=search,
        task_status=task_status,
        priority=priority,
        assignee_id=assignee_id,
        sort_by=sort_by,
        order=order,
        page=page,
        size=size,
    )


@router.get(
    "/research-tasks/{task_id}",
    response_model=ResearchTaskResponse,
    summary="Chi tiết nhiệm vụ nghiên cứu",
)
def get_task_detail(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Xem chi tiết nhiệm vụ (yêu cầu user thuộc đề tài)."""
    return ResearchTaskService.get_task_by_id(
        db=db,
        task_id=task_id,
        user_id=current_user.id,
    )


@router.patch(
    "/research-tasks/{task_id}",
    response_model=ResearchTaskResponse,
    summary="Cập nhật nhiệm vụ nghiên cứu",
)
def update_task(
    task_id: int,
    task_in: ResearchTaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cập nhật nhiệm vụ (OWNER có toàn quyền; Assignee chỉ được cập nhật status hoặc description)."""
    return ResearchTaskService.update_task(
        db=db,
        task_id=task_id,
        task_in=task_in,
        user_id=current_user.id,
    )


@router.delete(
    "/research-tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Xóa nhiệm vụ nghiên cứu (Chỉ OWNER)",
)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Xóa nhiệm vụ nghiên cứu (chỉ OWNER đề tài mới có quyền xóa)."""
    ResearchTaskService.delete_task(
        db=db,
        task_id=task_id,
        user_id=current_user.id,
    )
