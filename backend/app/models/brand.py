import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Brand(Base):
    __tablename__ = "brands"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sector: Mapped[str] = mapped_column(String(150), nullable=False)
    tone_of_voice: Mapped[str] = mapped_column(String(150), nullable=False)
    target_audience: Mapped[str] = mapped_column(String(255), nullable=False)
    keywords: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user = relationship("User", back_populates="brands")
    memory_items = relationship("BrandMemoryItem", back_populates="brand", cascade="all, delete-orphan")
    products = relationship("ProductService", back_populates="brand")
    generated_contents = relationship("GeneratedContent", back_populates="brand")
    generated_images = relationship("GeneratedImage", back_populates="brand")
    calendar_entries = relationship("ContentCalendar", back_populates="brand")
    analytics_entries = relationship("ManualPerformanceEntry", back_populates="brand")
    ai_jobs = relationship("AIJob", back_populates="brand")


class BrandMemoryItem(Base):
    __tablename__ = "brand_memory_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("brands.id", ondelete="CASCADE"), index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    brand = relationship("Brand", back_populates="memory_items")
