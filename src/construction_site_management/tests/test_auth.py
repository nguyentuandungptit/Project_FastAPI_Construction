from datetime import timedelta

from app.core.security import create_access_token, create_refresh_token
from fastapi.testclient import TestClient


class TestAuthEndpoints:
    """Test suite for Auth endpoints (/auth/register, /auth/login, /auth/refresh)."""

    def test_register_success_all_fields(self, client: TestClient):
        """Test user registration with all required fields."""
        payload = {
            "email": "lethic@example.com",
            "full_name": "Lê Thị C",
            "password": "Password@123",
        }
        response = client.post("/auth/register", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert isinstance(data["id"], int)
        assert data["email"] == payload["email"]
        assert data["full_name"] == payload["full_name"]
        assert data["role"] == "user"
        assert data["is_active"] is True

    def test_register_duplicate_email_error(self, client: TestClient):
        """Test registration failure when email already exists (using seed data)."""
        payload = {
            "email": "admin@example.com",
            "full_name": "Quản trị viên Trùng",
            "password": "Password@123",
        }
        response = client.post("/auth/register", json=payload)
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "BAD_REQUEST"
        assert "Email already exists" in data["message"]

    def test_register_invalid_password_validation(self, client: TestClient):
        """Test registration validation errors for weak passwords."""
        # Missing uppercase
        res1 = client.post(
            "/auth/register",
            json={
                "email": "test1@example.com",
                "full_name": "Test User",
                "password": "password@123",
            },
        )
        assert res1.status_code == 422

        # Missing special char
        res2 = client.post(
            "/auth/register",
            json={
                "email": "test2@example.com",
                "full_name": "Test User",
                "password": "Password123",
            },
        )
        assert res2.status_code == 422

        # Missing digit
        res3 = client.post(
            "/auth/register",
            json={
                "email": "test3@example.com",
                "full_name": "Test User",
                "password": "Password@abc",
            },
        )
        assert res3.status_code == 422

        # Too short (< 8 chars)
        res4 = client.post(
            "/auth/register",
            json={
                "email": "test4@example.com",
                "full_name": "Test User",
                "password": "Aa1@",
            },
        )
        assert res4.status_code == 422

    def test_register_missing_fields(self, client: TestClient):
        """Test registration failure when required fields are missing."""
        # Missing email
        res1 = client.post(
            "/auth/register",
            json={"full_name": "Test User", "password": "Password@123"},
        )
        assert res1.status_code == 422

        # Missing full_name
        res2 = client.post(
            "/auth/register",
            json={"email": "missing_name@example.com", "password": "Password@123"},
        )
        assert res2.status_code == 422

        # Missing password
        res3 = client.post(
            "/auth/register",
            json={"email": "missing_pwd@example.com", "full_name": "Test User"},
        )
        assert res3.status_code == 422

    def test_login_admin_success(self, client: TestClient):
        """Test login with admin account from seed data."""
        payload = {"email": "admin@example.com", "password": "Admin@123"}
        response = client.post("/auth/login", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0
        assert len(data["refresh_token"]) > 0

    def test_login_user1_success(self, client: TestClient):
        """Test login with user 1 account from seed data."""
        payload = {"email": "nguyenvana@example.com", "password": "User@123"}
        response = client.post("/auth/login", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_user2_success(self, client: TestClient):
        """Test login with user 2 account from seed data."""
        payload = {"email": "tranthib@example.com", "password": "User@123"}
        response = client.post("/auth/login", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password_error(self, client: TestClient):
        """Test login with invalid password."""
        payload = {"email": "admin@example.com", "password": "WrongPassword@123"}
        response = client.post("/auth/login", json=payload)
        assert response.status_code == 401
        data = response.json()
        assert data["error_code"] == "UNAUTHORIZED"
        assert "Invalid password" in data["message"]

    def test_login_nonexistent_email_error(self, client: TestClient):
        """Test login with non-existent email."""
        payload = {"email": "nonexistent@example.com", "password": "Password@123"}
        response = client.post("/auth/login", json=payload)
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "BAD_REQUEST"
        assert "Email not found" in data["message"]

    def test_login_missing_fields_validation(self, client: TestClient):
        """Test login with missing required fields."""
        res1 = client.post("/auth/login", json={"email": "admin@example.com"})
        assert res1.status_code == 422

        res2 = client.post("/auth/login", json={"password": "Admin@123"})
        assert res2.status_code == 422

    def test_refresh_token_success(self, client: TestClient, admin_user):
        """Test refreshing token with a valid refresh token."""
        valid_refresh_token = create_refresh_token({"sub": str(admin_user.id)})
        response = client.post(
            "/auth/refresh", json={"refresh_token": valid_refresh_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_refresh_token_with_access_token_fails(
        self, client: TestClient, admin_user
    ):
        """Test that sending an access token as refresh token fails (wrong token type)."""
        access_tok = create_access_token({"sub": str(admin_user.id)})
        response = client.post("/auth/refresh", json={"refresh_token": access_tok})
        assert response.status_code == 401

    def test_refresh_token_invalid_string_fails(self, client: TestClient):
        """Test refresh token with a malformed/invalid token string."""
        response = client.post(
            "/auth/refresh", json={"refresh_token": "invalid.jwt.token.string"}
        )
        assert response.status_code == 401

    def test_refresh_token_expired_fails(self, client: TestClient, admin_user):
        """Test refresh token with an expired token."""
        expired_token = create_refresh_token(
            {"sub": str(admin_user.id)}, expires_delta=timedelta(seconds=-10)
        )
        response = client.post("/auth/refresh", json={"refresh_token": expired_token})
        assert response.status_code == 401
