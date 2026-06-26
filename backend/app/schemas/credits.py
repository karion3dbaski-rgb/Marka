from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CreditBalanceResponse(BaseModel):
    balance: int


class CreditLedgerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    amount: int
    action_type: str
    description: str
    balance_after: int
    created_at: datetime
