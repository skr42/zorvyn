#!/usr/bin/env python3
"""
Initialize database with sample data
"""

import sys
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import Session


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
if os.path.exists(env_path):
    from dotenv import load_dotenv
    load_dotenv(env_path)

from app.database import SessionLocal, create_tables
from app.models import User, FinancialRecord, Role, UserRole, UserStatus, TransactionType
from app.auth.security import get_password_hash

def create_sample_data():
    """Create sample users and financial records"""
    # Create tables first
    create_tables()
    
    db = SessionLocal()
    
    try:
        # Create sample users
        admin_user = User(
            username="admin",
            email="admin@example.com",
            full_name="admin sujeet",
            hashed_password=get_password_hash("admin123"),
            role=UserRole.ADMIN,
            status=UserStatus.ACTIVE
        )
        
        analyst_user = User(
            username="analyst",
            email="analyst@example.com",
            full_name="analyst sujeet",
            hashed_password=get_password_hash("analyst123"),
            role=UserRole.ANALYST,
            status=UserStatus.ACTIVE
        )
        
        viewer_user = User(
            username="viewer",
            email="viewer@example.com",
            full_name="viewer sujeet",
            hashed_password=get_password_hash("viewer123"),
            role=UserRole.VIEWER,
            status=UserStatus.ACTIVE
        )
        
        db.add_all([admin_user, analyst_user, viewer_user])
        db.commit()
        db.refresh(admin_user)
        db.refresh(analyst_user)
        db.refresh(viewer_user)
        
        # Create sample financial records for analyst user
        base_date = datetime.now() - timedelta(days=90)
        
        sample_records = [
            # Income records
            FinancialRecord(
                amount=5000.00,
                type=TransactionType.INCOME,
                category="Salary",
                description="Monthly salary",
                date=base_date,
                owner_id=analyst_user.id
            ),
            FinancialRecord(
                amount=1500.00,
                type=TransactionType.INCOME,
                category="Freelance",
                description="Freelance project payment",
                date=base_date + timedelta(days=5),
                owner_id=analyst_user.id
            ),
            FinancialRecord(
                amount=200.00,
                type=TransactionType.INCOME,
                category="Investment",
                description="Dividend payment",
                date=base_date + timedelta(days=10),
                owner_id=analyst_user.id
            ),
            
            # Expense records
            FinancialRecord(
                amount=1200.00,
                type=TransactionType.EXPENSE,
                category="Rent",
                description="Monthly rent payment",
                date=base_date + timedelta(days=1),
                owner_id=analyst_user.id
            ),
            FinancialRecord(
                amount=300.00,
                type=TransactionType.EXPENSE,
                category="Groceries",
                description="Weekly groceries",
                date=base_date + timedelta(days=3),
                owner_id=analyst_user.id
            ),
            FinancialRecord(
                amount=150.00,
                type=TransactionType.EXPENSE,
                category="Utilities",
                description="Electricity and water bill",
                date=base_date + timedelta(days=7),
                owner_id=analyst_user.id
            ),
            FinancialRecord(
                amount=80.00,
                type=TransactionType.EXPENSE,
                category="Entertainment",
                description="Movie and dinner",
                date=base_date + timedelta(days=12),
                owner_id=analyst_user.id
            ),
            FinancialRecord(
                amount=500.00,
                type=TransactionType.EXPENSE,
                category="Healthcare",
                description="Doctor visit",
                date=base_date + timedelta(days=15),
                owner_id=analyst_user.id
            ),
        ]
        
        db.add_all(sample_records)
        db.commit()
        
        print("Sample data created successfully!")
        print("\nSample users:")
        print("- Admin: admin / admin123")
        print("- Analyst: analyst / analyst123") 
        print("- Viewer: viewer / viewer123")
        
    except Exception as e:
        print(f"Error creating sample data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_sample_data()
