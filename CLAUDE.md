# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development Server
```bash
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Server
```bash
cd app
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Install Dependencies
```bash
pip install -r app/requirements.txt
```

### Testing
```bash
# Note: No test suite currently implemented
pytest  # When tests are added
```

## Architecture Overview

This is a FastAPI-based REST API with a modular monolithic architecture. The codebase follows a consistent layered pattern across all modules.

### Module Structure
Each module (auth, users, locations, notifications, queue, services) follows this pattern:
- **models.py**: SQLAlchemy ORM models
- **schemas.py**: Pydantic models for request/response validation
- **repository.py**: Data access layer extending base repository
- **service.py**: Business logic layer
- **routers.py**: FastAPI route definitions
- **permissions.py**: Role-based access control
- **dependencies.py**: FastAPI dependency injection

### Key Architectural Decisions

1. **Repository Pattern**: All data access goes through repository classes that extend `/app/base/repositories.py`. This provides consistent CRUD operations and separation of concerns.

2. **Authentication**: JWT-based with access and refresh tokens. Five role levels: SUPER_ADMIN, API_CLIENT, ADMIN, STAFF, CUSTOMER.

3. **Database**: Currently SQLite (test.db) with plans to migrate to PostgreSQL. Uses SQLAlchemy ORM with UUID primary keys (stored as strings for SQLite compatibility).

4. **API Documentation**: Available at `/docs` (Swagger) and `/redoc` in development mode only.

### Important Notes

- **Incomplete Implementation**: Only auth module is currently connected in main.py. Other modules exist but aren't registered.
- **Environment Variables**: Configured via .env file. Key variables include SQLALCHEMY_DATABASE_URL, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS, ENV.
- **No Test Suite**: Testing is mentioned in README but no tests exist yet.
- **CORS**: Currently allows all origins (development configuration).

### Common Development Tasks

When adding new features:
1. Follow the existing module structure pattern
2. Extend base repository for data access
3. Use dependency injection for database sessions and authentication
4. Add role-based permissions in the module's permissions.py
5. Register new routers in main.py

### Common Pitfalls

- **Repository Update Method**: The BaseRepository.update() method expects the modified object instance, not an ID and update data. First fetch the object, modify its attributes directly with setattr(), then pass the object to update().