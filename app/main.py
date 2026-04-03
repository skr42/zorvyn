from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from app.routers import auth, users, financial_records, dashboard
from app.database import engine, Base, create_tables
from app.exceptions.handlers import (
    validation_exception_handler,
    http_exception_handler,
    database_exception_handler,
    general_exception_handler
)

create_tables()

app = FastAPI(
    title="Finance Dashboard API",
    description="Backend API for finance data processing and access control",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(financial_records.router, prefix="/api/records", tags=["financial records"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])

# Exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(SQLAlchemyError, database_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

@app.get("/")
async def root():
    return {"message": "Finance Dashboard API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
