from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BrandBase(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    sector: str = Field(min_length=2, max_length=150)
    tone_of_voice: str = Field(min_length=2, max_length=150)
    target_audience: str = Field(min_length=2, max_length=255)
    keywords: str | list[str] | None = None
    description: str | None = None
    logo_url: str | None = None


class BrandCreate(BrandBase):
    memory_items: list[dict[str, Any]] | None = None


class BrandUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    sector: str | None = Field(default=None, min_length=2, max_length=150)
    tone_of_voice: str | None = Field(default=None, min_length=2, max_length=150)
    target_audience: str | None = Field(default=None, min_length=2, max_length=255)
    keywords: str | list[str] | None = None
    description: str | None = None
    logo_url: str | None = None
    is_active: bool | None = None


class BrandMemoryItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    category: str
    content: str
    created_at: datetime


class BrandResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str
    sector: str
    tone_of_voice: str
    target_audience: str
    keywords: str | None
    description: str | None
    logo_url: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    memory_items: list[BrandMemoryItemResponse] = []
