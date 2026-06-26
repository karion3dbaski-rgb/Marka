import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.middleware.error_handler import ForbiddenError, NotFoundError
from app.models.brand import Brand, BrandMemoryItem
from app.models.subscription import SubscriptionPlan, UserSubscription


class BrandService:
    @staticmethod
    def normalize_keywords(keywords: str | list[str] | None) -> str | None:
        if keywords is None:
            return None
        if isinstance(keywords, list):
            cleaned = [item.strip() for item in keywords if item and item.strip()]
            return ", ".join(cleaned) if cleaned else None
        return keywords.strip() or None

    async def enforce_brand_limit(self, db: AsyncSession, user_id: uuid.UUID) -> None:
        subscription_result = await db.execute(
            select(UserSubscription, SubscriptionPlan)
            .join(SubscriptionPlan, UserSubscription.plan_id == SubscriptionPlan.id)
            .where(UserSubscription.user_id == user_id, UserSubscription.status == "active")
            .order_by(UserSubscription.created_at.desc())
            .limit(1)
        )
        subscription_row = subscription_result.first()
        if not subscription_row:
            return
        _, plan = subscription_row
        count_result = await db.execute(
            select(func.count(Brand.id)).where(Brand.user_id == user_id, Brand.is_active.is_(True))
        )
        active_brand_count = count_result.scalar_one()
        if plan.max_brands and active_brand_count >= plan.max_brands:
            raise ForbiddenError("Mevcut paketiniz ile daha fazla marka ekleyemezsiniz.")

    async def get_brand_for_user(
        self,
        db: AsyncSession,
        brand_id: uuid.UUID,
        user_id: uuid.UUID,
        include_inactive: bool = False,
    ) -> Brand:
        stmt = (
            select(Brand)
            .options(selectinload(Brand.memory_items))
            .where(Brand.id == brand_id, Brand.user_id == user_id)
        )
        if not include_inactive:
            stmt = stmt.where(Brand.is_active.is_(True))
        result = await db.execute(stmt)
        brand = result.scalar_one_or_none()
        if not brand:
            raise NotFoundError("Marka bulunamadı.")
        return brand

    async def list_brands(self, db: AsyncSession, user_id: uuid.UUID) -> list[Brand]:
        result = await db.execute(
            select(Brand)
            .options(selectinload(Brand.memory_items))
            .where(Brand.user_id == user_id, Brand.is_active.is_(True))
            .order_by(Brand.created_at.desc())
        )
        return list(result.scalars().all())

    async def create_memory_items(
        self,
        db: AsyncSession,
        brand: Brand,
        memory_items: list[dict[str, Any]] | None,
    ) -> None:
        if not memory_items:
            return
        for item in memory_items:
            category = item.get("category")
            content = item.get("content")
            if category and content:
                db.add(BrandMemoryItem(brand_id=brand.id, category=category, content=content))
        await db.flush()


brand_service = BrandService()
