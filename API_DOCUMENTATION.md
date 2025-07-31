# E-Library API Documentation for Frontend Developers

> **⚠️ Security Notice**: This API requires authentication for all data operations. The endpoints are protected by JWT tokens and role-based access control. Please follow security best practices when integrating.

## 🔗 Base URL
**Production**: `https://lightbearers.onrender.com`
**API Version**: `v1`
**Base API Path**: `https://lightbearers.onrender.com/api/v1`

## 📚 Interactive Documentation
- **Swagger UI**: https://lightbearers.onrender.com/docs
- **ReDoc**: https://lightbearers.onrender.com/redoc

## 🌍 Environment URLs
- **Production**: `https://lightbearers.onrender.com/api/v1`
- **Development**: `http://localhost:8000/api/v1` (when running locally)

## 🔐 Authentication
All protected endpoints require a Bearer token in the Authorization header:
```
Authorization: Bearer <access_token>
```

---

## 🔑 Authentication Endpoints

### 1. User Registration
**POST** `/api/v1/auth/signup`

**Request Body:**
```json
{
  "username": "johndoe",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "password": "securepassword123"
}
```

**Response (201):**
```json
{
  "uid": "uuid-string",
  "username": "johndoe",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "role": "user",
  "is_verified": false,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### 2. User Login
**POST** `/api/v1/auth/login`

**Request Body:**
```json
{
  "email": "john@example.com",
  "password": "securepassword123"
}
```

**Response (202):**
```json
{
  "message": "Login Successful",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### 3. Get Current User Profile
**GET** `/api/v1/auth/users/me`
**Headers:** `Authorization: Bearer <access_token>`

**Response (200):**
```json
{
  "uid": "uuid-string",
  "username": "johndoe",
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "role": "user",
  "is_verified": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

### 4. Email Verification
**POST** `/api/v1/auth/verify-email`

**Request Body:**
```json
{
  "token": "verification_token_from_email"
}
```

### 5. Forgot Password
**POST** `/api/v1/auth/forgot-password`

**Request Body:**
```json
{
  "email": "john@example.com"
}
```

### 6. Reset Password
**POST** `/api/v1/auth/reset-password`

**Request Body:**
```json
{
  "token": "reset_token_from_email",
  "new_password": "newpassword123"
}
```

### 7. Change Password
**POST** `/api/v1/auth/change-password`
**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "old_password": "oldpassword123",
  "new_password": "newpassword123"
}
```

### 8. Logout
**POST** `/api/v1/auth/logout`
**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "access_token": "current_access_token",
  "refresh_token": "current_refresh_token"
}
```

### 9. Update Profile
**PATCH** `/api/v1/auth/users/me`
**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "first_name": "Updated Name",
  "last_name": "Updated Last Name"
}
```

### 10. Get Download History
**GET** `/api/v1/auth/downloads`
**Headers:** `Authorization: Bearer <access_token>`

**Response (200):**
```json
{
  "downloads": [
    {
      "uid": "download-uuid",
      "book": {
        "uid": "book-uuid",
        "title": "Book Title",
        "author": "Author Name"
      },
      "timestamp": "2024-01-01T00:00:00Z",
      "was_emailed": true
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 10,
  "pages": 1
}
```

---

## 📖 Book Endpoints

### 1. Get All Books
**GET** `/api/v1/books/`
**Headers:** `Authorization: Bearer <access_token>`
**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 10)

**Response (200):**
```json
{
  "books": [
    {
      "uid": "book-uuid",
      "title": "Book Title",
      "author": "Author Name",
      "description": "Book description",
      "file_url": "/books/filename.pdf",
      "file_size": 2.5,
      "cover_image": "/covers/image.jpg",
      "uploaded_by": "uploader-uuid",
      "upload_date": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 10,
  "pages": 1
}
```

### 2. Search Books
**GET** `/api/v1/books/search`
**Headers:** `Authorization: Bearer <access_token>`
**Query Parameters:**
- `title` (optional): Search by title
- `author` (optional): Search by author
- `page` (optional): Page number
- `per_page` (optional): Items per page

**Example:** `/api/v1/books/search?title=python&author=smith&page=1`

### 3. Get Single Book
**GET** `/api/v1/books/{book_id}`
**Headers:** `Authorization: Bearer <access_token>`

**Response (200):**
```json
{
  "uid": "book-uuid",
  "title": "Book Title",
  "author": "Author Name",
  "description": "Book description",
  "file_url": "/books/filename.pdf",
  "file_size": 2.5,
  "cover_image": "/covers/image.jpg",
  "uploaded_by": "uploader-uuid",
  "upload_date": "2024-01-01T00:00:00Z"
}
```

### 4. Upload Book (Admin/Superadmin only)
**POST** `/api/v1/books/upload`
**Headers:** 
- `Authorization: Bearer <access_token>`
- `Content-Type: multipart/form-data`

**Form Data:**
- `file`: PDF file
- `title`: Book title
- `author`: Author name
- `description`: Book description
- `cover_image` (optional): Cover image file

### 5. Update Book (Admin/Superadmin only)
**PATCH** `/api/v1/books/{book_id}`
**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**
```json
{
  "title": "Updated Title",
  "author": "Updated Author",
  "description": "Updated description"
}
```

### 6. Delete Book (Admin/Superadmin only)
**DELETE** `/api/v1/books/{book_id}`
**Headers:** `Authorization: Bearer <access_token>`

### 7. Download Book
**GET** `/api/v1/books/{book_id}/download`
**Headers:** `Authorization: Bearer <access_token>`

**Response:** File download or redirect to download URL

### 8. Request Download Link
**POST** `/api/v1/books/{book_id}/download-link`
**Headers:** `Authorization: Bearer <access_token>`

**Response (200):**
```json
{
  "download_url": "https://lightbearers.onrender.com/api/v1/books/download/token",
  "expires_in": 3600,
  "message": "Download link sent to your email"
}
```

---

## 👑 Admin Endpoints

### 1. Get All Users (Admin/Superadmin only)
**GET** `/api/v1/admin/users`
**Headers:** `Authorization: Bearer <access_token>`
**Query Parameters:**
- `page` (optional): Page number
- `per_page` (optional): Items per page

### 2. Make User Admin (Superadmin only)
**PATCH** `/api/v1/admin/users/{user_id}/make-admin`
**Headers:** `Authorization: Bearer <access_token>`

### 3. Revoke Admin (Superadmin only)
**PATCH** `/api/v1/admin/users/{user_id}/revoke-admin`
**Headers:** `Authorization: Bearer <access_token>`

### 4. Get All Admins (Admin/Superadmin only)
**GET** `/api/v1/admin/admins`
**Headers:** `Authorization: Bearer <access_token>`

### 5. Get Download Analytics (Admin/Superadmin only)
**GET** `/api/v1/admin/downloads`
**Headers:** `Authorization: Bearer <access_token>`

---

## 🔧 Utility Endpoints

### Health Check
**GET** `/health`

**Response (200):**
```json
{
  "status": "healthy",
  "services": {
    "redis": {
      "status": "up",
      "info": {
        "status": "connected",
        "version": "6.2.6"
      }
    }
  }
}
```

---

## 📋 Error Responses

### Common Error Format:
```json
{
  "detail": "Error message description"
}
```

### HTTP Status Codes:
- `200`: Success
- `201`: Created
- `202`: Accepted
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `422`: Validation Error
- `500`: Internal Server Error

---

## 🚀 Getting Started

1. **Register a user** using `/api/v1/auth/signup`
2. **Login** using `/api/v1/auth/login` to get access token
3. **Use the access token** in Authorization header for protected endpoints
4. **Test endpoints** using the interactive docs at `/docs`

## 💻 Frontend Integration Example

### JavaScript/React Setup:
```javascript
// config.js
const API_CONFIG = {
  BASE_URL: 'https://lightbearers.onrender.com/api/v1',
  // For development: 'http://localhost:8000/api/v1'
};

// api.js
class ApiClient {
  constructor() {
    this.baseURL = API_CONFIG.BASE_URL;
    this.token = localStorage.getItem('access_token');
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...(this.token && { Authorization: `Bearer ${this.token}` }),
        ...options.headers,
      },
      ...options,
    };

    const response = await fetch(url, config);
    return response.json();
  }

  // Auth methods
  async login(email, password) {
    const response = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });

    if (response.access_token) {
      localStorage.setItem('access_token', response.access_token);
      this.token = response.access_token;
    }

    return response;
  }

  async getBooks(page = 1) {
    return this.request(`/books/?page=${page}`);
  }

  async getUserProfile() {
    return this.request('/auth/users/me');
  }
}

// Usage
const api = new ApiClient();
```

### Environment Variables (Frontend):
```env
# .env (React/Next.js)
REACT_APP_API_URL=https://lightbearers.onrender.com/api/v1

# .env (Vue/Nuxt)
VUE_APP_API_URL=https://lightbearers.onrender.com/api/v1

# .env (Svelte/SvelteKit)
VITE_API_URL=https://lightbearers.onrender.com/api/v1
```

## 📞 Support
For questions or issues, contact the backend development team.

**API Version**: 1.0.0
**Last Updated**: January 2024
