from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies.deps import get_current_active_user, require_admin
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_active_user)):
    """trả thông tin người dùng hiện tại."""
    return current_user


@router.get("", response_model=list[UserResponse])
def get_users(
    search: str | None = Query(None, description="Search theo tên hoặc email"),
    is_active: bool | None = Query(None, description="Lọc theo trạng thái"),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """chỉ Admin search theo tên/email và trạng thái."""
    query = db.query(User)

    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(
            (User.email.ilike(pattern)) | (User.full_name.ilike(pattern))
        )

    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    return query.all()
