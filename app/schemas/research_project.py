from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ResearchProjectBase(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    description: str | None = None


class ResearchProjectCreate(ResearchProjectBase):
    owner_id: int


class ResearchProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    description: str | None = None
    owner_id: int | None = None


class ResearchProjectResponse(ResearchProjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime
