from app.models.sites import ConstructionSiteModel
from fastapi.testclient import TestClient


class TestActivityLogEndpoints:
    """Test suite for Activity Log endpoints (/construction-sites/{site_id}/activity-logs)."""

    def test_get_activity_logs_as_member_all_fields(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        site_1: ConstructionSiteModel,
    ):
        """Test GET /construction-sites/{site_id}/activity-logs returns logs with all expected fields."""
        # Perform an action that logs activity: update site
        client.patch(
            f"/construction-sites/{site_1.id}",
            json={"name": "Tên mới để tạo log"},
            headers=admin_headers,
        )

        response = client.get(
            f"/construction-sites/{site_1.id}/activity-logs",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        for log in data:
            assert "id" in log
            assert log["site_id"] == site_1.id
            assert "user_id" in log
            assert "action" in log
            assert "details" in log
            assert "created_at" in log

    def test_get_activity_logs_non_member_forbidden(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        site_2: ConstructionSiteModel,
    ):
        """Test GET /construction-sites/{site_id}/activity-logs as non-member is forbidden."""
        # Admin is not a member of site 2
        response = client.get(
            f"/construction-sites/{site_2.id}/activity-logs",
            headers=admin_headers,
        )
        assert response.status_code == 403
        assert response.json()["error_code"] == "FORBIDDEN"

    def test_get_activity_logs_nonexistent_site_not_found(
        self, client: TestClient, admin_headers: dict[str, str]
    ):
        """Test GET /construction-sites/{site_id}/activity-logs for non-existent site returns 404."""
        response = client.get(
            "/construction-sites/99999/activity-logs", headers=admin_headers
        )
        assert response.status_code == 404
        assert response.json()["error_code"] == "NOT_FOUND"

    def test_get_activity_logs_pagination(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        site_1: ConstructionSiteModel,
    ):
        """Test GET /construction-sites/{site_id}/activity-logs pagination with skip and limit."""
        # Generate multiple activity logs
        client.patch(
            f"/construction-sites/{site_1.id}",
            json={"description": "Mô tả 1"},
            headers=admin_headers,
        )
        client.patch(
            f"/construction-sites/{site_1.id}",
            json={"description": "Mô tả 2"},
            headers=admin_headers,
        )

        response = client.get(
            f"/construction-sites/{site_1.id}/activity-logs?skip=0&limit=1",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
