from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

CalendarStatus = Literal["draft", "scheduled", "published"]
PlatformType = Literal["instagram", "twitter", "linkedin", "facebook"]


class CalendarEntryCreate(BaseModel):
    brand_id: UUID
    title: str = Field(min_length=2, max_length=255)
    content_text: str = Field(min_length=5)
    platform: PlatformType
    scheduled_date: datetime
    status: CalendarStatus = "draft"


class CalendarEntryUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=255)
    content_text: str | None = Field(default=None, min_length=5)
    platform: PlatformType | None = None
    scheduled_date: datetime | None = None
    status: CalendarStatus | None = None


class CalendarEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    brand_id: UUID
    user_id: UUID
    title: str
    content_text: str
    platform: str
    scheduled_date: datetime
    status: str
    created_at: datetime
    updated_at: datetime
