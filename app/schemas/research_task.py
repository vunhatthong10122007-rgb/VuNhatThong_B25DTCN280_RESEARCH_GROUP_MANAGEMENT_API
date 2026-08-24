from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ResearchTaskBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    status: str = "TODO"
    priority: str = "MEDIUM"
    due_date: datetime | None = None


class ResearchTaskCreate(ResearchTaskBase):
    project_id: int
    assignee_id: int | None = None


class ResearchTaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    assignee_id: int | None = None
    status: str | None = None
    priority: str | None = None
    due_date: datetime | None = None


class ResearchTaskResponse(ResearchTaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    assignee_id: int | None = None
    created_at: datetime
