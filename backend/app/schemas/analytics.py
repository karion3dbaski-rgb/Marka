from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

PlatformType = Literal["instagram", "twitter", "linkedin", "facebook"]


class ManualAnalyticsCreateRequest(BaseModel):
    brand_id: UUID
    platform: PlatformType
    post_date: datetime
    likes: int = Field(default=0, ge=0)
    comments: int = Field(default=0, ge=0)
    shares: int = Field(default=0, ge=0)
    reach: int = Field(default=0, ge=0)
    impressions: int = Field(default=0, ge=0)
    notes: str | None = None


class ManualAnalyticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    brand_id: UUID
    user_id: UUID
    platform: str
    post_date: datetime
    likes: int
    comments: int
    shares: int
    reach: int
    impressions: int
    notes: str | None
    created_at: datetime


class AnalyticsReportRequest(BaseModel):
    brand_id: UUID
    start_date: datetime | None = None
    end_date: datetime | None = None


class AnalyticsReportResponse(BaseModel):
    report: str
    summary: dict[str, int | float]
