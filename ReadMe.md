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

This project is fully containerized using Docker and Docker Compose, which is the recommended way to run it for development.

### Prerequisites

*   [Docker](https://www.docker.com/get-started)
*   [Docker Compose](https://docs.docker.com/compose/install/)

### Running with Docker (Recommended)

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/Gifted-Dev/e-library.git
    cd e-library
    ```

2.  **Set up your environment variables:**
    *   Create a `.env` file in the root directory by copying the example file:
        ```sh
        cp .env.example .env
        ```
    *   Edit the `.env` file with your specific database credentials, JWT secret, and email settings.

3.  **Build and run the containers:**
    This command will build the backend image and start both the FastAPI application and the PostgreSQL database containers in the background.
    ```sh
    docker compose up --build -d
    ```

4.  **Run the database migrations:**
    With the containers running, execute the following command to apply the database schema to the new database.
    ```sh
    docker compose exec backend alembic upgrade head
    ```

5.  **You're all set!**
    The API will be available at `http://localhost:8000/docs`.

<details>
<summary>Click here for manual local setup (without Docker)</summary>

### Prerequisites
*   Python 3.11+
*   A running PostgreSQL instance

### Installation
1.  **Clone the repository** and `cd` into the directory.
2.  **Create and activate a virtual environment:**
    ```sh
    python -m venv .venv && source .venv/bin/activate
    ```
3.  **Install dependencies:** `pip install -r requirements-dev.txt`
4.  **Set up your `.env` file** as described in the Docker instructions.
5.  **Run migrations:** `alembic upgrade head`
6.  **Run the app:** `uvicorn src:app --reload`

</details>

## Production & Deployment ⚙️

This repository is configured for a professional production deployment and CI/CD workflow.

*   **Production-Ready Image:** The `Dockerfile.prod` file uses a multi-stage build to create a lean, optimized, and secure image. It runs the application as a non-root user and includes multiple Uvicorn workers for better performance.
*   **Production Compose File:** The `docker-compose.prod.yml` is configured to run the pre-built production image.
*   **Continuous Integration:** The `.github/workflows/ci.yml` file defines a GitHub Actions pipeline that automatically builds the production image and pushes it to Docker Hub on every commit to the `main` branch.

### Running in Production Mode (Locally)

You can test the production-ready container on your local machine by following these steps:

1.  **Build the production image:**
    This command uses the `Dockerfile.prod` to build and tag the final image.
    ```sh
    docker build -f Dockerfile.prod -t e-library:prod .
    ```
2.  **Launch the production stack:**
    This command uses the production compose file to start the services using the image you just built.
    ```sh
    docker compose -f docker-compose.prod.yml up -d
    ```
3.  **Run database migrations:**
    Just like in development, you need to apply the database schema to the new production database.
    ```sh
    docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
    ```
