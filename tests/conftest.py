import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlmodel import SQLModel, create_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from src import app
from src.db.main import get_session
from src.config import Config
import os

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=True,
    connect_args={"check_same_thread": False}
)

# Create test session factory
TestSessionLocal = sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def test_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session
    
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

@pytest.fixture(scope="function")
async def client(test_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client."""
    def get_test_session():
        return test_session

    app.dependency_overrides[get_session] = get_test_session

    from fastapi.testclient import TestClient
    # For async tests, we'll use a sync TestClient wrapped in async
    test_client = TestClient(app)

    # Create a mock AsyncClient that uses TestClient internally
    class MockAsyncClient:
        def __init__(self, test_client):
            self.test_client = test_client

        async def post(self, url, **kwargs):
            return self.test_client.post(url, **kwargs)

        async def get(self, url, **kwargs):
            return self.test_client.get(url, **kwargs)

        async def patch(self, url, **kwargs):
            return self.test_client.patch(url, **kwargs)

        async def delete(self, url, **kwargs):
            return self.test_client.delete(url, **kwargs)

    yield MockAsyncClient(test_client)

    app.dependency_overrides.clear()

@pytest.fixture
def test_user_data():
    """Test user data."""
    return {
        "email": "test@example.com",
        "password": "testpassword123",
        "first_name": "Test",
        "last_name": "User"
    }

@pytest.fixture
def test_admin_data():
    """Test admin user data."""
    return {
        "email": "admin@example.com",
        "password": "adminpassword123",
        "first_name": "Admin",
        "last_name": "User"
    }

@pytest.fixture
def test_book_data():
    """Test book data."""
    return {
        "title": "Test Book",
        "author": "Test Author",
        "description": "A test book description"
    }

@pytest.fixture
async def authenticated_user(client: AsyncClient, test_user_data: dict):
    """Create and authenticate a test user."""
    # Register user
    response = await client.post("/api/v1/auth/signup", json=test_user_data)
    assert response.status_code == 201
    
    # Login user
    login_response = await client.post("/api/v1/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    assert login_response.status_code == 200
    
    tokens = login_response.json()
    return {
        "user_data": test_user_data,
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"]
    }

@pytest.fixture
async def authenticated_admin(client: AsyncClient):
    """Create and authenticate a test admin user."""
    # Use superadmin email to get admin privileges
    admin_data = {
        "email": "superadmin@example.com",  # This should be in SUPERADMIN_EMAILS
        "password": "adminpassword123",
        "first_name": "Admin",
        "last_name": "User"
    }

    # Register admin user
    response = await client.post("/api/v1/auth/signup", json=admin_data)
    assert response.status_code == 201

    # Login admin user
    login_response = await client.post("/api/v1/auth/login", json={
        "email": admin_data["email"],
        "password": admin_data["password"]
    })
    assert login_response.status_code == 200

    tokens = login_response.json()
    return {
        "user_data": admin_data,
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"]
    }
