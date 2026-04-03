# Finance Dashboard API

A comprehensive backend system for finance data processing and access control built with FastAPI and PostgreSQL.

## Features

### 🔐 User and Role Management
- **Three-tier role system**: Viewer, Analyst, Admin
- JWT-based authentication
- User registration and login
- Role-based access control
- User status management (active/inactive)

### 💰 Financial Records Management
- Complete CRUD operations for financial transactions
- Support for income and expense tracking
- Category-based organization
- Advanced filtering and search capabilities
- Date range queries

### 📊 Dashboard Analytics
- Real-time financial summaries
- Category-wise analysis
- Monthly/weekly trends
- Recent activity tracking
- Net balance calculations

### 🛡️ Security & Validation
- Input validation with detailed error messages
- Password strength requirements
- SQL injection protection
- Role-based API access control
- Comprehensive error handling

## Tech Stack

- **Backend**: FastAPI
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Authentication**: JWT (JSON Web Tokens)
- **Validation**: Pydantic

## Role Permissions

| Role | Permissions |
|------|-------------|
| **Viewer** | View dashboard data, view own financial records |
| **Analyst** | All viewer permissions + create/update/delete financial records, access insights |
| **Admin** | All permissions + manage users and system settings |

## Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- pip or poetry

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd finance-dashboard-api
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your database configuration
   ```

5. **Set up the database**
   ```bash
   # Create database
   createdb finance_db
   
   # Initialize database with sample data (optional)
   python scripts/init_db.py
   ```

6. **Start the server**
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login

### Users
- `GET /api/users/me` - Get current user info
- `PUT /api/users/me` - Update current user
- `GET /api/users/` - List users (Analyst+)
- `GET /api/users/{id}` - Get user details (Analyst+)
- `PUT /api/users/{id}` - Update user (Admin only)
- `DELETE /api/users/{id}` - Delete user (Admin only)

### Financial Records
- `POST /api/records/` - Create record (Analyst+)
- `GET /api/records/` - List records with filters
- `GET /api/records/{id}` - Get record details
- `PUT /api/records/{id}` - Update record (Analyst+)
- `DELETE /api/records/{id}` - Delete record (Analyst+)

### Dashboard
- `GET /api/dashboard/summary` - Get comprehensive dashboard summary
- `GET /api/dashboard/categories` - Get category-wise summaries
- `GET /api/dashboard/monthly-trends` - Get monthly trends

## Sample Users

After running the initialization script, you can use these sample accounts:

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |
| Analyst | analyst | analyst123 |
| Viewer | viewer | viewer123 |

## Database Schema

### Users Table
- `id` - Primary key
- `username` - Unique username
- `email` - Unique email address
- `hashed_password` - Bcrypt hashed password
- `full_name` - User's full name
- `role` - User role (viewer/analyst/admin)
- `status` - Account status (active/inactive)
- `created_at`, `updated_at` - Timestamps

### Financial Records Table
- `id` - Primary key
- `amount` - Transaction amount
- `type` - Transaction type (income/expense)
- `category` - Transaction category
- `description` - Optional description
- `date` - Transaction date
- `owner_id` - Foreign key to users table
- `created_at`, `updated_at` - Timestamps

## Environment Variables

```env
DATABASE_URL=postgresql://username:password@localhost/finance_db
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Development

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

### Database Migrations
```bash
# Tables are created automatically when the app starts
# To recreate tables, run:
python scripts/init_db.py
```

### Adding New Endpoints

1. Define Pydantic schemas in `app/schemas/`
2. Implement business logic in `app/routers/`
3. Add authentication/authorization using decorators
4. Include router in `app/main.py`

## Security Considerations

- All passwords are hashed using bcrypt
- JWT tokens expire after 30 minutes
- Input validation on all endpoints
- SQL injection protection via SQLAlchemy ORM
- Role-based access control on all sensitive operations
- CORS configuration for cross-origin requests

## Error Handling

The API provides consistent error responses:

```json
{
  "detail": "Error description",
  "type": "error_type",
  "status_code": 400
}
```

Error types include:
- `validation_error` - Input validation failed
- `http_error` - HTTP-specific errors
- `database_error` - Database operation failed
- `internal_error` - Unexpected server error

## Performance Considerations

- Database queries use proper indexing
- Pagination support on list endpoints
- Efficient aggregation queries for dashboard
- Connection pooling via SQLAlchemy
- Async support for high concurrency

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:
1. Check the API documentation at `/docs`
2. Review the error messages in responses
3. Check the logs for detailed error information
