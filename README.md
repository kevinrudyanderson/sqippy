@ -1,223 +0,0 @@

# Sqipit

A FastAPI-based web application with modular architecture supporting authentication, location management, notifications, queue processing, and service management.

## 🚀 Features

- **Authentication System**: Complete user authentication with roles and permissions
- **Location Management**: Handle location-based data and services
- **Notification System**: Real-time notifications and messaging
- **Queue Processing**: Background task processing and job management
- **Service Management**: Comprehensive service handling and management
- **User Management**: User profiles, roles, and permissions

## 📁 Project Structure

```
sqipit/
├── app/                    # Main application directory
│   ├── auth/              # Authentication module
│   ├── locations/         # Location management
│   ├── notifications/     # Notification system
│   ├── queue/             # Queue processing
│   ├── services/          # Service management
│   ├── users/             # User management
│   ├── base/              # Base classes and utilities
│   ├── database.py        # Database configuration
│   ├── main.py            # FastAPI application entry point
│   ├── settings.py        # Application settings
│   └── requirements.txt   # Python dependencies
├── test.db                # SQLite database (development)
├── venv/                  # Virtual environment
└── .gitignore             # Git ignore patterns
```

## 🛠️ Installation

### Prerequisites

- Python 3.8+
- pip (Python package installer)

### Setup

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd sqipit
   ```

2. **Create and activate virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r app/requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env  # If available
   # Edit .env with your configuration
   ```

## 🚀 Running the Application

### Development Server

```bash
# From the project root
cd app
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The application will be available at:

- **API**: http://localhost:8000
- **Interactive API Documentation**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc

### Production

```bash
cd app
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📚 API Modules

### Authentication (`/auth`)

- User registration and login
- JWT token management
- Role-based access control
- Password reset functionality

### Users (`/users`)

- User profile management
- User permissions and roles
- User search and filtering

### Locations (`/locations`)

- Location data management
- Geographic operations
- Location-based services

### Notifications (`/notifications`)

- Real-time notification system
- Push notifications
- Email notifications
- Notification preferences

### Queue (`/queue`)

- Background task processing
- Job scheduling
- Task monitoring
- Queue management

### Services (`/services`)

- Service registry
- Service health checks
- Service configuration
- Service monitoring

## 🔧 Development

### Code Structure

Each module follows a consistent structure:

- `models.py` - Database models
- `schemas.py` - Pydantic models for API
- `repository.py` - Database operations
- `service.py` - Business logic
- `routers.py` - API endpoints
- `permissions.py` - Access control
- `utils.py` - Utility functions

### Database

The application uses SQLite for development (`test.db`). For production, configure your preferred database in the settings.

### Environment Variables

Create a `.env` file in the root directory:

```env
# Database
DATABASE_URL=sqlite:///./test.db

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Environment
ENVIRONMENT=development
DEBUG=True
```

### Testing

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=app tests/
```

## 🐳 Docker Support

If you want to containerize the application:

```dockerfile
# Dockerfile example
FROM python:3.9-slim

WORKDIR /app
COPY app/requirements.txt .
RUN pip install -r requirements.txt

COPY app/ .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

If you encounter any issues or have questions:

1. Check the [Issues](../../issues) page
2. Create a new issue if your problem isn't already reported
3. Provide detailed information about your environment and the problem

## 🔗 Links

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://pydantic-docs.helpmanual.io/)
