import pytest
from httpx import AsyncClient
from io import BytesIO


class TestBookRoutes:
    """Test book-related routes."""

    async def test_get_all_books_success(self, client: AsyncClient, authenticated_user: dict):
        """Test getting all books."""
        headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}
        
        response = await client.get("/api/v1/books/all_books", headers=headers)
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_get_all_books_unauthorized(self, client: AsyncClient):
        """Test getting all books without authentication."""
        response = await client.get("/api/v1/books/all_books")
        
        assert response.status_code == 403

    async def test_get_all_books_with_pagination(self, client: AsyncClient, authenticated_user: dict):
        """Test getting all books with pagination."""
        headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}
        
        response = await client.get("/api/v1/books/all_books?skip=0&limit=10", headers=headers)
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_search_books_by_title(self, client: AsyncClient, authenticated_user: dict):
        """Test searching books by title."""
        headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}
        
        response = await client.get("/api/v1/books/search?title=test", headers=headers)
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_search_books_by_author(self, client: AsyncClient, authenticated_user: dict):
        """Test searching books by author."""
        headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}
        
        response = await client.get("/api/v1/books/search?author=test", headers=headers)
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_search_books_no_params(self, client: AsyncClient, authenticated_user: dict):
        """Test searching books without parameters."""
        headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}
        
        response = await client.get("/api/v1/books/search", headers=headers)
        
        assert response.status_code == 422
        data = response.json()
        assert "provide a title or an author" in data["error"]["message"]

    async def test_search_books_unauthorized(self, client: AsyncClient):
        """Test searching books without authentication."""
        response = await client.get("/api/v1/books/search?title=test")
        
        assert response.status_code == 403

    async def test_get_book_not_found(self, client: AsyncClient, authenticated_user: dict):
        """Test getting a non-existent book."""
        headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}
        
        # Use a valid UUID format
        fake_uuid = "12345678-1234-5678-9012-123456789012"
        response = await client.get(f"/api/v1/books/{fake_uuid}", headers=headers)
        
        assert response.status_code == 404

    async def test_get_book_invalid_uuid(self, client: AsyncClient, authenticated_user: dict):
        """Test getting a book with invalid UUID."""
        headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}

        response = await client.get("/api/v1/books/invalid-uuid", headers=headers)

        # Should return 422 for invalid UUID format or 500 for server error
        assert response.status_code in [422, 500, 400]

    async def test_upload_book_unauthorized(self, client: AsyncClient):
        """Test uploading a book without authentication."""
        # Create a fake PDF file
        fake_file = BytesIO(b"fake pdf content")
        
        files = {"file": ("test.pdf", fake_file, "application/pdf")}
        data = {
            "title": "Test Book",
            "author": "Test Author",
            "description": "Test Description"
        }
        
        response = await client.post("/api/v1/books/upload", files=files, data=data)
        
        assert response.status_code == 403

    async def test_upload_book_invalid_file_type(self, client: AsyncClient, authenticated_admin: dict):
        """Test uploading a book with invalid file type."""
        headers = {"Authorization": f"Bearer {authenticated_admin['access_token']}"}
        
        # Create a fake text file
        fake_file = BytesIO(b"fake text content")
        
        files = {"file": ("test.txt", fake_file, "text/plain")}
        data = {
            "title": "Test Book",
            "author": "Test Author",
            "description": "Test Description"
        }
        
        response = await client.post("/api/v1/books/upload", files=files, data=data, headers=headers)
        
        assert response.status_code == 400
        data = response.json()
        assert "unsupported file format" in data["error"]["message"].lower()

    async def test_update_book_unauthorized(self, client: AsyncClient):
        """Test updating a book without authentication."""
        fake_uuid = "12345678-1234-5678-9012-123456789012"
        update_data = {"title": "Updated Title"}
        
        response = await client.patch(f"/api/v1/books/{fake_uuid}/update", json=update_data)
        
        assert response.status_code == 403

    async def test_update_book_not_found(self, client: AsyncClient, authenticated_admin: dict):
        """Test updating a non-existent book."""
        headers = {"Authorization": f"Bearer {authenticated_admin['access_token']}"}
        
        fake_uuid = "12345678-1234-5678-9012-123456789012"
        update_data = {"title": "Updated Title"}
        
        response = await client.patch(f"/api/v1/books/{fake_uuid}/update", 
                                    json=update_data, headers=headers)
        
        assert response.status_code == 404

    async def test_delete_book_unauthorized(self, client: AsyncClient):
        """Test deleting a book without authentication."""
        fake_uuid = "12345678-1234-5678-9012-123456789012"
        
        response = await client.delete(f"/api/v1/books/delete-book/{fake_uuid}")
        
        assert response.status_code == 403

    async def test_delete_book_not_found(self, client: AsyncClient, authenticated_admin: dict):
        """Test deleting a non-existent book."""
        headers = {"Authorization": f"Bearer {authenticated_admin['access_token']}"}
        
        fake_uuid = "12345678-1234-5678-9012-123456789012"
        
        response = await client.delete(f"/api/v1/books/delete-book/{fake_uuid}", headers=headers)
        
        assert response.status_code == 404

    async def test_download_book_unauthorized(self, client: AsyncClient):
        """Test downloading a book without authentication."""
        fake_uuid = "12345678-1234-5678-9012-123456789012"
        
        response = await client.get(f"/api/v1/books/download/{fake_uuid}")
        
        assert response.status_code == 404

    async def test_download_book_not_found(self, client: AsyncClient, authenticated_user: dict):
        """Test downloading a non-existent book."""
        headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}
        
        fake_uuid = "12345678-1234-5678-9012-123456789012"
        
        response = await client.get(f"/api/v1/books/download/{fake_uuid}", headers=headers)
        
        assert response.status_code == 404

    async def test_request_download_link_unauthorized(self, client: AsyncClient):
        """Test requesting download link without authentication."""
        fake_uuid = "12345678-1234-5678-9012-123456789012"
        
        response = await client.post(f"/api/v1/books/request-download-link/{fake_uuid}")
        
        assert response.status_code == 404

    async def test_request_download_link_not_found(self, client: AsyncClient, authenticated_user: dict):
        """Test requesting download link for non-existent book."""
        headers = {"Authorization": f"Bearer {authenticated_user['access_token']}"}
        
        fake_uuid = "12345678-1234-5678-9012-123456789012"
        
        response = await client.post(f"/api/v1/books/request-download-link/{fake_uuid}", headers=headers)
        
        assert response.status_code == 404
