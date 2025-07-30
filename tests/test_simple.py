import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from src import app


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test the root endpoint redirects to docs."""
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_docs_endpoint():
    """Test the docs endpoint is accessible."""
    client = TestClient(app)
    response = client.get("/docs")
    assert response.status_code == 200


def test_app_creation():
    """Test that the FastAPI app can be created."""
    from src import app
    assert app is not None
    assert hasattr(app, 'routes')
    assert len(app.routes) > 0
