"""
Performance tests for API endpoints.
"""

import pytest
import asyncio
import time
from httpx import AsyncClient
from typing import List


@pytest.mark.asyncio
class TestPerformance:
    """Test API performance."""

    async def test_signup_performance(self, client: AsyncClient):
        """Test signup endpoint performance."""
        start_time = time.time()
        
        user_data = {
            "email": "perf_test@example.com",
            "password": "testpassword123",
            "first_name": "Performance",
            "last_name": "Test"
        }
        
        response = await client.post("/api/v1/auth/signup", json=user_data)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response.status_code == 201
        assert response_time < 2.0  # Should complete within 2 seconds

    async def test_login_performance(self, client: AsyncClient):
        """Test login endpoint performance."""
        # First create a user
        user_data = {
            "email": "login_perf@example.com",
            "password": "testpassword123",
            "first_name": "Login",
            "last_name": "Performance"
        }
        
        await client.post("/api/v1/auth/signup", json=user_data)
        
        # Test login performance
        start_time = time.time()
        
        login_response = await client.post("/api/v1/auth/login", json={
            "email": user_data["email"],
            "password": user_data["password"]
        })
        
        end_time = time.time()
        response_time = end_time - start_time
        
        assert login_response.status_code == 200
        assert response_time < 1.0  # Should complete within 1 second

    async def test_get_books_performance(self, client: AsyncClient, authenticated_user: dict):
        """Test get all books endpoint performance."""
        headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}
        
        start_time = time.time()
        
        response = await client.get("/api/v1/books/all_books", headers=headers)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 1.0  # Should complete within 1 second

    async def test_search_books_performance(self, client: AsyncClient, authenticated_user: dict):
        """Test book search endpoint performance."""
        headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}
        
        start_time = time.time()
        
        response = await client.get("/api/v1/books/search?title=test", headers=headers)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 1.0  # Should complete within 1 second

    async def test_get_user_profile_performance(self, client: AsyncClient, authenticated_user: dict):
        """Test get user profile endpoint performance."""
        headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}
        
        start_time = time.time()
        
        response = await client.get("/api/v1/auth/users/me", headers=headers)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 0.5  # Should complete within 0.5 seconds

    async def test_admin_endpoints_performance(self, client: AsyncClient, authenticated_admin: dict):
        """Test admin endpoints performance."""
        headers = {"Authorization": f"Bearer {authenticated_admin['access_token']}"}
        
        endpoints = [
            "/api/v1/admin/users",
            "/api/v1/admin/admins",
            "/api/v1/admin/downloads"
        ]
        
        for endpoint in endpoints:
            start_time = time.time()
            
            response = await client.get(endpoint, headers=headers)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            assert response.status_code == 200
            assert response_time < 1.0  # Should complete within 1 second

    async def test_concurrent_requests_performance(self, client: AsyncClient, authenticated_user: dict):
        """Test performance under concurrent requests."""
        headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}
        
        async def make_request():
            return await client.get("/api/v1/books/all_books", headers=headers)
        
        # Create 10 concurrent requests
        start_time = time.time()
        
        tasks = [make_request() for _ in range(10)]
        responses = await asyncio.gather(*tasks)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
        
        # 10 concurrent requests should complete within 3 seconds
        assert total_time < 3.0
        
        # Average response time should be reasonable
        avg_response_time = total_time / len(responses)
        assert avg_response_time < 0.5

    async def test_pagination_performance(self, client: AsyncClient, authenticated_admin: dict):
        """Test pagination performance with different page sizes."""
        headers = {"Authorization": f"Bearer {authenticated_admin['access_token']}"}
        
        page_sizes = [5, 10, 20, 50]
        
        for page_size in page_sizes:
            start_time = time.time()
            
            response = await client.get(f"/api/v1/admin/users?skip=0&limit={page_size}", headers=headers)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            assert response.status_code == 200
            assert response_time < 1.0  # Should complete within 1 second regardless of page size

    async def test_error_handling_performance(self, client: AsyncClient):
        """Test that error responses are fast."""
        # Test 404 error performance
        start_time = time.time()
        
        response = await client.get("/api/v1/books/12345678-1234-5678-9012-123456789012")
        
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response.status_code == 403  # Unauthorized
        assert response_time < 0.5  # Error responses should be fast
        
        # Test validation error performance
        start_time = time.time()
        
        invalid_data = {"email": "invalid", "password": "123"}
        response = await client.post("/api/v1/auth/signup", json=invalid_data)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response.status_code == 422
        assert response_time < 0.5  # Validation errors should be fast

    async def test_token_validation_performance(self, client: AsyncClient):
        """Test JWT token validation performance."""
        # Test with invalid token
        headers = {"Authorization": "Bearer invalid_token"}
        
        start_time = time.time()
        
        response = await client.get("/api/v1/auth/users/me", headers=headers)
        
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response.status_code == 401
        assert response_time < 0.3  # Token validation should be very fast

    async def test_database_query_performance(self, client: AsyncClient, authenticated_admin: dict):
        """Test database query performance."""
        headers = {"Authorization": f"Bearer {authenticated_admin['access_token']}"}
        
        # Test multiple database queries in sequence
        endpoints = [
            "/api/v1/admin/users",
            "/api/v1/books/all_books",
            "/api/v1/admin/downloads"
        ]
        
        start_time = time.time()
        
        for endpoint in endpoints:
            response = await client.get(endpoint, headers=headers)
            assert response.status_code == 200
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Multiple database queries should complete within reasonable time
        assert total_time < 2.0

    @pytest.mark.slow
    async def test_stress_test_signup(self, client: AsyncClient):
        """Stress test for signup endpoint."""
        async def create_user(index: int):
            user_data = {
                "email": f"stress_test_{index}@example.com",
                "password": "testpassword123",
                "first_name": f"Stress{index}",
                "last_name": "Test"
            }
            return await client.post("/api/v1/auth/signup", json=user_data)
        
        # Create 20 users concurrently
        start_time = time.time()
        
        tasks = [create_user(i) for i in range(20)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Count successful responses
        successful_responses = [r for r in responses if hasattr(r, 'status_code') and r.status_code == 201]
        
        # At least 80% should succeed
        success_rate = len(successful_responses) / len(responses)
        assert success_rate >= 0.8
        
        # Should complete within reasonable time
        assert total_time < 10.0
