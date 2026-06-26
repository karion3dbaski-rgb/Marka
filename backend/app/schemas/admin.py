from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AdminDashboardResponse(BaseModel):
    total_users: int
    total_brands: int
    ai_jobs_today: int
    revenue: Decimal


class UserAdminResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    full_name: str
    is_active: bool
    is_admin: bool
    created_at: datetime


class UserCreditAdjustRequest(BaseModel):
    amount: int = Field(description="Pozitif değer kredi ekler, negatif değer kredi düşer.")
    description: str = Field(min_length=3, max_length=255)


class PromptTemplateCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    task_type: str = Field(min_length=2, max_length=100)
    platform: str | None = None
    prompt_text: str = Field(min_length=10)
    version: int = Field(default=1, ge=1)
    is_active: bool = True


class PromptTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    task_type: str
    platform: str | None
    prompt_text: str
    version: int
    is_active: bool
    created_by: UUID | None
    created_at: datetime


class AIJobAdminResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    brand_id: UUID | None
    job_type: str
    status: str
    provider: str | None
    model_used: str | None
    prompt_tokens: int | None
    completion_tokens: int | None
    cost_usd: Decimal | None
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None


class ProviderCostItem(BaseModel):
    provider: str
    total_cost: Decimal


class CostSummaryResponse(BaseModel):
    total_cost_usd: Decimal
    today_cost_usd: Decimal
    provider_breakdown: list[ProviderCostItem]
