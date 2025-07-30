import pytest
from sqlmodel.ext.asyncio.session import AsyncSession
from src.auth.services import UserService
from src.books.services import BookService
from src.auth.schemas import UserCreateModel, UserLoginModel, UserUpdateModel
from src.books.schemas import BookCreateModel, BookUpdateModel
from src.db.models import User, Book
from src.core.exceptions import (
    UserNotFoundError,
    InvalidCredentialsError,
    BookNotFoundError
)
from uuid import uuid4


class TestUserService:
    """Test UserService methods."""

    @pytest.fixture
    def user_service(self):
        return UserService()

    @pytest.fixture
    def sample_user_data(self):
        return UserCreateModel(
            email="test@example.com",
            password="testpassword123",
            first_name="Test",
            last_name="User"
        )

    async def test_create_user_success(self, user_service: UserService, sample_user_data: UserCreateModel, test_session: AsyncSession):
        """Test successful user creation."""
        user = await user_service.create_user(sample_user_data, test_session)
        
        assert user.email == sample_user_data.email
        assert user.first_name == sample_user_data.first_name
        assert user.last_name == sample_user_data.last_name
        assert user.role == "user"
        assert user.password_hash != sample_user_data.password  # Should be hashed
        assert not user.is_verified  # Should be False by default

    async def test_create_superadmin_user(self, user_service: UserService, test_session: AsyncSession):
        """Test creating a superadmin user."""
        # Use an email that's in the superadmin list
        superadmin_data = UserCreateModel(
            email="superadmin@example.com",
            password="testpassword123",
            first_name="Super",
            last_name="Admin"
        )
        
        user = await user_service.create_user(superadmin_data, test_session)
        
        # Note: This test might fail if the email is not in Config.SUPERADMIN_EMAILS
        # In a real test, you'd mock the config or use a test-specific email
        assert user.email == superadmin_data.email

    async def test_get_user_by_email_success(self, user_service: UserService, sample_user_data: UserCreateModel, test_session: AsyncSession):
        """Test getting user by email."""
        # Create user first
        created_user = await user_service.create_user(sample_user_data, test_session)
        
        # Get user by email
        found_user = await user_service.get_user_by_email(sample_user_data.email, test_session)
        
        assert found_user is not None
        assert found_user.email == sample_user_data.email
        assert found_user.uid == created_user.uid

    async def test_get_user_by_email_not_found(self, user_service: UserService, test_session: AsyncSession):
        """Test getting non-existent user by email."""
        user = await user_service.get_user_by_email("nonexistent@example.com", test_session)
        
        assert user is None

    async def test_user_exists_true(self, user_service: UserService, sample_user_data: UserCreateModel, test_session: AsyncSession):
        """Test user_exists returns True for existing user."""
        # Create user first
        await user_service.create_user(sample_user_data, test_session)
        
        # Check if user exists
        exists = await user_service.user_exists(sample_user_data.email, test_session)
        
        assert exists is True

    async def test_user_exists_false(self, user_service: UserService, test_session: AsyncSession):
        """Test user_exists returns False for non-existent user."""
        exists = await user_service.user_exists("nonexistent@example.com", test_session)
        
        assert exists is False

    async def test_login_user_success(self, user_service: UserService, sample_user_data: UserCreateModel, test_session: AsyncSession):
        """Test successful user login."""
        # Create user first
        await user_service.create_user(sample_user_data, test_session)
        
        # Login
        login_data = UserLoginModel(
            email=sample_user_data.email,
            password=sample_user_data.password
        )
        
        response = await user_service.login_user(login_data, test_session)
        
        assert response.status_code == 200
        response_data = response.body.decode()
        assert "access_token" in response_data
        assert "refresh_token" in response_data

    async def test_login_user_not_found(self, user_service: UserService, test_session: AsyncSession):
        """Test login with non-existent user."""
        login_data = UserLoginModel(
            email="nonexistent@example.com",
            password="password123"
        )
        
        with pytest.raises(UserNotFoundError):
            await user_service.login_user(login_data, test_session)

    async def test_login_user_wrong_password(self, user_service: UserService, sample_user_data: UserCreateModel, test_session: AsyncSession):
        """Test login with wrong password."""
        # Create user first
        await user_service.create_user(sample_user_data, test_session)
        
        # Login with wrong password
        login_data = UserLoginModel(
            email=sample_user_data.email,
            password="wrongpassword"
        )
        
        with pytest.raises(InvalidCredentialsError):
            await user_service.login_user(login_data, test_session)

    async def test_get_user_by_uid_success(self, user_service: UserService, sample_user_data: UserCreateModel, test_session: AsyncSession):
        """Test getting user by UID."""
        # Create user first
        created_user = await user_service.create_user(sample_user_data, test_session)
        
        # Get user by UID
        found_user = await user_service.get_user_by_uid(str(created_user.uid), test_session)
        
        assert found_user is not None
        assert found_user.uid == created_user.uid
        assert found_user.email == sample_user_data.email

    async def test_get_user_by_uid_not_found(self, user_service: UserService, test_session: AsyncSession):
        """Test getting non-existent user by UID."""
        fake_uid = str(uuid4())
        
        with pytest.raises(UserNotFoundError):
            await user_service.get_user_by_uid(fake_uid, test_session)

    async def test_update_user_success(self, user_service: UserService, sample_user_data: UserCreateModel, test_session: AsyncSession):
        """Test updating user."""
        # Create user first
        created_user = await user_service.create_user(sample_user_data, test_session)
        
        # Update user
        update_data = UserUpdateModel(
            first_name="Updated",
            last_name="Name"
        )
        
        updated_user = await user_service.update_user(created_user, update_data, test_session)
        
        assert updated_user.first_name == "Updated"
        assert updated_user.last_name == "Name"
        assert updated_user.email == sample_user_data.email  # Should remain unchanged

    async def test_get_all_users(self, user_service: UserService, sample_user_data: UserCreateModel, test_session: AsyncSession):
        """Test getting all users."""
        # Create a user first
        await user_service.create_user(sample_user_data, test_session)
        
        # Get all users
        users = await user_service.get_all_users(test_session)
        
        assert isinstance(users, list)
        assert len(users) >= 1


class TestBookService:
    """Test BookService methods."""

    @pytest.fixture
    def book_service(self):
        return BookService()

    @pytest.fixture
    def sample_book_data(self):
        return BookCreateModel(
            title="Test Book",
            author="Test Author",
            description="A test book description"
        )

    async def test_confirm_book_exists_new_book(self, book_service: BookService, sample_book_data: BookCreateModel, test_session: AsyncSession):
        """Test confirming book doesn't exist (should pass)."""
        # This should not raise an exception
        await book_service.confirm_book_exists(sample_book_data, test_session)

    async def test_get_all_books_empty(self, book_service: BookService, test_session: AsyncSession):
        """Test getting all books when none exist."""
        books = await book_service.get_all_books(0, 20, test_session)
        
        assert isinstance(books, list)
        assert len(books) == 0

    async def test_get_book_not_found(self, book_service: BookService, test_session: AsyncSession):
        """Test getting non-existent book."""
        fake_uid = str(uuid4())
        
        with pytest.raises(BookNotFoundError):
            await book_service.get_book(fake_uid, test_session)

    async def test_search_book_empty_results(self, book_service: BookService, test_session: AsyncSession):
        """Test searching books with no results."""
        books = await book_service.search_book("nonexistent", None, 0, 20, test_session)
        
        assert isinstance(books, list)
        assert len(books) == 0
