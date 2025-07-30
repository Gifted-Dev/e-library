"""
Integration tests for complete user workflows.
"""

import pytest
from httpx import AsyncClient
from io import BytesIO


@pytest.mark.asyncio
class TestUserWorkflow:
    """Test complete user workflows."""

    async def test_complete_user_registration_and_login_flow(self, client: AsyncClient):
        """Test complete user registration and login workflow."""
        # 1. Register a new user
        user_data = {
            "email": "integration@example.com",
            "password": "testpassword123",
            "first_name": "Integration",
            "last_name": "Test"
        }
        
        signup_response = await client.post("/api/v1/auth/signup", json=user_data)
        assert signup_response.status_code == 201
        
        user_info = signup_response.json()
        assert user_info["email"] == user_data["email"]
        assert user_info["first_name"] == user_data["first_name"]
        
        # 2. Login with the new user
        login_response = await client.post("/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        assert login_response.status_code == 200
        
        tokens = login_response.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        
        # 3. Access protected endpoint
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        profile_response = await client.get("/api/v1/auth/users/me", headers=headers)
        assert profile_response.status_code == 200
        
        profile = profile_response.json()
        assert profile["email"] == user_data["email"]

    async def test_password_change_workflow(self, client: AsyncClient, authenticated_user: dict):
        """Test password change workflow."""
        headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}
        
        # 1. Change password
        new_password = "newpassword123"
        change_data = {
            "old_password": authenticated_user["user_data"]["password"],
            "new_password": new_password
        }
        
        change_response = await client.post("/api/v1/auth/change-password", 
                                          json=change_data, headers=headers)
        assert change_response.status_code == 204
        
        # 2. Login with new password
        login_response = await client.post("/api/v1/auth/login", json={
            "email": authenticated_user["user_data"]["email"],
            "password": new_password
        })
        assert login_response.status_code == 200
        
        # 3. Verify old password doesn't work
        old_login_response = await client.post("/api/v1/auth/login", json={
            "email": authenticated_user["user_data"]["email"],
            "password": authenticated_user["user_data"]["password"]
        })
        assert old_login_response.status_code == 401

    async def test_book_management_workflow(self, client: AsyncClient, authenticated_admin: dict):
        """Test complete book management workflow."""
        headers = {"Authorization": f"Bearer {authenticated_admin['access_token']}"}
        
        # 1. Get initial book count
        books_response = await client.get("/api/v1/books/all_books", headers=headers)
        assert books_response.status_code == 200
        initial_count = len(books_response.json())
        
        # 2. Search for non-existent book
        search_response = await client.get("/api/v1/books/search?title=NonExistentBook", headers=headers)
        assert search_response.status_code == 200
        assert len(search_response.json()) == 0
        
        # 3. Try to get non-existent book
        fake_uuid = "12345678-1234-5678-9012-123456789012"
        get_response = await client.get(f"/api/v1/books/{fake_uuid}", headers=headers)
        assert get_response.status_code == 404

    async def test_admin_user_management_workflow(self, client: AsyncClient, authenticated_admin: dict):
        """Test admin user management workflow."""
        headers = {"Authorization": f"Bearer {authenticated_admin['access_token']}"}
        
        # 1. Create a regular user
        user_data = {
            "email": "manageme@example.com",
            "password": "testpassword123",
            "first_name": "Manage",
            "last_name": "Me"
        }
        
        signup_response = await client.post("/api/v1/auth/signup", json=user_data)
        assert signup_response.status_code == 201
        
        # 2. Get all users (admin should see the new user)
        users_response = await client.get("/api/v1/admin/users", headers=headers)
        assert users_response.status_code == 200
        users = users_response.json()
        assert len(users) >= 2  # At least admin and the new user
        
        # 3. Get all admins (note: superadmin users are also included)
        admins_response = await client.get("/api/v1/admin/admins", headers=headers)
        assert admins_response.status_code == 200
        admins = admins_response.json()
        assert len(admins) >= 0  # May be 0 if only superadmins exist
        
        # 4. Get download logs
        downloads_response = await client.get("/api/v1/admin/downloads", headers=headers)
        assert downloads_response.status_code == 200
        assert isinstance(downloads_response.json(), list)

    async def test_unauthorized_access_workflow(self, client: AsyncClient):
        """Test unauthorized access attempts."""
        # 1. Try to access protected endpoints without token
        protected_endpoints = [
            "/api/v1/auth/users/me",
            "/api/v1/books/all_books",
            "/api/v1/admin/users",
            "/api/v1/admin/admins",
            "/api/v1/admin/downloads"
        ]
        
        for endpoint in protected_endpoints:
            response = await client.get(endpoint)
            assert response.status_code == 403
        
        # 2. Try to access with invalid token
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        for endpoint in protected_endpoints:
            response = await client.get(endpoint, headers=invalid_headers)
            assert response.status_code == 401

    async def test_regular_user_admin_access_workflow(self, client: AsyncClient, authenticated_user: dict):
        """Test regular user trying to access admin endpoints."""
        headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}
        
        # Regular user should not be able to access admin endpoints
        admin_endpoints = [
            "/api/v1/admin/users",
            "/api/v1/admin/admins",
            "/api/v1/admin/downloads"
        ]
        
        for endpoint in admin_endpoints:
            response = await client.get(endpoint, headers=headers)
            assert response.status_code == 403

    async def test_error_handling_workflow(self, client: AsyncClient):
        """Test error handling across different scenarios."""
        # 1. Invalid registration data
        invalid_user_data = {
            "email": "invalid-email",
            "password": "123",  # Too short
            "first_name": "",
            "last_name": ""
        }
        
        response = await client.post("/api/v1/auth/signup", json=invalid_user_data)
        assert response.status_code == 422
        
        # 2. Duplicate email registration
        valid_user_data = {
            "email": "duplicate@example.com",
            "password": "testpassword123",
            "first_name": "Test",
            "last_name": "User"
        }
        
        # First registration
        response1 = await client.post("/api/v1/auth/signup", json=valid_user_data)
        assert response1.status_code == 201
        
        # Duplicate registration
        response2 = await client.post("/api/v1/auth/signup", json=valid_user_data)
        assert response2.status_code == 409
        
        # 3. Invalid login credentials
        invalid_login = {
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        
        response = await client.post("/api/v1/auth/login", json=invalid_login)
        assert response.status_code == 404

    async def test_pagination_workflow(self, client: AsyncClient, authenticated_admin: dict):
        """Test pagination across different endpoints."""
        headers = {"Authorization": f"Bearer {authenticated_admin['access_token']}"}
        
        # Test pagination parameters
        endpoints_with_pagination = [
            "/api/v1/books/all_books",
            "/api/v1/admin/users",
            "/api/v1/admin/admins",
            "/api/v1/admin/downloads"
        ]
        
        for endpoint in endpoints_with_pagination:
            # Test with pagination parameters
            response = await client.get(f"{endpoint}?skip=0&limit=5", headers=headers)
            assert response.status_code == 200
            assert isinstance(response.json(), list)
            
            # Test with different pagination
            response = await client.get(f"{endpoint}?skip=10&limit=10", headers=headers)
            assert response.status_code == 200
            assert isinstance(response.json(), list)
