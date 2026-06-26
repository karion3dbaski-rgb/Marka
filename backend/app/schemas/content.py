from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

PlatformType = Literal["instagram", "twitter", "linkedin", "facebook"]


class ContentIdeasRequest(BaseModel):
    brand_id: UUID
    platform: PlatformType


class GeneratePostRequest(BaseModel):
    brand_id: UUID
    platform: PlatformType
    idea: str = Field(min_length=5)


class HashtagRequest(BaseModel):
    brand_id: UUID
    platform: PlatformType
    topic: str = Field(min_length=2)


class RewriteContentRequest(BaseModel):
    brand_id: UUID
    platform: PlatformType
    content: str = Field(min_length=5)
    instructions: str | None = None


class QualityCheckRequest(BaseModel):
    brand_id: UUID
    platform: PlatformType
    content: str = Field(min_length=5)


class ContentIdeaItem(BaseModel):
    title: str
    description: str
    suggested_format: str


class ContentIdeasResponse(BaseModel):
    ideas: list[ContentIdeaItem]


class GeneratedTextResponse(BaseModel):
    content: str


class HashtagResponse(BaseModel):
    hashtags: list[str]


class QualityCheckResponse(BaseModel):
    score: float
    feedback: list[str]
    improved_version: str | None = None


class ImageTemplateRequest(BaseModel):
    brand_id: UUID
    template_type: str = Field(min_length=2, max_length=100)
    prompt_details: str | None = None


class ImagePromptRequest(BaseModel):
    brand_id: UUID
    prompt: str = Field(min_length=5)


class GeneratedImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    brand_id: UUID
    user_id: UUID
    prompt_used: str
    image_url: str
    template_type: str | None
    created_at: datetime
