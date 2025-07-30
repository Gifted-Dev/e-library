# 📚 E-Library Management System

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

A modern FastAPI-based e-library management system with JWT authentication, book management, and Redis-powered secure logout functionality.

## 🚀 Quick Start

### **Docker (Recommended)**
```bash
# Clone and run
git clone <your-repo-url>
cd e-library
docker build -t elibrary .
docker run -p 8000:8000 elibrary
```

### **Local Development**
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your database and Redis URLs

# Run the application (database tables created automatically)
uvicorn src:app --reload
```

> **Note**: Database tables are created automatically on first startup. No manual migrations needed!

### **API Documentation**
Visit `http://localhost:8000/docs` for interactive API documentation.

## ✨ Key Features

- **🔐 JWT Authentication** with Redis blocklist for secure logout
- **📖 Book Management** with upload, search, and download tracking
- **👥 User Management** with role-based access control (User/Admin/Superadmin)
- **📧 Email Notifications** for user verification and password reset
- **🛡️ Security** with password hashing and input validation
- **⚡ High Performance** with async/await and PostgreSQL
- **🧪 Comprehensive Testing** with 124+ test cases

## 📱 API Endpoints

### Authentication
- `POST /api/v1/auth/signup` - User registration
- `POST /api/v1/auth/login` - User login  
- `POST /api/v1/auth/logout` - User logout (invalidates tokens)
- `GET /api/v1/auth/users/me` - Get current user profile

### Books
- `GET /api/v1/books/all_books` - List all books with pagination
- `GET /api/v1/books/search` - Search books by title/author
- `POST /api/v1/books/upload` - Upload book (admin only)
- `GET /api/v1/books/{book_id}/download` - Download book

### Admin
- `GET /api/v1/admin/users` - List all users (admin only)
- `DELETE /api/v1/admin/users/{user_id}` - Delete user (admin only)

### Health Check
- `GET /health` - Application health status

## 🛠 Tech Stack

- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Primary database
- **Redis** - JWT blocklist and caching
- **SQLModel** - Type-safe database operations
- **Pydantic** - Data validation
- **JWT** - Authentication tokens
- **Docker** - Containerization

## 🔧 Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/elibrary

# Redis (for JWT blocklist)
REDIS_HOST=localhost
REDIS_PORT=6379

# JWT
JWT_SECRET=your-secret-key
JWT_ALGORITHM=HS256

# Email (optional)
MAIL_SERVER=smtp.gmail.com
MAIL_USERNAME=your-email
MAIL_PASSWORD=your-password
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_auth.py
```

## 📦 Deployment

### **Render (Recommended)**
1. Fork this repository
2. Connect to Render
3. Add environment variables
4. Deploy automatically

### **Local with Docker**
```bash
docker build -t elibrary .
docker run -p 8000:8000 elibrary
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

**Built with ❤️ using FastAPI and modern Python practices**
