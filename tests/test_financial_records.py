import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, date
from app.main import app
from app.database import get_db, Base
from app.models.user import UserRole

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
    # Register user
    client.post(
        "/api/auth/register",
        json={
            "username": f"{role}user",
            "email": f"{role}@example.com",
            "full_name": f"{role.title()} User",
            "password": "TestPass123",
            "role": role
        }
    )
    
    # Login
    response = client.post(
        "/api/auth/login",
        params={
            "username": f"{role}user",
            "password": "TestPass123"
        }
    )
    return response.json()["access_token"]

class TestFinancialRecords:
    def test_create_financial_record_as_analyst(self):
        token = get_auth_token("analyst")
        
        response = client.post(
            "/api/records/",
            json={
                "amount": 1000.50,
                "type": "income",
                "category": "Salary",
                "description": "Monthly salary",
                "date": datetime.now().isoformat()
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["amount"] == 1000.50
        assert data["type"] == "income"
        assert data["category"] == "Salary"

    def test_create_financial_record_as_viewer_fails(self):
        token = get_auth_token("viewer")
        
        response = client.post(
            "/api/records/",
            json={
                "amount": 1000.50,
                "type": "income",
                "category": "Salary",
                "date": datetime.now().isoformat()
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["detail"]

    def test_create_financial_record_invalid_amount(self):
        token = get_auth_token("analyst")
        
        response = client.post(
            "/api/records/",
            json={
                "amount": -100.00,
                "type": "income",
                "category": "Salary",
                "date": datetime.now().isoformat()
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400
        assert "Amount must be positive" in response.json()["detail"]

    def test_get_financial_records(self):
        token = get_auth_token("analyst")
        
        # Create a record first
        client.post(
            "/api/records/",
            json={
                "amount": 500.00,
                "type": "expense",
                "category": "Groceries",
                "date": datetime.now().isoformat()
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Get records
        response = client.get(
            "/api/records/",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["amount"] == 500.00

    def test_get_financial_records_with_filters(self):
        token = get_auth_token("analyst")
        
        # Create records
        client.post(
            "/api/records/",
            json={
                "amount": 1000.00,
                "type": "income",
                "category": "Salary",
                "date": datetime.now().isoformat()
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        client.post(
            "/api/records/",
            json={
                "amount": 200.00,
                "type": "expense",
                "category": "Food",
                "date": datetime.now().isoformat()
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Filter by type
        response = client.get(
            "/api/records/?type=income",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert all(record["type"] == "income" for record in data)

    def test_update_financial_record(self):
        token = get_auth_token("analyst")
        
        # Create record
        create_response = client.post(
            "/api/records/",
            json={
                "amount": 100.00,
                "type": "expense",
                "category": "Transport",
                "date": datetime.now().isoformat()
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        record_id = create_response.json()["id"]
        
        # Update record
        response = client.put(
            f"/api/records/{record_id}",
            json={
                "amount": 150.00,
                "description": "Updated description"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == 150.00
        assert data["description"] == "Updated description"

    def test_delete_financial_record(self):
        token = get_auth_token("analyst")
        
        # Create record
        create_response = client.post(
            "/api/records/",
            json={
                "amount": 75.00,
                "type": "expense",
                "category": "Entertainment",
                "date": datetime.now().isoformat()
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        record_id = create_response.json()["id"]
        
        # Delete record
        response = client.delete(
            f"/api/records/{record_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]

    def test_admin_can_access_all_records(self):
        admin_token = get_auth_token("admin")
        analyst_token = get_auth_token("analyst")
        
        # Create record as analyst
        client.post(
            "/api/records/",
            json={
                "amount": 300.00,
                "type": "income",
                "category": "Freelance",
                "date": datetime.now().isoformat()
            },
            headers={"Authorization": f"Bearer {analyst_token}"}
        )
        
        # Admin should be able to see all records
        response = client.get(
            "/api/records/",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
