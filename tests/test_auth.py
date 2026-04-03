import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
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

class TestAuthentication:
    def test_register_user(self):
        response = client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "full_name": "Test User",
                "password": "TestPass123",
                "role": "viewer"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "id" in data

    def test_register_duplicate_email(self):
        # First registration
        client.post(
            "/api/auth/register",
            json={
                "username": "user1",
                "email": "duplicate@example.com",
                "full_name": "User One",
                "password": "TestPass123"
            }
        )
        
        # Second registration with same email
        response = client.post(
            "/api/auth/register",
            json={
                "username": "user2",
                "email": "duplicate@example.com",
                "full_name": "User Two",
                "password": "TestPass123"
            }
        )
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    def test_login_success(self):
        # Register user first
        client.post(
            "/api/auth/register",
            json={
                "username": "loginuser",
                "email": "login@example.com",
                "full_name": "Login User",
                "password": "LoginPass123"
            }
        )
        
        # Login
        response = client.post(
            "/api/auth/login",
            params={
                "username": "loginuser",
                "password": "LoginPass123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self):
        response = client.post(
            "/api/auth/login",
            params={
                "username": "nonexistent",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    def test_protected_endpoint_without_token(self):
        response = client.get("/api/users/me")
        assert response.status_code == 403

    def test_protected_endpoint_with_token(self):
        # Register and login
        client.post(
            "/api/auth/register",
            json={
                "username": "protecteduser",
                "email": "protected@example.com",
                "full_name": "Protected User",
                "password": "ProtectedPass123"
            }
        )
        
        login_response = client.post(
            "/api/auth/login",
            params={
                "username": "protecteduser",
                "password": "ProtectedPass123"
            }
        )
        token = login_response.json()["access_token"]
        
        # Access protected endpoint
        response = client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "protecteduser"
