from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    brand_id: UUID
    name: str = Field(min_length=2, max_length=255)
    description: str | None = None
    price: Decimal | None = None
    features: dict[str, Any] | list[Any] | None = None


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    description: str | None = None
    price: Decimal | None = None
    features: dict[str, Any] | list[Any] | None = None
    is_active: bool | None = None


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    brand_id: UUID
    name: str
    description: str | None
    price: Decimal | None
    features: dict[str, Any] | list[Any] | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
