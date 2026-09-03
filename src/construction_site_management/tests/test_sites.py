from app.models.sites import ConstructionSiteModel, RoleSiteMemberEnum, SiteMemberModel
from app.models.users import UserModel
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestConstructionSiteEndpoints:
    """Test suite for /construction-sites endpoints."""

    def test_create_construction_site_success_all_fields(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        admin_user: UserModel,
        db_session: Session,
    ):
        """Test POST /construction-sites with all fields and check automatic OWNER member assignment."""
        payload = {
            "name": "Khu căn hộ Sky Garden",
            "description": "Dự án căn hộ chung cư cao cấp 25 tầng",
        }
        response = client.post(
            "/construction-sites", json=payload, headers=admin_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["name"] == payload["name"]
        assert data["description"] == payload["description"]
        assert data["owner_id"] == admin_user.id

        # Verify owner membership was created
        site_id = data["id"]
        member = (
            db_session.query(SiteMemberModel)
            .filter_by(site_id=site_id, user_id=admin_user.id)
            .first()
        )
        assert member is not None
        assert member.role == RoleSiteMemberEnum.OWNER

    def test_create_construction_site_minimal_fields(
        self, client: TestClient, user1_headers: dict[str, str], user_1: UserModel
    ):
        """Test POST /construction-sites with description omitted."""
        payload = {"name": "Công trình không mô tả"}
        response = client.post(
            "/construction-sites", json=payload, headers=user1_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Công trình không mô tả"
        assert data["description"] is None
        assert data["owner_id"] == user_1.id

    def test_create_construction_site_validation_error(
        self, client: TestClient, admin_headers: dict[str, str]
    ):
        """Test POST /construction-sites with empty name fails validation."""
        response = client.post(
            "/construction-sites", json={"name": ""}, headers=admin_headers
        )
        assert response.status_code == 422

    def test_create_construction_site_unauthenticated(self, client: TestClient):
        """Test POST /construction-sites without auth fails."""
        response = client.post("/construction-sites", json={"name": "Dự án ẩn danh"})
        assert response.status_code in (401, 403)

    def test_get_all_construction_sites_for_user1(
        self, client: TestClient, user1_headers: dict[str, str]
    ):
        """Test GET /construction-sites as User 1 (Member of site 1, Owner of site 2)."""
        response = client.get("/construction-sites", headers=user1_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        site_names = [s["name"] for s in data]
        assert "Tòa nhà văn phòng Hưng Phát" in site_names
        assert "Khu dân cư Green City" in site_names
        for site in data:
            assert "id" in site
            assert "name" in site
            assert "description" in site
            assert "owner_id" in site

    def test_get_all_construction_sites_search_filter(
        self, client: TestClient, user1_headers: dict[str, str]
    ):
        """Test GET /construction-sites with search query."""
        response = client.get(
            "/construction-sites?search=Hưng Phát", headers=user1_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Tòa nhà văn phòng Hưng Phát"

    def test_get_all_construction_sites_pagination(
        self, client: TestClient, user1_headers: dict[str, str]
    ):
        """Test GET /construction-sites pagination."""
        # Skip & limit
        res_skip = client.get(
            "/construction-sites?skip=0&limit=1", headers=user1_headers
        )
        assert res_skip.status_code == 200
        assert len(res_skip.json()) == 1

        # Page & size
        res_page = client.get(
            "/construction-sites?page=1&size=1", headers=user1_headers
        )
        assert res_page.status_code == 200
        assert len(res_page.json()) == 1

    def test_get_construction_site_by_id_success(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        site_1: ConstructionSiteModel,
    ):
        """Test GET /construction-sites/{site_id} as owner/member returns all fields."""
        response = client.get(f"/construction-sites/{site_1.id}", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == site_1.id
        assert data["name"] == "Tòa nhà văn phòng Hưng Phát"
        assert (
            data["description"]
            == "Dự án xây dựng tòa nhà văn phòng 15 tầng tại Quận 1, TP.HCM"
        )
        assert data["owner_id"] == site_1.owner_id

    def test_get_construction_site_by_id_non_member_forbidden(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        site_2: ConstructionSiteModel,
    ):
        """Test GET /construction-sites/{site_id} for a non-member returns 403."""
        # admin is not a member of site 2 in seed data
        response = client.get(f"/construction-sites/{site_2.id}", headers=admin_headers)
        assert response.status_code == 403
        data = response.json()
        assert data["error_code"] == "FORBIDDEN"

    def test_get_construction_site_by_id_not_found(
        self, client: TestClient, admin_headers: dict[str, str]
    ):
        """Test GET /construction-sites/{site_id} for non-existent site returns 404."""
        response = client.get("/construction-sites/99999", headers=admin_headers)
        assert response.status_code == 404
        assert response.json()["error_code"] == "NOT_FOUND"

    def test_update_construction_site_as_owner_all_fields(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        site_1: ConstructionSiteModel,
    ):
        """Test PATCH /construction-sites/{site_id} as OWNER updating all fields."""
        payload = {
            "name": "Tòa nhà văn phòng Hưng Phát - Cập nhật",
            "description": "Mô tả mới sau khi điều chỉnh thiết kế",
        }
        response = client.patch(
            f"/construction-sites/{site_1.id}",
            json=payload,
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == payload["name"]
        assert data["description"] == payload["description"]

    def test_update_construction_site_as_member_forbidden(
        self,
        client: TestClient,
        user1_headers: dict[str, str],
        site_1: ConstructionSiteModel,
    ):
        """Test PATCH /construction-sites/{site_id} as MEMBER (not owner) is forbidden."""
        payload = {"name": "Đổi tên bất hợp pháp"}
        response = client.patch(
            f"/construction-sites/{site_1.id}",
            json=payload,
            headers=user1_headers,
        )
        assert response.status_code == 403
        assert response.json()["error_code"] == "FORBIDDEN"

    def test_delete_construction_site_as_owner_soft_delete(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        site_1: ConstructionSiteModel,
        db_session: Session,
    ):
        """Test DELETE /construction-sites/{site_id} as OWNER performs soft delete."""
        response = client.delete(
            f"/construction-sites/{site_1.id}", headers=admin_headers
        )
        assert response.status_code == 204

        # Verify soft deleted in DB
        db_session.expire_all()
        db_site = (
            db_session.query(ConstructionSiteModel).filter_by(id=site_1.id).first()
        )
        assert db_site.is_deleted is True
        assert db_site.deleted_at is not None

        # Subsequent GET should return 404
        get_res = client.get(f"/construction-sites/{site_1.id}", headers=admin_headers)
        assert get_res.status_code == 404

    def test_delete_construction_site_as_member_forbidden(
        self,
        client: TestClient,
        user1_headers: dict[str, str],
        site_1: ConstructionSiteModel,
    ):
        """Test DELETE /construction-sites/{site_id} as MEMBER (non-owner) is forbidden."""
        response = client.delete(
            f"/construction-sites/{site_1.id}", headers=user1_headers
        )
        assert response.status_code == 403
        assert response.json()["error_code"] == "FORBIDDEN"
