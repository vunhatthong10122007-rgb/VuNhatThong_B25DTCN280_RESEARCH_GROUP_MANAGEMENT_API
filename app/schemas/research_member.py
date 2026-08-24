from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.research_members import MemberRole
from app.schemas.user import UserResponse


class ResearchMemberBase(BaseModel):
    role: MemberRole = MemberRole.MEMBER


class ResearchMemberCreate(ResearchMemberBase):
    user_id: int = Field(..., description="Id người dùng cần thêm")
    role: MemberRole = MemberRole.MEMBER


class ResearchMemberUpdate(BaseModel):
    role: str | None = None


class ResearchMemberResponse(ResearchMemberBase):
    model_config = ConfigDict(from_attributes=True)

    project_id: int
    user_id: int
    joined_at: datetime
    user: UserResponse | None = None
