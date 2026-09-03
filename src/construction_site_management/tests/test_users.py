from app.models.users import UserModel
from fastapi.testclient import TestClient


class TestUserEndpoints:
    """Test suite for Users endpoints (/users/me, /users)."""

    def test_get_my_profile_admin_all_fields(
        self, client: TestClient, admin_headers: dict[str, str], admin_user: UserModel
    ):
        """Test GET /users/me with Admin credentials and check all returned fields."""
        response = client.get("/users/me", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == admin_user.id
        assert data["email"] == "admin@example.com"
        assert data["full_name"] == "Quản trị viên Hệ thống"
        assert data["role"] == "admin"
        assert data["is_active"] is True
        assert "password_hash" not in data

    def test_get_my_profile_user1_all_fields(
        self, client: TestClient, user1_headers: dict[str, str], user_1: UserModel
    ):
        """Test GET /users/me with User 1 credentials."""
        response = client.get("/users/me", headers=user1_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_1.id
        assert data["email"] == "nguyenvana@example.com"
        assert data["full_name"] == "Nguyễn Văn A"
        assert data["role"] == "user"
        assert data["is_active"] is True

    def test_get_my_profile_user2_all_fields(
        self, client: TestClient, user2_headers: dict[str, str], user_2: UserModel
    ):
        """Test GET /users/me with User 2 credentials."""
        response = client.get("/users/me", headers=user2_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == user_2.id
        assert data["email"] == "tranthib@example.com"
        assert data["full_name"] == "Trần Thị B"
        assert data["role"] == "user"
        assert data["is_active"] is True

    def test_get_my_profile_unauthenticated(self, client: TestClient):
        """Test GET /users/me without Authorization header fails."""
        response = client.get("/users/me")
        assert response.status_code in (401, 403)

    def test_get_my_profile_invalid_token(self, client: TestClient):
        """Test GET /users/me with invalid token."""
        response = client.get(
            "/users/me", headers={"Authorization": "Bearer invalid.token.value"}
        )
        assert response.status_code == 401

    def test_get_all_users_as_admin(
        self, client: TestClient, admin_headers: dict[str, str]
    ):
        """Test GET /users as admin returns all seeded users."""
        response = client.get("/users", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3
        emails = [u["email"] for u in data]
        assert "admin@example.com" in emails
        assert "nguyenvana@example.com" in emails
        assert "tranthib@example.com" in emails
        for u in data:
            assert "id" in u
            assert "email" in u
            assert "full_name" in u
            assert "role" in u
            assert "is_active" in u

    def test_get_all_users_forbidden_for_regular_user(
        self,
        client: TestClient,
        user1_headers: dict[str, str],
        user2_headers: dict[str, str],
    ):
        """Test GET /users is forbidden for non-admin users."""
        res1 = client.get("/users", headers=user1_headers)
        assert res1.status_code == 403
        assert res1.json()["error_code"] == "FORBIDDEN"

        res2 = client.get("/users", headers=user2_headers)
        assert res2.status_code == 403

    def test_get_all_users_filter_by_user_id(
        self, client: TestClient, admin_headers: dict[str, str], user_1: UserModel
    ):
        """Test GET /users with user_id query parameter."""
        response = client.get(f"/users?user_id={user_1.id}", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == user_1.id
        assert data[0]["email"] == "nguyenvana@example.com"

    def test_get_all_users_filter_by_nonexistent_user_id(
        self, client: TestClient, admin_headers: dict[str, str]
    ):
        """Test GET /users with non-existent user_id."""
        response = client.get("/users?user_id=99999", headers=admin_headers)
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "BAD_REQUEST"
        assert "User not found" in data["message"]

    def test_get_all_users_search_filter(
        self, client: TestClient, admin_headers: dict[str, str]
    ):
        """Test GET /users with search parameter (name or email)."""
        # Search by name
        res1 = client.get("/users?search=Văn A", headers=admin_headers)
        assert res1.status_code == 200
        data1 = res1.json()
        assert len(data1) == 1
        assert data1[0]["full_name"] == "Nguyễn Văn A"

        # Search by email
        res2 = client.get("/users?search=tranthib", headers=admin_headers)
        assert res2.status_code == 200
        data2 = res2.json()
        assert len(data2) == 1
        assert data2[0]["email"] == "tranthib@example.com"

    def test_get_all_users_is_active_filter(
        self, client: TestClient, admin_headers: dict[str, str]
    ):
        """Test GET /users with is_active filter."""
        response = client.get("/users?is_active=true", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3
        for user in data:
            assert user["is_active"] is True

    def test_get_all_users_pagination_skip_limit(
        self, client: TestClient, admin_headers: dict[str, str]
    ):
        """Test GET /users with skip and limit pagination."""
        response = client.get("/users?skip=0&limit=2", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        response_skip = client.get("/users?skip=2&limit=2", headers=admin_headers)
        assert response_skip.status_code == 200
        data_skip = response_skip.json()
        assert len(data_skip) >= 1
        # Should not overlap with first 2
        assert data[0]["id"] != data_skip[0]["id"]

    def test_get_all_users_pagination_page_size(
        self, client: TestClient, admin_headers: dict[str, str]
    ):
        """Test GET /users with page and size pagination."""
        res_page1 = client.get("/users?page=1&size=2", headers=admin_headers)
        assert res_page1.status_code == 200
        data_p1 = res_page1.json()
        assert len(data_p1) == 2

        res_page2 = client.get("/users?page=2&size=2", headers=admin_headers)
        assert res_page2.status_code == 200
        data_p2 = res_page2.json()
        assert len(data_p2) >= 1
        assert data_p1[0]["id"] != data_p2[0]["id"]
