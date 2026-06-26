import uuid

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.middleware.error_handler import ForbiddenError, ValidationApiError
from app.models.credits import CreditLedger


class CreditService:
    async def get_balance(self, db: AsyncSession, user_id: uuid.UUID) -> int:
        result = await db.execute(
            select(CreditLedger.balance_after)
            .where(CreditLedger.user_id == user_id)
            .order_by(desc(CreditLedger.created_at), desc(CreditLedger.id))
            .limit(1)
        )
        balance = result.scalar_one_or_none()
        return balance or 0

    async def ensure_credits(self, db: AsyncSession, user_id: uuid.UUID, required: int) -> int:
        balance = await self.get_balance(db, user_id)
        if balance < required:
            raise ForbiddenError("Yeterli krediniz bulunmuyor.")
        return balance

    async def add_credits(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        amount: int,
        action_type: str,
        description: str,
    ) -> CreditLedger:
        if amount == 0:
            raise ValidationApiError("Kredi tutarı 0 olamaz.")
        current_balance = await self.get_balance(db, user_id)
        new_balance = current_balance + amount
        if new_balance < 0:
            raise ForbiddenError("Bu işlem mevcut kredi bakiyesini negatife düşürüyor.")
        ledger = CreditLedger(
            user_id=user_id,
            amount=amount,
            action_type=action_type,
            description=description,
            balance_after=new_balance,
        )
        db.add(ledger)
        await db.flush()
        return ledger


credit_service = CreditService()
