from pydantic import BaseModel
from datetime import datetime
from app.models.financial_record import TransactionType
from typing import Optional

class FinancialRecordBase(BaseModel):
    amount: float
    type: TransactionType
    category: str
    description: Optional[str] = None
    date: datetime

class FinancialRecordCreate(FinancialRecordBase):
    pass

class FinancialRecordUpdate(BaseModel):
    amount: Optional[float] = None
    type: Optional[TransactionType] = None
    category: Optional[str] = None
    description: Optional[str] = None
    date: Optional[datetime] = None

class FinancialRecordResponse(FinancialRecordBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
