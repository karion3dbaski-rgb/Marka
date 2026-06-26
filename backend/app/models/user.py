import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    brands = relationship("Brand", back_populates="user")
    generated_contents = relationship("GeneratedContent", back_populates="user")
    generated_images = relationship("GeneratedImage", back_populates="user")
    calendar_entries = relationship("ContentCalendar", back_populates="user")
    analytics_entries = relationship("ManualPerformanceEntry", back_populates="user")
    credit_ledger = relationship("CreditLedger", back_populates="user")
    ai_jobs = relationship("AIJob", back_populates="user")
    subscriptions = relationship("UserSubscription", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    prompt_templates = relationship("AIPromptTemplate", back_populates="admin_user")
