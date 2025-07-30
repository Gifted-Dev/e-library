# 📚 E-Library Management System - Backend API

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

A modern, high-performance FastAPI backend for digital library management with JWT authentication, book management, and Redis-powered secure logout functionality.

## 🚀 Features

### **🔐 Authentication & Security**
- **JWT Authentication** with access and refresh tokens
- **Redis-powered JWT blocklist** for secure logout
- **Password hashing** with bcrypt
- **Role-based access control** (User, Admin, Superadmin)
- **Email verification** system
- **Password reset** functionality

### **📖 Book Management**
- **Book upload** with file storage support
- **Advanced search** by title, author, and metadata
- **Download tracking** and analytics
- **Pagination** for efficient data retrieval
- **File management** with background deletion
- **Book metadata** extraction and storage

### **👥 User Management**
- **User registration** with email verification
- **Profile management** and updates
- **Admin user management** (view, delete users)
- **Download history** tracking
- **User activity** monitoring

### **⚡ Performance & Reliability**
- **Async/await** throughout for high concurrency
- **SQLModel** for type-safe database operations
- **PostgreSQL** for robust data storage
- **Redis** for caching and session management
- **Background tasks** for file operations
- **Comprehensive error handling**

## 🛠 Tech Stack

- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern Python web framework
- **[SQLModel](https://sqlmodel.tiangolo.com/)** - Type-safe database operations
- **[PostgreSQL](https://www.postgresql.org/)** - Primary database
- **[Redis](https://redis.io/)** - JWT blocklist and caching
- **[Pydantic](https://pydantic.dev/)** - Data validation and serialization
- **[Uvicorn](https://www.uvicorn.org/)** - ASGI server
- **[Alembic](https://alembic.sqlalchemy.org/)** - Database migrations (available)
- **[Pytest](https://pytest.org/)** - Testing framework

## 📋 Prerequisites

- **Python 3.11+**
- **PostgreSQL 12+**
- **Redis 6+**
- **Git**

## 🚀 Quick Start

### **1. Clone Repository**
```bash
git clone https://github.com/Gifted-Dev/e-library.git
cd e-library
```

### **2. Environment Setup**
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### **3. Environment Configuration**
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### **4. Database Setup**
```bash
# Ensure PostgreSQL is running
# Ensure Redis is running

# Database tables are created automatically on first startup
```

### **5. Run Application**
```bash
# Development server
uvicorn src:app --reload

# Production server
uvicorn src:app --host 0.0.0.0 --port 8000
```

### **6. Access API Documentation**
- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 🔧 Environment Variables

Create a `.env` file with the following configuration:

```bash
# --- App Config ---
ENVIRONMENT=development
DOMAIN=http://localhost:8000/api/v1
CLIENT_DOMAIN=http://localhost:3000

# --- Database ---
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/elibrary

# --- Redis ---
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_URL=redis://localhost:6379

# --- JWT ---
JWT_SECRET=your-super-secret-jwt-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# --- Email (Optional) ---
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_FROM=your-email@gmail.com
MAIL_FROM_NAME=E-Library System

# --- File Storage ---
STORAGE_BACKEND=local
UPLOAD_DIR=uploads
MAX_FILE_SIZE=50MB

# --- Security ---
SECRET_KEY=your-secret-key-for-general-encryption
BCRYPT_ROUNDS=12
```

## 📱 API Endpoints

### **Authentication**
```http
POST   /api/v1/auth/signup          # User registration
POST   /api/v1/auth/login           # User login
POST   /api/v1/auth/logout          # User logout (invalidates tokens)
POST   /api/v1/auth/refresh         # Refresh access token
GET    /api/v1/auth/users/me        # Get current user profile
PUT    /api/v1/auth/users/me        # Update user profile
POST   /api/v1/auth/verify-email    # Verify email address
POST   /api/v1/auth/forgot-password # Request password reset
POST   /api/v1/auth/reset-password  # Reset password
```

### **Books**
```http
GET    /api/v1/books/all_books      # List all books (paginated)
GET    /api/v1/books/search         # Search books by title/author
GET    /api/v1/books/get_book/{id}  # Get specific book details
POST   /api/v1/books/upload         # Upload book (admin only)
GET    /api/v1/books/download/{id}  # Download book file
DELETE /api/v1/books/delete-book/{id} # Delete book (admin only)
GET    /api/v1/books/download-logs  # Get download logs (admin only)
```

### **Admin**
```http
GET    /api/v1/admin/users          # List all users (admin only)
DELETE /api/v1/admin/users/{id}     # Delete user (admin only)
GET    /api/v1/admin/stats          # System statistics (admin only)
```

### **Health & Monitoring**
```http
GET    /health                      # Application health check
GET    /api/v1/health               # Detailed health status
```

## 🗄 Database Schema

The application uses **automatic table creation** via SQLModel. Database tables are created automatically when the application starts.

### **Key Models:**
- **User** - User accounts and profiles
- **Book** - Book metadata and file information
- **DownloadLog** - Download tracking and analytics
- **RefreshToken** - JWT refresh token management

### **Database Migration (Optional)**
While the app uses automatic table creation, Alembic is available for advanced migrations:

```bash
# Initialize Alembic (if needed)
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Description"

# Apply migration
alembic upgrade head
```

## 🧪 Testing

### **Run Tests**
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_auth.py

# Run with verbose output
pytest -v

# Run performance tests
pytest tests/test_performance.py
```

### **Test Coverage**
The project includes comprehensive tests covering:
- ✅ Authentication flows
- ✅ Book management operations
- ✅ Admin functionality
- ✅ API endpoints
- ✅ Database operations
- ✅ Error handling
- ✅ Performance benchmarks

## 🚀 Deployment

### **Docker Deployment**
```bash
# Build image
docker build -t elibrary-api .

# Run container
docker run -p 8000:8000 --env-file .env elibrary-api
```

### **Render Deployment**
1. Connect your GitHub repository to Render
2. Set environment variables in Render dashboard
3. Deploy automatically on push to main branch

**Render Configuration:**
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn src:app --host 0.0.0.0 --port $PORT`
- **Environment**: Python 3.11

### **Railway Deployment**
1. Connect repository to Railway
2. Configure environment variables
3. Deploy with automatic builds

## 📊 Performance

- **Async/await** throughout for high concurrency
- **Connection pooling** for database efficiency
- **Redis caching** for session management
- **Background tasks** for file operations
- **Optimized queries** with SQLModel
- **Pagination** for large datasets

## 🔒 Security Features

- **JWT tokens** with secure signing
- **Password hashing** with bcrypt
- **CORS protection** configured
- **Input validation** with Pydantic
- **SQL injection** protection via SQLModel
- **Rate limiting** ready (configurable)
- **Secure headers** implementation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

- **Documentation**: http://localhost:8000/docs
- **Issues**: [GitHub Issues](https://github.com/Gifted-Dev/e-library/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Gifted-Dev/e-library/discussions)

---

**Built with ❤️ using FastAPI and modern Python practices**
