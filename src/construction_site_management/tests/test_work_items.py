from datetime import UTC, datetime, timedelta

from app.models.sites import ConstructionSiteModel
from app.models.users import UserModel
from app.models.work_items import WorkItemModel
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestWorkItemEndpoints:
    """Test suite for Work Items endpoints (/construction-sites/{site_id}/work-items and /work-items/{item_id})."""

    def test_create_work_item_success_all_fields(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        site_1: ConstructionSiteModel,
        user_1: UserModel,
    ):
        """Test POST /construction-sites/{site_id}/work-items with all fields provided."""
        due_date = (datetime.now(UTC) + timedelta(days=10)).isoformat()
        payload = {
            "title": "Lắp đặt hệ thống cấp thoát nước",
            "description": "Lắp đặt ống nước và phụ kiện cho toàn bộ tầng hầm",
            "assignee_id": user_1.id,
            "status": "TODO",
            "priority": "HIGH",
            "due_date": due_date,
        }
        response = client.post(
            f"/construction-sites/{site_1.id}/work-items",
            json=payload,
            headers=admin_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["site_id"] == site_1.id
        assert data["title"] == payload["title"]
        assert data["description"] == payload["description"]
        assert data["assignee_id"] == user_1.id
        assert data["status"] == "TODO"
        assert data["priority"] == "HIGH"
        assert data["due_date"] is not None
        assert "created_at" in data

    def test_create_work_item_minimal_fields(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        site_1: ConstructionSiteModel,
    ):
        """Test POST /construction-sites/{site_id}/work-items with only required title."""
        payload = {"title": "Hạng mục tối thiểu"}
        response = client.post(
            f"/construction-sites/{site_1.id}/work-items",
            json=payload,
            headers=admin_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Hạng mục tối thiểu"
        assert data["description"] is None
        assert data["assignee_id"] is None
        assert data["status"] == "TODO"
        assert data["priority"] == "MEDIUM"

    def test_create_work_item_assignee_not_member_error(
        self,
        client: TestClient,
        user1_headers: dict[str, str],
        site_2: ConstructionSiteModel,
        admin_user: UserModel,
    ):
        """Test creating work item with assignee who is not a site member returns 400."""
        # admin is not a member of site 2
        payload = {
            "title": "Công việc cho người ngoài",
            "assignee_id": admin_user.id,
        }
        response = client.post(
            f"/construction-sites/{site_2.id}/work-items",
            json=payload,
            headers=user1_headers,
        )
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "BAD_REQUEST"
        assert "Assignee must be a member" in data["message"]

    def test_create_work_item_non_member_forbidden(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        site_2: ConstructionSiteModel,
    ):
        """Test creating work item by non-member of site returns 403."""
        payload = {"title": "Tạo việc trái phép"}
        response = client.post(
            f"/construction-sites/{site_2.id}/work-items",
            json=payload,
            headers=admin_headers,
        )
        assert response.status_code == 403
        assert response.json()["error_code"] == "FORBIDDEN"

    def test_get_work_items_for_site_all_fields(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        site_1: ConstructionSiteModel,
    ):
        """Test GET /construction-sites/{site_id}/work-items returns all seeded work items."""
        response = client.get(
            f"/construction-sites/{site_1.id}/work-items",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
        titles = [item["title"] for item in data]
        assert "Đào móng tòa nhà" in titles
        assert "Đổ bê tông sàn tầng 1" in titles
        for item in data:
            assert "id" in item
            assert item["site_id"] == site_1.id
            assert "title" in item
            assert "status" in item
            assert "priority" in item
            assert "created_at" in item

    def test_get_work_items_filter_by_status(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        site_1: ConstructionSiteModel,
    ):
        """Test filtering work items by status (TODO, IN_PROGRESS, DONE)."""
        res_in_prog = client.get(
            f"/construction-sites/{site_1.id}/work-items?status=IN_PROGRESS",
            headers=admin_headers,
        )
        assert res_in_prog.status_code == 200
        items_ip = res_in_prog.json()
        assert len(items_ip) == 1
        assert items_ip[0]["title"] == "Đào móng tòa nhà"
        assert items_ip[0]["status"] == "IN_PROGRESS"

        res_todo = client.get(
            f"/construction-sites/{site_1.id}/work-items?status=TODO",
            headers=admin_headers,
        )
        assert res_todo.status_code == 200
        items_todo = res_todo.json()
        assert len(items_todo) == 1
        assert items_todo[0]["title"] == "Đổ bê tông sàn tầng 1"

    def test_get_work_items_filter_by_priority(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        site_1: ConstructionSiteModel,
    ):
        """Test filtering work items by priority."""
        response = client.get(
            f"/construction-sites/{site_1.id}/work-items?priority=HIGH",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Đào móng tòa nhà"

    def test_get_work_items_filter_by_assignee(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        site_1: ConstructionSiteModel,
        user_1: UserModel,
    ):
        """Test filtering work items by assignee_id."""
        response = client.get(
            f"/construction-sites/{site_1.id}/work-items?assignee_id={user_1.id}",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["assignee_id"] == user_1.id

    def test_get_work_items_search_filter(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        site_1: ConstructionSiteModel,
    ):
        """Test searching work items by title."""
        response = client.get(
            f"/construction-sites/{site_1.id}/work-items?search=bê tông",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Đổ bê tông sàn tầng 1"

    def test_get_work_items_sorting_and_pagination(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        site_1: ConstructionSiteModel,
    ):
        """Test sorting and pagination of work items."""
        # Sort by title asc
        res_sort = client.get(
            f"/construction-sites/{site_1.id}/work-items?sort_by=title&order=asc",
            headers=admin_headers,
        )
        assert res_sort.status_code == 200
        data = res_sort.json()
        assert len(data) >= 2
        assert data[0]["title"] <= data[1]["title"]

        # Pagination
        res_page = client.get(
            f"/construction-sites/{site_1.id}/work-items?page=1&size=1",
            headers=admin_headers,
        )
        assert res_page.status_code == 200
        assert len(res_page.json()) == 1

    def test_get_work_items_invalid_sort_error(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        site_1: ConstructionSiteModel,
    ):
        """Test invalid sort_by field returns 400."""
        response = client.get(
            f"/construction-sites/{site_1.id}/work-items?sort_by=invalid_field",
            headers=admin_headers,
        )
        assert response.status_code == 400
        assert response.json()["error_code"] == "BAD_REQUEST"

    def test_get_work_item_by_id_success_all_fields(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        work_item_1: WorkItemModel,
        site_1: ConstructionSiteModel,
        user_1: UserModel,
    ):
        """Test GET /work-items/{item_id} returns all fields."""
        response = client.get(f"/work-items/{work_item_1.id}", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == work_item_1.id
        assert data["site_id"] == site_1.id
        assert data["title"] == "Đào móng tòa nhà"
        assert "Thi công đào móng" in data["description"]
        assert data["assignee_id"] == user_1.id
        assert data["status"] == "IN_PROGRESS"
        assert data["priority"] == "HIGH"
        assert "due_date" in data
        assert "created_at" in data

    def test_get_work_item_by_id_non_member_forbidden(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        work_item_3: WorkItemModel,
    ):
        """Test GET /work-items/{item_id} by non-member of the site returns 403."""
        # work_item_3 is in site 2, admin is not a member of site 2
        response = client.get(f"/work-items/{work_item_3.id}", headers=admin_headers)
        assert response.status_code == 403
        assert response.json()["error_code"] == "FORBIDDEN"

    def test_get_work_item_nonexistent_not_found(
        self, client: TestClient, admin_headers: dict[str, str]
    ):
        """Test GET /work-items/{item_id} with non-existent ID returns 404."""
        response = client.get("/work-items/99999", headers=admin_headers)
        assert response.status_code == 404
        assert response.json()["error_code"] == "NOT_FOUND"

    def test_update_work_item_as_owner_all_fields(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        work_item_1: WorkItemModel,
        user_2: UserModel,
    ):
        """Test PATCH /work-items/{item_id} as OWNER updating all fields."""
        new_due = (datetime.now(UTC) + timedelta(days=20)).isoformat()
        payload = {
            "title": "Đào móng và ép cọc",
            "description": "Cập nhật mô tả chi tiết hơn",
            "assignee_id": user_2.id,
            "status": "DONE",
            "priority": "LOW",
            "due_date": new_due,
        }
        response = client.patch(
            f"/work-items/{work_item_1.id}",
            json=payload,
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == payload["title"]
        assert data["description"] == payload["description"]
        assert data["assignee_id"] == user_2.id
        assert data["status"] == "DONE"
        assert data["priority"] == "LOW"

    def test_update_work_item_as_assignee_member_status_only(
        self,
        client: TestClient,
        user1_headers: dict[str, str],
        work_item_1: WorkItemModel,
    ):
        """Test PATCH /work-items/{item_id} as MEMBER (who is assignee) can update status."""
        # work_item_1 is assigned to user_1
        payload = {"status": "DONE"}
        response = client.patch(
            f"/work-items/{work_item_1.id}",
            json=payload,
            headers=user1_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "DONE"

    def test_update_work_item_as_assignee_member_disallowed_fields_forbidden(
        self,
        client: TestClient,
        user1_headers: dict[str, str],
        work_item_1: WorkItemModel,
    ):
        """Test PATCH /work-items/{item_id} as MEMBER (assignee) updating non-status fields is forbidden."""
        payload = {"title": "Cố gắng sửa tiêu đề"}
        response = client.patch(
            f"/work-items/{work_item_1.id}",
            json=payload,
            headers=user1_headers,
        )
        assert response.status_code == 403
        data = response.json()
        assert data["error_code"] == "FORBIDDEN"
        assert "only permitted to update work item status" in data["message"]

    def test_update_work_item_as_non_assignee_member_forbidden(
        self,
        client: TestClient,
        user2_headers: dict[str, str],
        work_item_1: WorkItemModel,
    ):
        """Test PATCH /work-items/{item_id} as MEMBER who is NOT assignee is forbidden."""
        # work_item_1 is assigned to user_1, user_2 is just a member
        payload = {"status": "DONE"}
        response = client.patch(
            f"/work-items/{work_item_1.id}",
            json=payload,
            headers=user2_headers,
        )
        assert response.status_code == 403
        assert response.json()["error_code"] == "FORBIDDEN"

    def test_delete_work_item_as_owner_success(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        work_item_1: WorkItemModel,
        db_session: Session,
    ):
        """Test DELETE /work-items/{item_id} as OWNER deletes the item."""
        response = client.delete(f"/work-items/{work_item_1.id}", headers=admin_headers)
        assert response.status_code == 204

        # Subsequent GET should return 404
        get_res = client.get(f"/work-items/{work_item_1.id}", headers=admin_headers)
        assert get_res.status_code == 404

    def test_delete_work_item_as_member_forbidden(
        self,
        client: TestClient,
        user1_headers: dict[str, str],
        work_item_1: WorkItemModel,
    ):
        """Test DELETE /work-items/{item_id} as MEMBER (non-owner) is forbidden."""
        response = client.delete(f"/work-items/{work_item_1.id}", headers=user1_headers)
        assert response.status_code == 403
        assert response.json()["error_code"] == "FORBIDDEN"
