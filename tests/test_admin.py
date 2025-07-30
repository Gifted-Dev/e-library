import pytest
from httpx import AsyncClient


class TestAdminRoutes:
    """Test admin-related routes."""

    async def test_get_all_users_success(self, client: AsyncClient, authenticated_admin: dict):
        """Test getting all users as admin."""
        headers = {"Authorization": f"Bearer {authenticated_admin['access_token']}"}
        
        response = await client.get("/api/v1/admin/users", headers=headers)
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_get_all_users_unauthorized(self, client: AsyncClient):
        """Test getting all users without authentication."""
        response = await client.get("/api/v1/admin/users")
        
        assert response.status_code == 403

    async def test_get_all_users_regular_user(self, client: AsyncClient, authenticated_user: dict):
        """Test getting all users as regular user (should fail)."""
        headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}
        
        response = await client.get("/api/v1/admin/users", headers=headers)
        
        assert response.status_code == 403

    async def test_get_all_users_with_pagination(self, client: AsyncClient, authenticated_admin: dict):
        """Test getting all users with pagination."""
        headers = {"Authorization": f"Bearer {authenticated_admin['access_token']}"}
        
        response = await client.get("/api/v1/admin/users?skip=0&limit=10", headers=headers)
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_make_admin_unauthorized(self, client: AsyncClient):
        """Test making user admin without authentication."""
        data = {"email": "test@example.com"}
        
        response = await client.post("/api/v1/admin/make_admin", data=data)
        
        assert response.status_code == 403

    async def test_make_admin_regular_user(self, client: AsyncClient, authenticated_user: dict):
        """Test making user admin as regular user (should fail)."""
        headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}
        data = {"email": "test@example.com"}
        
        response = await client.post("/api/v1/admin/make_admin", data=data, headers=headers)
        
        assert response.status_code == 403

    async def test_make_admin_user_not_found(self, client: AsyncClient, authenticated_admin: dict):
        """Test making non-existent user admin."""
        headers = {"Authorization": f"Bearer {authenticated_admin['access_token']}"}
        data = {"email": "nonexistent@example.com"}
        
        response = await client.post("/api/v1/admin/make_admin", data=data, headers=headers)
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["error"]["message"].lower()

    async def test_revoke_admin_unauthorized(self, client: AsyncClient):
        """Test revoking admin without authentication."""
        data = {"email": "test@example.com"}
        
        response = await client.post("/api/v1/admin/revoke_admin", data=data)
        
        assert response.status_code == 403

    async def test_revoke_admin_regular_user(self, client: AsyncClient, authenticated_user: dict):
        """Test revoking admin as regular user (should fail)."""
        headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}
        data = {"email": "test@example.com"}
        
        response = await client.post("/api/v1/admin/revoke_admin", data=data, headers=headers)
        
        assert response.status_code == 403

    async def test_revoke_admin_user_not_found(self, client: AsyncClient, authenticated_admin: dict):
        """Test revoking admin from non-existent user."""
        headers = {"Authorization": f"Bearer {authenticated_admin['access_token']}"}
        data = {"email": "nonexistent@example.com"}
        
        response = await client.post("/api/v1/admin/revoke_admin", data=data, headers=headers)
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["error"]["message"].lower()

    async def test_revoke_admin_not_admin_user(self, client: AsyncClient, authenticated_admin: dict, test_user_data: dict):
        """Test revoking admin from user who is not admin."""
        # First create a regular user
        await client.post("/api/v1/auth/signup", json=test_user_data)
        
        headers = {"Authorization": f"Bearer {authenticated_admin['access_token']}"}
        data = {"email": test_user_data["email"]}
        
        response = await client.post("/api/v1/admin/revoke_admin", data=data, headers=headers)
        
        assert response.status_code == 400
        data = response.json()
        assert "not an admin" in data["error"]["message"].lower()

    async def test_get_all_admins_unauthorized(self, client: AsyncClient):
        """Test getting all admins without authentication."""
        response = await client.get("/api/v1/admin/admins")
        
        assert response.status_code == 403

    async def test_get_all_admins_regular_user(self, client: AsyncClient, authenticated_user: dict):
        """Test getting all admins as regular user (should fail)."""
        headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}
        
        response = await client.get("/api/v1/admin/admins", headers=headers)
        
        assert response.status_code == 403

    async def test_get_all_admins_with_pagination(self, client: AsyncClient, authenticated_admin: dict):
        """Test getting all admins with pagination."""
        headers = {"Authorization": f"Bearer {authenticated_admin['access_token']}"}
        
        response = await client.get("/api/v1/admin/admins?skip=0&limit=10", headers=headers)
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_get_downloads_unauthorized(self, client: AsyncClient):
        """Test getting download logs without authentication."""
        response = await client.get("/api/v1/admin/downloads")
        
        assert response.status_code == 403

    async def test_get_downloads_regular_user(self, client: AsyncClient, authenticated_user: dict):
        """Test getting download logs as regular user (should fail)."""
        headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}
        
        response = await client.get("/api/v1/admin/downloads", headers=headers)
        
        assert response.status_code == 403

    async def test_get_downloads_success(self, client: AsyncClient, authenticated_admin: dict):
        """Test getting download logs as admin."""
        headers = {"Authorization": f"Bearer {authenticated_admin['access_token']}"}
        
        response = await client.get("/api/v1/admin/downloads", headers=headers)
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_get_downloads_with_pagination(self, client: AsyncClient, authenticated_admin: dict):
        """Test getting download logs with pagination."""
        headers = {"Authorization": f"Bearer {authenticated_admin['access_token']}"}
        
        response = await client.get("/api/v1/admin/downloads?skip=0&limit=10", headers=headers)
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)
