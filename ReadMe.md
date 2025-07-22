# E-Library API 📚

An online library system built with a robust FastAPI backend, designed for managing, searching, and securely downloading books.

## About The Project

This project is a comprehensive, production-ready backend API for an e-library platform. It features a secure authentication system, role-based access control, and a flexible file storage backend. The API is designed to be consumed by a separate frontend application (e.g., React, Vue, or a mobile app). 🚀

## Key Features ✨

*   🛡️ **Complete User Authentication:** Secure user registration with email verification, login with JWT (access/refresh tokens), and a full password management flow (forgot/reset/change).
*   👑 **Role-Based Access Control (RBAC):** A three-tier role system (`user`, `admin`, `superadmin`) protects sensitive endpoints and actions.
*   📖 **Full Book Management (CRUD):** Admins can upload, view, update, and delete books.
*   ☁️ **Dual Storage Backend:** A flexible storage service that can save files to either the **local disk** for development or **Amazon S3** for production.
*   📧 **Secure Asynchronous Downloads:** Users receive secure, temporary, one-time-use download links via professional HTML emails.
*   📊 **Comprehensive Admin Panel:** Endpoints for admins to list all users, manage admin roles, and view a complete history of all book downloads.
*   👤 **User-Specific Features:** Users can view and update their own profiles and see a history of their personal downloads.

## Built With 🛠️

This project leverages a modern, asynchronous Python technology stack.

*   **Framework:** FastAPI
*   **Database ORM:** SQLModel
*   **Database:** PostgreSQL
*   **Migrations:** Alembic
*   **Authentication:** python-jose for JWTs, passlib for hashing
*   **Async Support:** Uvicorn & [SQLAlchemy[asyncio]](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
*   **File Storage:** aioboto3 for S3, aiofiles for local storage
*   **Email:** fastapi-mail with Jinja2 for HTML templates

## Getting Started 🚀

To get a local copy up and running, follow these simple steps.

### Prerequisites

*   Python 3.11+
*   A running PostgreSQL instance

### Installation

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/your_username/your_repository_name.git
    cd your_repository_name
    ```

2.  **Create and activate a virtual environment:**
    ```sh
    python -m venv .venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
    ```

3.  **Install the dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

4.  **Set up your environment variables:**
    *   Create a `.env` file in the root directory by copying the example file:
        ```sh
        cp .env.example .env
        ```
    *   Edit the `.env` file with your specific database credentials, JWT secret, and email settings.

5.  **Run the database migrations:**
    ```sh
    alembic upgrade head
    ```

6.  **Run the application:**
    ```sh
    uvicorn src:app --reload
    ```
    The API will be available at `http://localhost:8000`.
