from pydantic import BaseModel
from typing import List, Optional

class CategorySummary(BaseModel):
    category: str
    total_amount: float
    transaction_count: int

class MonthlyTrend(BaseModel):
    month: str
    income: float
    expenses: float
    net_balance: float

class DashboardSummary(BaseModel):
    total_income: float
    total_expenses: float
    net_balance: float
    category_summaries: List[CategorySummary]
    recent_transactions: List[dict]
    monthly_trends: List[MonthlyTrend]
