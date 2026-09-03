import io
import os
import shutil

from app.models.users import UserModel
from app.models.work_items import WorkItemModel
from fastapi.testclient import TestClient


class TestWorkItemInteractionsEndpoints:
    """Test suite for Work Item Comments and Attachments endpoints."""

    def test_create_work_item_comment_success_all_fields(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        admin_user: UserModel,
        work_item_1: WorkItemModel,
    ):
        """Test POST /work-items/{item_id}/comments creates a comment with all response fields."""
        payload = {"content": "Đã hoàn thành 50% khối lượng đào móng tầng hầm."}
        response = client.post(
            f"/work-items/{work_item_1.id}/comments",
            json=payload,
            headers=admin_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["work_item_id"] == work_item_1.id
        assert data["user_id"] == admin_user.id
        assert data["content"] == payload["content"]
        assert "created_at" in data

    def test_create_work_item_comment_validation_empty_content(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        work_item_1: WorkItemModel,
    ):
        """Test creating comment with empty content fails validation."""
        response = client.post(
            f"/work-items/{work_item_1.id}/comments",
            json={"content": ""},
            headers=admin_headers,
        )
        assert response.status_code == 422

    def test_create_work_item_comment_non_member_forbidden(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        work_item_3: WorkItemModel,
    ):
        """Test adding comment on work item from a site user is not a member of is forbidden."""
        # work_item_3 belongs to site 2, admin is not a member of site 2
        payload = {"content": "Bình luận không được phép"}
        response = client.post(
            f"/work-items/{work_item_3.id}/comments",
            json=payload,
            headers=admin_headers,
        )
        assert response.status_code == 403
        assert response.json()["error_code"] == "FORBIDDEN"

    def test_get_work_item_comments_success_and_pagination(
        self,
        client: TestClient,
        user1_headers: dict[str, str],
        work_item_1: WorkItemModel,
    ):
        """Test GET /work-items/{item_id}/comments lists comments with fields and pagination."""
        # Add 2 comments
        client.post(
            f"/work-items/{work_item_1.id}/comments",
            json={"content": "Ghi chú tiến độ 1"},
            headers=user1_headers,
        )
        client.post(
            f"/work-items/{work_item_1.id}/comments",
            json={"content": "Ghi chú tiến độ 2"},
            headers=user1_headers,
        )

        response = client.get(
            f"/work-items/{work_item_1.id}/comments",
            headers=user1_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
        for comment in data:
            assert "id" in comment
            assert comment["work_item_id"] == work_item_1.id
            assert "user_id" in comment
            assert "content" in comment
            assert "created_at" in comment

        # Pagination test
        res_skip = client.get(
            f"/work-items/{work_item_1.id}/comments?skip=0&limit=1",
            headers=user1_headers,
        )
        assert res_skip.status_code == 200
        assert len(res_skip.json()) == 1

    def test_upload_work_item_attachment_png_success_all_fields(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        admin_user: UserModel,
        work_item_1: WorkItemModel,
    ):
        """Test POST /work-items/{item_id}/attachments uploads valid PNG image."""
        file_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
        file_tuple = ("test_image.png", io.BytesIO(file_content), "image/png")

        response = client.post(
            f"/work-items/{work_item_1.id}/attachments",
            files={"file": file_tuple},
            headers=admin_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["work_item_id"] == work_item_1.id
        assert data["uploader_id"] == admin_user.id
        assert data["file_name"] == "test_image.png"
        assert data["file_type"] == "image/png"
        assert data["file_size"] == len(file_content)
        assert "file_path" in data
        assert "created_at" in data

        # Clean up created upload file if needed
        if os.path.exists("uploads"):
            shutil.rmtree("uploads", ignore_errors=True)

    def test_upload_work_item_attachment_pdf_success(
        self,
        client: TestClient,
        user1_headers: dict[str, str],
        work_item_1: WorkItemModel,
    ):
        """Test uploading valid PDF attachment."""
        file_content = b"%PDF-1.4 sample pdf content for testing"
        file_tuple = ("report.pdf", io.BytesIO(file_content), "application/pdf")

        response = client.post(
            f"/work-items/{work_item_1.id}/attachments",
            files={"file": file_tuple},
            headers=user1_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["file_name"] == "report.pdf"
        assert data["file_type"] == "application/pdf"

        if os.path.exists("uploads"):
            shutil.rmtree("uploads", ignore_errors=True)

    def test_upload_work_item_attachment_invalid_file_type_error(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        work_item_1: WorkItemModel,
    ):
        """Test uploading text/plain file is rejected with 400."""
        file_content = b"Plain text file not allowed"
        file_tuple = ("document.txt", io.BytesIO(file_content), "text/plain")

        response = client.post(
            f"/work-items/{work_item_1.id}/attachments",
            files={"file": file_tuple},
            headers=admin_headers,
        )
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "BAD_REQUEST"
        assert "Invalid file type" in data["message"]

    def test_upload_work_item_attachment_oversized_file_error(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        work_item_1: WorkItemModel,
    ):
        """Test uploading file larger than 10MB limit returns 400."""
        # 11 MB simulated file
        large_content = b"A" * (11 * 1024 * 1024)
        file_tuple = ("large.pdf", io.BytesIO(large_content), "application/pdf")

        response = client.post(
            f"/work-items/{work_item_1.id}/attachments",
            files={"file": file_tuple},
            headers=admin_headers,
        )
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "BAD_REQUEST"
        assert "File size exceeds 10MB limit" in data["message"]

    def test_upload_work_item_attachment_non_member_forbidden(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        work_item_3: WorkItemModel,
    ):
        """Test non-member uploading attachment is forbidden."""
        file_content = b"%PDF-1.4 test"
        file_tuple = ("report.pdf", io.BytesIO(file_content), "application/pdf")

        response = client.post(
            f"/work-items/{work_item_3.id}/attachments",
            files={"file": file_tuple},
            headers=admin_headers,
        )
        assert response.status_code == 403
        assert response.json()["error_code"] == "FORBIDDEN"

    def test_get_work_item_attachments_success(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        work_item_1: WorkItemModel,
    ):
        """Test GET /work-items/{item_id}/attachments lists all uploaded attachments."""
        # Upload an attachment first
        file_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        file_tuple = ("site_photo.png", io.BytesIO(file_content), "image/png")
        client.post(
            f"/work-items/{work_item_1.id}/attachments",
            files={"file": file_tuple},
            headers=admin_headers,
        )

        response = client.get(
            f"/work-items/{work_item_1.id}/attachments",
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["file_name"] == "site_photo.png"
        assert data[0]["file_type"] == "image/png"
        assert "file_path" in data[0]
        assert "file_size" in data[0]

        if os.path.exists("uploads"):
            shutil.rmtree("uploads", ignore_errors=True)

    def test_get_work_item_attachments_non_member_forbidden(
        self,
        client: TestClient,
        admin_headers: dict[str, str],
        work_item_3: WorkItemModel,
    ):
        """Test non-member retrieving attachments returns 403."""
        response = client.get(
            f"/work-items/{work_item_3.id}/attachments",
            headers=admin_headers,
        )
        assert response.status_code == 403
        assert response.json()["error_code"] == "FORBIDDEN"
