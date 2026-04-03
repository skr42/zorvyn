from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, and_
from typing import List, Optional
from datetime import datetime, date, timedelta
from app.database import get_db
from app.models.user import User, UserRole
from app.models.financial_record import FinancialRecord, TransactionType
from app.schemas.dashboard import DashboardSummary, CategorySummary, MonthlyTrend
from app.auth.dependencies import get_current_user, require_min_role

router = APIRouter()

@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Set default date range to current month if not provided
    if not start_date:
        start_date = date.today().replace(day=1)
    if not end_date:
        end_date = date.today()
    
    # Base query - users can only see their own records unless admin
    base_query = db.query(FinancialRecord).filter(
        and_(
            FinancialRecord.date >= start_date,
            FinancialRecord.date <= end_date
        )
    )
    
    if current_user.role != UserRole.ADMIN:
        base_query = base_query.filter(FinancialRecord.owner_id == current_user.id)
    
    # Calculate totals
    income_subquery = base_query.filter(FinancialRecord.type == TransactionType.INCOME)
    expense_subquery = base_query.filter(FinancialRecord.type == TransactionType.EXPENSE)
    
    total_income = income_subquery.with_entities(func.sum(FinancialRecord.amount)).scalar() or 0
    total_expenses = expense_subquery.with_entities(func.sum(FinancialRecord.amount)).scalar() or 0
    net_balance = total_income - total_expenses
    
    # Category summaries
    category_query = base_query.with_entities(
        FinancialRecord.category,
        func.sum(FinancialRecord.amount).label('total_amount'),
        func.count(FinancialRecord.id).label('transaction_count')
    ).group_by(FinancialRecord.category).all()
    
    category_summaries = [
        CategorySummary(
            category=category,
            total_amount=float(total_amount),
            transaction_count=transaction_count
        )
        for category, total_amount, transaction_count in category_query
    ]
    
    # Recent transactions (last 10)
    recent_query = base_query.order_by(FinancialRecord.date.desc()).limit(10)
    recent_transactions = [
        {
            "id": record.id,
            "amount": float(record.amount),
            "type": record.type.value,
            "category": record.category,
            "description": record.description,
            "date": record.date.isoformat(),
            "owner_id": record.owner_id
        }
        for record in recent_query.all()
    ]
    
    # Monthly trends (last 12 months)
    twelve_months_ago = date.today() - timedelta(days=365)
    monthly_query = base_query.filter(FinancialRecord.date >= twelve_months_ago)
    
    if current_user.role != UserRole.ADMIN:
        monthly_query = monthly_query.filter(FinancialRecord.owner_id == current_user.id)
    
    monthly_data = monthly_query.with_entities(
        extract('year', FinancialRecord.date).label('year'),
        extract('month', FinancialRecord.date).label('month'),
        FinancialRecord.type,
        func.sum(FinancialRecord.amount).label('amount')
    ).group_by(
        extract('year', FinancialRecord.date),
        extract('month', FinancialRecord.date),
        FinancialRecord.type
    ).all()
    
    # Process monthly data
    monthly_dict = {}
    for year, month, trans_type, amount in monthly_data:
        month_key = f"{int(year)}-{int(month):02d}"
        if month_key not in monthly_dict:
            monthly_dict[month_key] = {"income": 0, "expenses": 0}
        
        if trans_type == TransactionType.INCOME:
            monthly_dict[month_key]["income"] = float(amount)
        else:
            monthly_dict[month_key]["expenses"] = float(amount)
    
    monthly_trends = [
        MonthlyTrend(
            month=month_key,
            income=data["income"],
            expenses=data["expenses"],
            net_balance=data["income"] - data["expenses"]
        )
        for month_key, data in sorted(monthly_dict.items())[-12:]
    ]
    
    return DashboardSummary(
        total_income=total_income,
        total_expenses=total_expenses,
        net_balance=net_balance,
        category_summaries=category_summaries,
        recent_transactions=recent_transactions,
        monthly_trends=monthly_trends
    )

@router.get("/categories", response_model=List[CategorySummary])
async def get_category_summaries(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not start_date:
        start_date = date.today().replace(day=1)
    if not end_date:
        end_date = date.today()
    
    query = db.query(FinancialRecord).filter(
        and_(
            FinancialRecord.date >= start_date,
            FinancialRecord.date <= end_date
        )
    )
    
    if current_user.role != UserRole.ADMIN:
        query = query.filter(FinancialRecord.owner_id == current_user.id)
    
    category_data = query.with_entities(
        FinancialRecord.category,
        func.sum(FinancialRecord.amount).label('total_amount'),
        func.count(FinancialRecord.id).label('transaction_count')
    ).group_by(FinancialRecord.category).all()
    
    return [
        CategorySummary(
            category=category,
            total_amount=float(total_amount),
            transaction_count=transaction_count
        )
        for category, total_amount, transaction_count in category_data
    ]

@router.get("/monthly-trends", response_model=List[MonthlyTrend])
async def get_monthly_trends(
    months: int = Query(12, ge=1, le=24),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_date = date.today() - timedelta(days=months * 30)
    
    query = db.query(FinancialRecord).filter(FinancialRecord.date >= start_date)
    
    if current_user.role != UserRole.ADMIN:
        query = query.filter(FinancialRecord.owner_id == current_user.id)
    
    monthly_data = query.with_entities(
        extract('year', FinancialRecord.date).label('year'),
        extract('month', FinancialRecord.date).label('month'),
        FinancialRecord.type,
        func.sum(FinancialRecord.amount).label('amount')
    ).group_by(
        extract('year', FinancialRecord.date),
        extract('month', FinancialRecord.date),
        FinancialRecord.type
    ).all()
    
    monthly_dict = {}
    for year, month, trans_type, amount in monthly_data:
        month_key = f"{int(year)}-{int(month):02d}"
        if month_key not in monthly_dict:
            monthly_dict[month_key] = {"income": 0, "expenses": 0}
        
        if trans_type == TransactionType.INCOME:
            monthly_dict[month_key]["income"] = float(amount)
        else:
            monthly_dict[month_key]["expenses"] = float(amount)
    
    return [
        MonthlyTrend(
            month=month_key,
            income=data["income"],
            expenses=data["expenses"],
            net_balance=data["income"] - data["expenses"]
        )
        for month_key, data in sorted(monthly_dict.items())[-months:]
    ]
