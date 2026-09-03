from app.models.sites import ConstructionSiteModel, SiteMemberModel
from app.models.users import UserModel
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestSiteMemberEndpoints:
    """Test suite for Site Member endpoints (/construction-sites/{site_id}/members)."""

    def test_add_member_as_owner_success_all_fields(
        self,
        client: TestClient,
        user1_headers: dict[str, str],
        site_2: ConstructionSiteModel,
        admin_user: UserModel,
    ):
        """Test POST /construction-sites/{site_id}/members as OWNER adding a new member."""
        # On site 2, user_1 is OWNER. We add admin_user as MEMBER.
        payload = {
            "site_id": site_2.id,
            "user_id": admin_user.id,
            "role": "member",
        }
        response = client.post(
            f"/construction-sites/{site_2.id}/members",
            json=payload,
            headers=user1_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["site_id"] == site_2.id
        assert data["user_id"] == admin_user.id
        assert data["role"] == "member"
        assert "joined_at" in data

    def test_add_existing_member_error(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        site_1: ConstructionSiteModel,
        user_1: UserModel,
    ):
        """Test adding a user who is already a member fails with 400."""
        payload = {
            "site_id": site_1.id,
            "user_id": user_1.id,
            "role": "member",
        }
        response = client.post(
            f"/construction-sites/{site_1.id}/members",
            json=payload,
            headers=admin_headers,
        )
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "BAD_REQUEST"
        assert "already a member" in data["message"]

    def test_add_member_nonexistent_user_error(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        site_1: ConstructionSiteModel,
    ):
        """Test adding a non-existent user_id fails with 404."""
        payload = {
            "site_id": site_1.id,
            "user_id": 99999,
            "role": "member",
        }
        response = client.post(
            f"/construction-sites/{site_1.id}/members",
            json=payload,
            headers=admin_headers,
        )
        assert response.status_code == 404
        data = response.json()
        assert data["error_code"] == "NOT_FOUND"

    def test_add_member_as_non_owner_forbidden(
        self,
        client: TestClient,
        user1_headers: dict[str, str],
        site_1: ConstructionSiteModel,
        admin_user: UserModel,
    ):
        """Test adding a member as MEMBER (not owner) is forbidden."""
        payload = {
            "site_id": site_1.id,
            "user_id": admin_user.id,
            "role": "member",
        }
        response = client.post(
            f"/construction-sites/{site_1.id}/members",
            json=payload,
            headers=user1_headers,
        )
        assert response.status_code == 403
        assert response.json()["error_code"] == "FORBIDDEN"

    def test_get_members_as_site_member_all_fields(
        self,
        client: TestClient,
        user1_headers: dict[str, str],
        site_1: ConstructionSiteModel,
    ):
        """Test GET /construction-sites/{site_id}/members lists all members with fields."""
        response = client.get(
            f"/construction-sites/{site_1.id}/members", headers=user1_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3  # admin (owner), user1 (member), user2 (member)
        roles = {m["user_id"]: m["role"] for m in data}
        assert "owner" in roles.values()
        assert "member" in roles.values()
        for m in data:
            assert m["site_id"] == site_1.id
            assert "user_id" in m
            assert "role" in m
            assert "joined_at" in m

    def test_get_members_non_member_forbidden(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        site_2: ConstructionSiteModel,
    ):
        """Test GET /construction-sites/{site_id}/members by non-member returns 403."""
        # admin is not a member of site 2
        response = client.get(
            f"/construction-sites/{site_2.id}/members", headers=admin_headers
        )
        assert response.status_code == 403
        assert response.json()["error_code"] == "FORBIDDEN"

    def test_remove_member_as_owner_success(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        site_1: ConstructionSiteModel,
        user_2: UserModel,
        db_session: Session,
    ):
        """Test DELETE /construction-sites/{site_id}/members/{user_id} as OWNER."""
        response = client.delete(
            f"/construction-sites/{site_1.id}/members/{user_2.id}",
            headers=admin_headers,
        )
        assert response.status_code == 204

        # Verify member removed from DB
        db_session.expire_all()
        member = (
            db_session.query(SiteMemberModel)
            .filter_by(site_id=site_1.id, user_id=user_2.id)
            .first()
        )
        assert member is None

    def test_remove_owner_from_site_error(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        site_1: ConstructionSiteModel,
        admin_user: UserModel,
    ):
        """Test removing the OWNER from the site fails with 400."""
        response = client.delete(
            f"/construction-sites/{site_1.id}/members/{admin_user.id}",
            headers=admin_headers,
        )
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "BAD_REQUEST"
        assert "Cannot remove the owner" in data["message"]

    def test_remove_nonexistent_member_error(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        site_1: ConstructionSiteModel,
    ):
        """Test removing a non-member from the site fails with 404."""
        response = client.delete(
            f"/construction-sites/{site_1.id}/members/99999",
            headers=admin_headers,
        )
        assert response.status_code == 404
        assert response.json()["error_code"] == "NOT_FOUND"

    def test_remove_member_as_non_owner_forbidden(
        self,
        client: TestClient,
        user1_headers: dict[str, str],
        site_1: ConstructionSiteModel,
        user_2: UserModel,
    ):
        """Test removing a member as non-owner (MEMBER) is forbidden."""
        response = client.delete(
            f"/construction-sites/{site_1.id}/members/{user_2.id}",
            headers=user1_headers,
        )
        assert response.status_code == 403
        assert response.json()["error_code"] == "FORBIDDEN"
