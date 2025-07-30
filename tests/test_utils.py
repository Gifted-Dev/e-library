import pytest
from datetime import timedelta, datetime, timezone
from src.auth.utils import (
    generate_password_hash,
    verify_password,
    create_access_token,
    create_download_token,
    create_verification_token,
    create_password_reset_token,
    decode_token
)
import jwt
from src.config import Config


class TestAuthUtils:
    """Test authentication utility functions."""

    def test_generate_password_hash(self):
        """Test password hashing."""
        password = "testpassword123"
        hash_result = generate_password_hash(password)
        
        assert hash_result != password
        assert len(hash_result) > 0
        assert hash_result.startswith("$2b$")  # bcrypt hash format

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "testpassword123"
        hash_result = generate_password_hash(password)
        
        is_valid = verify_password(password, hash_result)
        
        assert is_valid is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hash_result = generate_password_hash(password)
        
        is_valid = verify_password(wrong_password, hash_result)
        
        assert is_valid is False

    def test_create_access_token_default(self):
        """Test creating access token with default expiry."""
        user_data = {"email": "test@example.com", "user_uid": "123"}
        
        token = create_access_token(user_data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode and verify token
        decoded = jwt.decode(token, Config.JWT_SECRET, algorithms=[Config.JWT_ALGORITHM])
        assert decoded["user"] == user_data
        assert "exp" in decoded
        assert "jti" in decoded
        assert decoded["refresh"] is False

    def test_create_access_token_custom_expiry(self):
        """Test creating access token with custom expiry."""
        user_data = {"email": "test@example.com", "user_uid": "123"}
        expiry = timedelta(minutes=30)
        
        token = create_access_token(user_data, expiry=expiry)
        
        assert isinstance(token, str)
        
        # Decode and verify token
        decoded = jwt.decode(token, Config.JWT_SECRET, algorithms=[Config.JWT_ALGORITHM])
        assert decoded["user"] == user_data
        
        # Check expiry is approximately 30 minutes from now
        exp_time = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
        expected_exp = datetime.now(timezone.utc) + expiry
        time_diff = abs((exp_time - expected_exp).total_seconds())
        assert time_diff < 60  # Allow 1 minute tolerance

    def test_create_refresh_token(self):
        """Test creating refresh token."""
        user_data = {"email": "test@example.com", "user_uid": "123"}
        
        token = create_access_token(user_data, refresh=True)
        
        assert isinstance(token, str)
        
        # Decode and verify token
        decoded = jwt.decode(token, Config.JWT_SECRET, algorithms=[Config.JWT_ALGORITHM])
        assert decoded["user"] == user_data
        assert decoded["refresh"] is True

    def test_create_download_token(self):
        """Test creating download token."""
        user_data = {"email": "test@example.com", "user_uid": "123"}
        book_uid = "book-123"
        
        token = create_download_token(user_data, book_uid)
        
        assert isinstance(token, str)
        
        # Decode and verify token
        decoded = jwt.decode(token, Config.JWT_SECRET, algorithms=[Config.JWT_ALGORITHM])
        assert decoded["user"] == user_data
        assert decoded["book_uid"] == book_uid
        assert "exp" in decoded
        assert "jti" in decoded

    def test_create_verification_token(self):
        """Test creating verification token."""
        user_data = {"email": "test@example.com", "user_uid": "123"}
        
        token = create_verification_token(user_data)
        
        assert isinstance(token, str)
        
        # Decode and verify token
        decoded = jwt.decode(token, Config.JWT_SECRET, algorithms=[Config.JWT_ALGORITHM])
        assert decoded["user"] == user_data
        assert decoded["verification"] is True
        assert "exp" in decoded
        assert "jti" in decoded

    def test_create_password_reset_token(self):
        """Test creating password reset token."""
        user_data = {"email": "test@example.com", "user_uid": "123"}
        
        token = create_password_reset_token(user_data)
        
        assert isinstance(token, str)
        
        # Decode and verify token
        decoded = jwt.decode(token, Config.JWT_SECRET, algorithms=[Config.JWT_ALGORITHM])
        assert decoded["user"] == user_data
        assert "exp" in decoded
        assert "jti" in decoded
        
        # Check expiry is approximately 15 minutes from now (default)
        exp_time = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
        expected_exp = datetime.now(timezone.utc) + timedelta(minutes=15)
        time_diff = abs((exp_time - expected_exp).total_seconds())
        assert time_diff < 60  # Allow 1 minute tolerance

    def test_decode_token_valid(self):
        """Test decoding valid token."""
        user_data = {"email": "test@example.com", "user_uid": "123"}
        token = create_access_token(user_data)
        
        decoded = decode_token(token)
        
        assert decoded is not None
        assert decoded["user"] == user_data
        assert "jti" in decoded

    def test_decode_token_invalid(self):
        """Test decoding invalid token."""
        invalid_token = "invalid.token.here"
        
        decoded = decode_token(invalid_token)
        
        assert decoded is None

    def test_decode_token_expired(self):
        """Test decoding expired token."""
        user_data = {"email": "test@example.com", "user_uid": "123"}
        # Create token that expires immediately
        expired_expiry = timedelta(seconds=-1)
        token = create_access_token(user_data, expiry=expired_expiry)
        
        decoded = decode_token(token)
        
        assert decoded is None

    def test_decode_token_missing_jti(self):
        """Test decoding token without jti claim."""
        # Create token manually without jti
        payload = {
            "user": {"email": "test@example.com"},
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }

        token = jwt.encode(payload, Config.JWT_SECRET, algorithm=Config.JWT_ALGORITHM)

        decoded = decode_token(token)

        assert decoded is None

    def test_token_uniqueness(self):
        """Test that tokens are unique (different jti)."""
        user_data = {"email": "test@example.com", "user_uid": "123"}
        
        token1 = create_access_token(user_data)
        token2 = create_access_token(user_data)
        
        assert token1 != token2
        
        decoded1 = jwt.decode(token1, Config.JWT_SECRET, algorithms=[Config.JWT_ALGORITHM])
        decoded2 = jwt.decode(token2, Config.JWT_SECRET, algorithms=[Config.JWT_ALGORITHM])
        
        assert decoded1["jti"] != decoded2["jti"]
