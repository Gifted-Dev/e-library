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
    """Test logout API and token invalidation."""

    async def test_logout_with_access_token_only(self, client: AsyncClient, authenticated_user: dict):
        """Test logout with only access token."""
        headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}
        
        # Mock Redis service
        with patch.object(redis_service, 'is_connected', return_value=True), \
             patch.object(redis_service, 'add_to_blocklist', return_value=True) as mock_add:
            
            response = await client.post("/api/v1/auth/logout", 
                                       json={}, 
                                       headers=headers)
            
            assert response.status_code == 200
            assert response.json()["message"] == "Successfully logged out"
            
            # Verify token was added to blocklist
            mock_add.assert_called_once()

    async def test_logout_with_both_tokens(self, client: AsyncClient, authenticated_user: dict):
        """Test logout with both access and refresh tokens."""
        headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}
        
        # Mock Redis service
        with patch.object(redis_service, 'is_connected', return_value=True), \
             patch.object(redis_service, 'add_to_blocklist', return_value=True) as mock_add:
            
            response = await client.post("/api/v1/auth/logout", 
                                       json={"refresh_token": authenticated_user['refresh_token']}, 
                                       headers=headers)
            
            assert response.status_code == 200
            assert response.json()["message"] == "Successfully logged out"
            
            # Verify both tokens were added to blocklist
            assert mock_add.call_count == 2

    async def test_logout_without_authentication(self, client: AsyncClient):
        """Test logout without authentication token."""
        response = await client.post("/api/v1/auth/logout", json={})
        
        assert response.status_code == 403
        data = response.json()
        assert "not authenticated" in data["error"]["message"].lower()

    async def test_logout_with_invalid_token(self, client: AsyncClient):
        """Test logout with invalid access token."""
        headers = {"Authorization": "Bearer invalid_token"}
        
        response = await client.post("/api/v1/auth/logout", 
                                   json={}, 
                                   headers=headers)
        
        assert response.status_code == 401
        data = response.json()
        assert "invalid" in data["error"]["message"].lower()

    async def test_logout_redis_unavailable(self, client: AsyncClient, authenticated_user: dict):
        """Test logout when Redis is unavailable."""
        headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}
        
        # Mock Redis as unavailable
        with patch.object(redis_service, 'is_connected', return_value=False):
            response = await client.post("/api/v1/auth/logout", 
                                       json={}, 
                                       headers=headers)
            
            assert response.status_code == 503
            data = response.json()
            assert "temporarily unavailable" in data["error"]["message"].lower()

    async def test_token_blocked_after_logout(self, client: AsyncClient, authenticated_user: dict):
        """Test that tokens are blocked after logout."""
        headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}
        
        # Mock Redis service
        with patch.object(redis_service, 'is_connected', return_value=True), \
             patch.object(redis_service, 'add_to_blocklist', return_value=True), \
             patch.object(redis_service, 'is_token_blocked', return_value=False) as mock_blocked:
            
            # First, logout
            response = await client.post("/api/v1/auth/logout", 
                                       json={}, 
                                       headers=headers)
            assert response.status_code == 200
            
            # Now mock the token as blocked
            mock_blocked.return_value = True
            
            # Try to access protected endpoint
            response = await client.get("/api/v1/auth/users/me", headers=headers)
            assert response.status_code == 401
            data = response.json()
            assert "revoked" in data["error"]["message"].lower()

    async def test_logout_with_invalid_refresh_token(self, client: AsyncClient, authenticated_user: dict):
        """Test logout with invalid refresh token."""
        headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}
        
        # Mock Redis service
        with patch.object(redis_service, 'is_connected', return_value=True), \
             patch.object(redis_service, 'add_to_blocklist', return_value=True) as mock_add:
            
            response = await client.post("/api/v1/auth/logout", 
                                       json={"refresh_token": "invalid_refresh_token"}, 
                                       headers=headers)
            
            assert response.status_code == 200
            assert response.json()["message"] == "Successfully logged out"
            
            # Only access token should be added to blocklist (refresh token is invalid)
            assert mock_add.call_count == 1

    async def test_multiple_logouts_same_token(self, client: AsyncClient, authenticated_user: dict):
        """Test multiple logout attempts with the same token."""
        headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}
        
        # Mock Redis service
        with patch.object(redis_service, 'is_connected', return_value=True), \
             patch.object(redis_service, 'add_to_blocklist', return_value=True):
            
            # First logout
            response1 = await client.post("/api/v1/auth/logout", 
                                        json={}, 
                                        headers=headers)
            assert response1.status_code == 200
            
            # Second logout with same token should still work
            response2 = await client.post("/api/v1/auth/logout", 
                                        json={}, 
                                        headers=headers)
            assert response2.status_code == 200

    async def test_logout_response_format(self, client: AsyncClient, authenticated_user: dict):
        """Test logout response format."""
        headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}
        
        # Mock Redis service
        with patch.object(redis_service, 'is_connected', return_value=True), \
             patch.object(redis_service, 'add_to_blocklist', return_value=True):
            
            response = await client.post("/api/v1/auth/logout", 
                                       json={}, 
                                       headers=headers)
            
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert isinstance(data["message"], str)
            assert data["message"] == "Successfully logged out"

    async def test_logout_with_empty_refresh_token(self, client: AsyncClient, authenticated_user: dict):
        """Test logout with empty refresh token."""
        headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}
        
        # Mock Redis service
        with patch.object(redis_service, 'is_connected', return_value=True), \
             patch.object(redis_service, 'add_to_blocklist', return_value=True) as mock_add:
            
            response = await client.post("/api/v1/auth/logout", 
                                       json={"refresh_token": ""}, 
                                       headers=headers)
            
            assert response.status_code == 200
            assert response.json()["message"] == "Successfully logged out"
            
            # Only access token should be added to blocklist
            assert mock_add.call_count == 1

    async def test_logout_with_null_refresh_token(self, client: AsyncClient, authenticated_user: dict):
        """Test logout with null refresh token."""
        headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}
        
        # Mock Redis service
        with patch.object(redis_service, 'is_connected', return_value=True), \
             patch.object(redis_service, 'add_to_blocklist', return_value=True) as mock_add:
            
            response = await client.post("/api/v1/auth/logout", 
                                       json={"refresh_token": None}, 
                                       headers=headers)
            
            assert response.status_code == 200
            assert response.json()["message"] == "Successfully logged out"
            
            # Only access token should be added to blocklist
            assert mock_add.call_count == 1


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
