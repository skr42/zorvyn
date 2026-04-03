from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional
from datetime import datetime, date
from app.database import get_db
from app.models.user import User, UserRole
from app.models.financial_record import FinancialRecord, TransactionType
from app.schemas.financial_record import FinancialRecordCreate, FinancialRecordResponse, FinancialRecordUpdate
from app.auth.dependencies import get_current_user, require_min_role

router = APIRouter()

@router.post("/", response_model=FinancialRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_financial_record(
    record: FinancialRecordCreate,
    current_user: User = Depends(require_min_role(UserRole.ANALYST)),
    db: Session = Depends(get_db)
):
    if record.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be positive"
        )
    
    db_record = FinancialRecord(
        **record.dict(),
        owner_id=current_user.id
    )
    
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record

@router.get("/", response_model=List[FinancialRecordResponse])
async def get_financial_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    transaction_type: Optional[TransactionType] = Query(None),
    category: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    min_amount: Optional[float] = Query(None),
    max_amount: Optional[float] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(FinancialRecord)
    
    # Users can only see their own records unless they're admin
    if current_user.role != UserRole.ADMIN:
        query = query.filter(FinancialRecord.owner_id == current_user.id)
    
    if transaction_type:
        query = query.filter(FinancialRecord.type == transaction_type)
    
    if category:
        query = query.filter(FinancialRecord.category.ilike(f"%{category}%"))
    
    if start_date:
        query = query.filter(FinancialRecord.date >= start_date)
    
    if end_date:
        query = query.filter(FinancialRecord.date <= end_date)
    
    if min_amount:
        query = query.filter(FinancialRecord.amount >= min_amount)
    
    if max_amount:
        query = query.filter(FinancialRecord.amount <= max_amount)
    
    records = query.order_by(FinancialRecord.date.desc()).offset(skip).limit(limit).all()
    return records

@router.get("/{record_id}", response_model=FinancialRecordResponse)
async def get_financial_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.query(FinancialRecord).filter(FinancialRecord.id == record_id).first()
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financial record not found"
        )
    
    # Users can only access their own records unless they're admin
    if current_user.role != UserRole.ADMIN and record.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this record"
        )
    
    return record

@router.put("/{record_id}", response_model=FinancialRecordResponse)
async def update_financial_record(
    record_id: int,
    record_update: FinancialRecordUpdate,
    current_user: User = Depends(require_min_role(UserRole.ANALYST)),
    db: Session = Depends(get_db)
):
    record = db.query(FinancialRecord).filter(FinancialRecord.id == record_id).first()
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financial record not found"
        )
    
    # Users can only update their own records unless they're admin
    if current_user.role != UserRole.ADMIN and record.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this record"
        )
    
    update_data = record_update.dict(exclude_unset=True)
    
    if "amount" in update_data and update_data["amount"] <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be positive"
        )
    
    for field, value in update_data.items():
        setattr(record, field, value)
    
    db.commit()
    db.refresh(record)
    return record

@router.delete("/{record_id}")
async def delete_financial_record(
    record_id: int,
    current_user: User = Depends(require_min_role(UserRole.ANALYST)),
    db: Session = Depends(get_db)
):
    record = db.query(FinancialRecord).filter(FinancialRecord.id == record_id).first()
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financial record not found"
        )
    
    # Users can only delete their own records unless they're admin
    if current_user.role != UserRole.ADMIN and record.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this record"
        )
    
    db.delete(record)
    db.commit()
    return {"message": "Financial record deleted successfully"}
