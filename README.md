# GraphMind - Production-Grade Multi-Tenant FastAPI Backend

A modular, scalable FastAPI backend with:

✅ **Modular Architecture** - Each feature is a self-contained module  
✅ **Plug-and-Play Modules** - Dynamic router loading  
✅ **Shared Core Resources** - Centralized config, database, security  
✅ **Multi-Tenant Support** - Built-in tenant isolation  
✅ **Production Ready** - Docker, migrations, testing setup  

## Project Structure

```
fastapi-backend/
├── app/
│   ├── core/              # Shared logic (config, db, security, middleware)
│   ├── modules/           # Feature modules (auth, users, tenants, etc.)
│   ├── schemas/           # Pydantic models (request/response)
│   ├── models/            # SQLAlchemy ORM models
│   ├── utils/             # Utility functions (validators, formatters, helpers)
│   ├── plugins/           # Plugin system (dynamic router loading)
│   └── main.py            # FastAPI app entry point
│
├── tests/                 # Test suite
├── config/                # Environment-specific configs
├── migrations/            # Database migrations (Alembic)
├── requirements.txt       # Python dependencies
├── docker-compose.yml     # Docker services
├── dockerfile             # Docker image
└── .env                   # Environment variables
```

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Environment
```bash
cp .env.example .env
# Update .env with your settings
```

### 3. Run Locally
```bash
uvicorn app.main:app --reload
```

Visit: http://localhost:8000/docs

### 4. Run with Docker
```bash
docker-compose up
```

## Features

### Dynamic Module Loading
New modules are automatically discovered and registered. Just create a new directory in `app/modules/` with a `routes.py` file containing a `router` object.

### Module Template
```
app/modules/feature_name/
├── __init__.py
├── routes.py       # FastAPI router
├── models.py       # SQLAlchemy models
├── schemas.py      # Pydantic schemas
├── services.py     # Business logic
└── dependencies.py # FastAPI dependencies
```

### Multi-Tenant Support
- Tenant isolation via middleware
- Tenant dependency injection
- X-Tenant-ID header support

### Security
- JWT authentication
- Password hashing (bcrypt)
- CORS middleware
- Role-based access control

## Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/unit/test_auth.py
```

## Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "migration message"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Environment Configuration

- **Development**: `config/development.py`
- **Production**: `config/production.py`
- **Testing**: `config/testing.py`

## Adding New Features

1. Create module directory: `app/modules/feature_name/`
2. Implement `routes.py` with a `router` object
3. Add models, schemas, services as needed
4. Router is automatically loaded on startup

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Architecture Principles

- **Separation of Concerns**: Each module is independent
- **DRY (Don't Repeat Yourself)**: Shared logic in core/
- **Dependency Injection**: FastAPI Depends() for clean code
- **Type Safety**: Pydantic for validation, mypy for type checking
- **Testability**: Easy to mock and isolate

## Core Modules

### `core/config.py` - Configuration Management
- Environment variable support
- Settings for different environments

### `core/database.py` - Database Management
- SQLAlchemy integration
- Session factory
- Context managers

### `core/security.py` - Security Utilities
- JWT token creation/verification
- Password hashing
- Token validation

### `core/middleware.py` - Request Processing
- Tenant middleware
- Error handling
- Request logging

### `core/exceptions.py` - Custom Exceptions
- HTTP exceptions
- Tenant/Auth errors
- Validation errors

## Built-in Modules

### Auth Module (`modules/auth/`)
- User registration
- Login with JWT
- Token refresh

### Users Module (`modules/users/`)
- User CRUD operations
- User listing with pagination
- User role management

### Tenants Module (`modules/tenants/`)
- Tenant creation/management
- Multi-tenant data isolation
- Tenant membership

## Utilities

### `utils/validators.py`
- Email validation
- Slug validation
- Password strength checking

### `utils/formatters.py`
- DateTime formatting
- Response formatting
- camelCase to snake_case conversion

### `utils/helpers.py`
- ID generation
- List chunking
- Dictionary operations

## Plugin System (`plugins/loader.py`)

Automatically discovers and loads routers from modules. Supports:
- Auto-discovery of module routers
- Custom router loading
- Error handling for failed loads

## Next Steps

1. **Database Setup**: Configure PostgreSQL connection in `.env`
2. **Create First Feature**: Add module in `app/modules/`
3. **Write Tests**: Use `tests/` directory structure
4. **Deploy**: Use Docker for containerization

## License

MIT
