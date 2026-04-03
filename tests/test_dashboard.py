import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from app.main import app
from app.database import get_db, Base

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def get_auth_token(role="analyst"):
    """Helper function to get authentication token"""
    client.post(
        "/api/auth/register",
        json={
            "username": f"{role}dashboard",
            "email": f"{role}dashboard@example.com",
            "full_name": f"{role.title()} Dashboard User",
            "password": "TestPass123",
            "role": role
        }
    )
    
    response = client.post(
        "/api/auth/login",
        params={
            "username": f"{role}dashboard",
            "password": "TestPass123"
        }
    )
    return response.json()["access_token"]

def create_sample_records(token):
    """Create sample financial records for testing"""
    base_date = datetime.now() - timedelta(days=30)
    
    records = [
        {
            "amount": 5000.00,
            "type": "income",
            "category": "Salary",
            "date": base_date.isoformat()
        },
        {
            "amount": 1200.00,
            "type": "expense",
            "category": "Rent",
            "date": (base_date + timedelta(days=5)).isoformat()
        },
        {
            "amount": 300.00,
            "type": "expense",
            "category": "Groceries",
            "date": (base_date + timedelta(days=10)).isoformat()
        },
        {
            "amount": 800.00,
            "type": "income",
            "category": "Freelance",
            "date": (base_date + timedelta(days=15)).isoformat()
        }
    ]
    
    for record in records:
        client.post(
            "/api/records/",
            json=record,
            headers={"Authorization": f"Bearer {token}"}
        )

class TestDashboard:
    def test_get_dashboard_summary(self):
        token = get_auth_token("analyst")
        create_sample_records(token)
        
        response = client.get(
            "/api/dashboard/summary",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check required fields
        assert "total_income" in data
        assert "total_expenses" in data
        assert "net_balance" in data
        assert "category_summaries" in data
        assert "recent_transactions" in data
        assert "monthly_trends" in data
        
        # Check calculations
        assert data["total_income"] == 5800.00  # 5000 + 800
        assert data["total_expenses"] == 1500.00  # 1200 + 300
        assert data["net_balance"] == 4300.00  # 5800 - 1500

    def test_get_dashboard_summary_as_viewer(self):
        token = get_auth_token("viewer")
        create_sample_records(token)
        
        response = client.get(
            "/api/dashboard/summary",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_income" in data
        assert "total_expenses" in data

    def test_get_category_summaries(self):
        token = get_auth_token("analyst")
        create_sample_records(token)
        
        response = client.get(
            "/api/dashboard/categories",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should have 4 categories: Salary, Rent, Groceries, Freelance
        assert len(data) == 4
        
        # Check category structure
        for category in data:
            assert "category" in category
            assert "total_amount" in category
            assert "transaction_count" in category
            assert category["transaction_count"] == 1

    def test_get_monthly_trends(self):
        token = get_auth_token("analyst")
        create_sample_records(token)
        
        response = client.get(
            "/api/dashboard/monthly-trends",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check trend structure
        for trend in data:
            assert "month" in trend
            assert "income" in trend
            assert "expenses" in trend
            assert "net_balance" in trend

    def test_dashboard_summary_with_date_range(self):
        token = get_auth_token("analyst")
        
        # Create records with specific dates
        old_date = (datetime.now() - timedelta(days=60)).isoformat()
        recent_date = (datetime.now() - timedelta(days=10)).isoformat()
        
        # Old record
        client.post(
            "/api/records/",
            json={
                "amount": 1000.00,
                "type": "income",
                "category": "Old Income",
                "date": old_date
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Recent record
        client.post(
            "/api/records/",
            json={
                "amount": 500.00,
                "type": "expense",
                "category": "Recent Expense",
                "date": recent_date
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Get summary for recent period only
        start_date = (datetime.now() - timedelta(days=30)).date().isoformat()
        end_date = datetime.now().date().isoformat()
        
        response = client.get(
            f"/api/dashboard/summary?start_date={start_date}&end_date={end_date}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should only include recent record
        assert data["total_income"] == 0.00  # No recent income
        assert data["total_expenses"] == 500.00  # Recent expense only

    def test_admin_dashboard_access(self):
        admin_token = get_auth_token("admin")
        analyst_token = get_auth_token("analyst")
        
        # Create records as analyst
        create_sample_records(analyst_token)
        
        # Admin should be able to access dashboard
        response = client.get(
            "/api/dashboard/summary",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_income" in data

    def test_dashboard_empty_data(self):
        token = get_auth_token("analyst")
        
        # Get dashboard without any records
        response = client.get(
            "/api/dashboard/summary",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_income"] == 0.00
        assert data["total_expenses"] == 0.00
        assert data["net_balance"] == 0.00
        assert len(data["category_summaries"]) == 0
        assert len(data["recent_transactions"]) == 0
