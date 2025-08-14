"""
Tests for logout functionality and JWT blocklist.
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from src.core.redis import redis_service
from src.auth.services import UserService


@pytest.mark.asyncio
class TestLogoutFunctionality:
    """Test HTMX-based logout API and token invalidation."""

    async def test_successful_logout(self, client: AsyncClient, authenticated_user: dict):
        """
        Test successful logout via cookie authentication.
        Should clear the cookie, return a 200 OK, and an HX-Redirect header.
        """
        cookies = {"access_token": f"Bearer {authenticated_user['access_token']}"}
        
        with patch.object(redis_service, 'is_connected', return_value=True), \
             patch.object(redis_service, 'add_to_blocklist', return_value=True) as mock_add_to_blocklist:
            
            response = await client.post("/api/v1/auth/logout", cookies=cookies)
            
            assert response.status_code == 200
            assert response.text == ""  # Body should be empty
            assert response.headers.get("hx-redirect") == "/"
            
            # Verify the cookie was cleared in the response
            assert "access_token" in response.cookies
            assert response.cookies["access_token"] == ""
            # httpx sets expires to a past date for cleared cookies, checking for a non-future value is robust
            assert response.cookies.get("access_token").expires <= 0
            
            # Verify the access token's JTI was added to the blocklist
            mock_add_to_blocklist.assert_called_once()


    async def test_logout_without_authentication(self, client: AsyncClient):
        """
        Test logout without an authentication cookie.
        Should still return 200 OK and attempt to clear the cookie.
        """
        response = await client.post("/api/v1/auth/logout")
        
        assert response.status_code == 200
        assert response.headers.get("hx-redirect") == "/"
        assert "access_token" in response.cookies
        assert response.cookies["access_token"] == ""

    async def test_logout_with_invalid_token(self, client: AsyncClient):
        """Test logout with an invalid or malformed token in the cookie."""
        cookies = {"access_token": "Bearer invalid-token"}
        
        response = await client.post("/api/v1/auth/logout", cookies=cookies)
        
        assert response.status_code == 401
        data = response.json()
        assert "invalid or expired token" in data["detail"].lower()

    async def test_logout_redis_unavailable(self, client: AsyncClient, authenticated_user: dict):
        """Test logout behavior when the Redis service is down."""
        cookies = {"access_token": f"Bearer {authenticated_user['access_token']}"}
        
        # Mock Redis as unavailable
        with patch.object(redis_service, 'is_connected', return_value=False):
            response = await client.post("/api/v1/auth/logout", cookies=cookies)
            
            assert response.status_code == 503
            data = response.json()
            assert "logout service temporarily unavailable" in data["detail"].lower()

    async def test_token_is_blocked_after_logout(self, client: AsyncClient, authenticated_user: dict):
        """
        Verify that after a successful logout, the token is blocked and cannot be used
        to access protected endpoints.
        """
        cookies = {"access_token": f"Bearer {authenticated_user['access_token']}"}
        
        with patch.object(redis_service, 'is_connected', return_value=True), \
             patch.object(redis_service, 'add_to_blocklist', return_value=True), \
             patch.object(redis_service, 'is_token_blocked', return_value=False) as mock_is_blocked:
            
            # 1. Perform logout
            logout_response = await client.post("/api/v1/auth/logout", cookies=cookies)
            assert logout_response.status_code == 200
            
            # 2. Mock that the token is now in the blocklist
            mock_is_blocked.return_value = True
            
            # 3. Try to access a protected endpoint with the same (now blocked) token
            profile_response = await client.get("/api/v1/auth/users/me", cookies=cookies)
            
            assert profile_response.status_code == 401
            data = profile_response.json()
            assert "token has been revoked" in data["detail"].lower()

    async def test_multiple_logouts_with_same_token(self, client: AsyncClient, authenticated_user: dict):
        """Test that attempting to log out multiple times with the same token is handled gracefully."""
        cookies = {"access_token": f"Bearer {authenticated_user['access_token']}"}
        
        with patch.object(redis_service, 'is_connected', return_value=True), \
             patch.object(redis_service, 'add_to_blocklist', return_value=True):
            
            # First logout
            response1 = await client.post("/api/v1/auth/logout", cookies=cookies)
            assert response1.status_code == 200
            
            # Second logout with the same token should still succeed and redirect
            response2 = await client.post("/api/v1/auth/logout", cookies=cookies)
            assert response2.status_code == 200


@pytest.mark.asyncio
class TestRedisBlocklistService:
    """Test Redis blocklist service functionality."""

    async def test_redis_connection_check(self):
        """Test Redis connection status check."""
        with patch.object(redis_service, 'redis') as mock_redis:
            mock_redis.ping = AsyncMock()
            
            # Test successful connection
            result = await redis_service.is_connected()
            assert result is True
            mock_redis.ping.assert_called_once()

    async def test_add_token_to_blocklist(self):
        """Test adding token to blocklist."""
        with patch.object(redis_service, 'redis') as mock_redis:
            mock_redis.setex = AsyncMock()
            
            result = await redis_service.add_to_blocklist("test_jti", 3600)
            assert result is True
            mock_redis.setex.assert_called_once_with("blocklist:test_jti", 3600, "1")

    async def test_check_token_blocked(self):
        """Test checking if token is blocked."""
        with patch.object(redis_service, 'redis') as mock_redis:
            mock_redis.exists = AsyncMock(return_value=1)
            
            result = await redis_service.is_token_blocked("test_jti")
            assert result is True
            mock_redis.exists.assert_called_once_with("blocklist:test_jti")

    async def test_remove_token_from_blocklist(self):
        """Test removing token from blocklist."""
        with patch.object(redis_service, 'redis') as mock_redis:
            mock_redis.delete = AsyncMock(return_value=1)
            
            result = await redis_service.remove_from_blocklist("test_jti")
            assert result is True
            mock_redis.delete.assert_called_once_with("blocklist:test_jti")

    async def test_get_blocklist_size(self):
        """Test getting blocklist size."""
        with patch.object(redis_service, 'redis') as mock_redis:
            mock_redis.keys = AsyncMock(return_value=["blocklist:jti1", "blocklist:jti2"])
            
            result = await redis_service.get_blocklist_size()
            assert result == 2
            mock_redis.keys.assert_called_once_with("blocklist:*")

    async def test_clear_blocklist(self):
        """Test clearing blocklist."""
        with patch.object(redis_service, 'redis') as mock_redis:
            mock_redis.keys = AsyncMock(return_value=["blocklist:jti1", "blocklist:jti2"])
            mock_redis.delete = AsyncMock()
            
            result = await redis_service.clear_blocklist()
            assert result is True
            mock_redis.keys.assert_called_once_with("blocklist:*")
            mock_redis.delete.assert_called_once_with("blocklist:jti1", "blocklist:jti2")
