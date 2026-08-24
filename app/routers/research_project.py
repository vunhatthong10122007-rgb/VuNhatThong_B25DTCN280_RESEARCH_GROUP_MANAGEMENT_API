from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.dependencies.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.research_member import ResearchMemberCreate, ResearchMemberResponse
from app.schemas.research_project import (
    ResearchProjectBase,
    ResearchProjectResponse,
    ResearchProjectUpdate,
)
from app.services.research_project import ResearchProjectService

router = APIRouter(prefix="/research-projects", tags=["Research Projects"])


@router.post(
    "", response_model=ResearchProjectResponse, status_code=status.HTTP_201_CREATED
)
def create_project(
    project_in: ResearchProjectBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Tạo đề tài mới tự động trở thành OWNER"""
    return ResearchProjectService.create(db, project_in, current_user.id)


@router.get("", response_model=list[ResearchProjectResponse])
def get_my_projects(
    search: str | None = Query(None, description="Tìm theo tên đề tài"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Lấy danh sách đề tài mà user là OWNER hoặc MEMBER"""
    return ResearchProjectService.get_my_project(db, current_user.id, search)


@router.get("/{project_id}", response_model=ResearchProjectResponse)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Xem chi tiết đề tài"""
    return ResearchProjectService.get_by_id(db, project_id, current_user.id)


@router.patch("/{project_id}", response_model=ResearchProjectResponse)
def update_project(
    project_id: int,
    project_in: ResearchProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cập nhật đề tài"""
    return ResearchProjectService.update(db, project_id, project_in, current_user.id)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Xóa đề tài (hard delete, chỉ OWNER)"""
    ResearchProjectService.delete(db, project_id, current_user.id)


@router.get("/{project_id}/members", response_model=list[ResearchMemberResponse])
def get_members(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Xem danh sách thành viên"""
    return ResearchProjectService.get_members(db, project_id, current_user.id)


@router.post(
    "/{project_id}/members",
    response_model=ResearchMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_member(
    project_id: int,
    member_in: ResearchMemberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Thêm thành viên (chỉ OWNER)"""
    return ResearchProjectService.add_member(db, project_id, member_in, current_user.id)


@router.delete(
    "/{project_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_member(
    project_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Xóa thành viên (chỉ OWNER, không xóa được OWNER cuối cùng)"""
    ResearchProjectService.remove_member(db, project_id, user_id, current_user.id)
