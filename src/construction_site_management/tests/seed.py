import os
import sys
from datetime import UTC, datetime, timedelta

# Thêm thư mục src vào sys.path để import đúng các module
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

try:
    from construction_site_management.app.core.security import get_password_hash
    from construction_site_management.app.db.database import Base, SessionLocal, engine
    from construction_site_management.app.models import (
        ConstructionSiteModel,
        RoleSiteMemberEnum,
        RoleUserEnum,
        SiteMemberModel,
        UserModel,
        WorkItemModel,
    )
    from construction_site_management.app.models.work_items import (
        PriorityEnum,
        WorkStatusEnum,
    )
except ImportError:
    from app.core.security import get_password_hash
    from app.db.database import Base, SessionLocal, engine
    from app.models import (
        ConstructionSiteModel,
        RoleSiteMemberEnum,
        RoleUserEnum,
        SiteMemberModel,
        UserModel,
        WorkItemModel,
    )
    from app.models.work_items import (
        PriorityEnum,
        WorkStatusEnum,
    )


from sqlalchemy.orm import Session


def seed_data(db: Session | None = None) -> dict:
    close_db_on_exit = False
    if db is None:
        print("Đang tạo các bảng trong cơ sở dữ liệu (nếu chưa có)...")
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        close_db_on_exit = True

    try:
        # 1. Seed Users (Tạo người dùng mẫu)
        print("1. Đang seed Users...")
        admin_user = (
            db.query(UserModel).filter(UserModel.email == "admin@example.com").first()
        )
        if not admin_user:
            admin_user = UserModel(
                email="admin@example.com",
                password_hash=get_password_hash("Admin@123"),
                full_name="Quản trị viên Hệ thống",
                role=RoleUserEnum.ADMIN,
                is_active=True,
            )
            db.add(admin_user)

        user_1 = (
            db.query(UserModel)
            .filter(UserModel.email == "nguyenvana@example.com")
            .first()
        )
        if not user_1:
            user_1 = UserModel(
                email="nguyenvana@example.com",
                password_hash=get_password_hash("User@123"),
                full_name="Nguyễn Văn A",
                role=RoleUserEnum.USER,
                is_active=True,
            )
            db.add(user_1)

        user_2 = (
            db.query(UserModel)
            .filter(UserModel.email == "tranthib@example.com")
            .first()
        )
        if not user_2:
            user_2 = UserModel(
                email="tranthib@example.com",
                password_hash=get_password_hash("User@123"),
                full_name="Trần Thị B",
                role=RoleUserEnum.USER,
                is_active=True,
            )
            db.add(user_2)

        db.commit()
        db.refresh(admin_user)
        db.refresh(user_1)
        db.refresh(user_2)
        print("   -> Hoàn tất seed Users.")

        # 2. Seed Construction Sites (Công trình)
        print("2. Đang seed Công trình (Construction Sites)...")
        site_1 = (
            db.query(ConstructionSiteModel)
            .filter(ConstructionSiteModel.name == "Tòa nhà văn phòng Hưng Phát")
            .first()
        )
        if not site_1:
            site_1 = ConstructionSiteModel(
                name="Tòa nhà văn phòng Hưng Phát",
                description=(
                    "Dự án xây dựng tòa nhà văn phòng 15 tầng tại Quận 1, TP.HCM"
                ),
                owner_id=admin_user.id,
            )
            db.add(site_1)

        site_2 = (
            db.query(ConstructionSiteModel)
            .filter(ConstructionSiteModel.name == "Khu dân cư Green City")
            .first()
        )
        if not site_2:
            site_2 = ConstructionSiteModel(
                name="Khu dân cư Green City",
                description=(
                    "Khu đô thị mới với 200 căn biệt thự và khu tiện ích công cộng"
                ),
                owner_id=user_1.id,
            )
            db.add(site_2)

        db.commit()
        db.refresh(site_1)
        db.refresh(site_2)
        print("   -> Hoàn tất seed Công trình.")

        # 3. Seed Site Members (Thành viên công trình)
        print("3. Đang phân công Thành viên (Site Members)...")
        # Site 1
        if (
            not db.query(SiteMemberModel)
            .filter_by(site_id=site_1.id, user_id=admin_user.id)
            .first()
        ):
            db.add(
                SiteMemberModel(
                    site_id=site_1.id,
                    user_id=admin_user.id,
                    role=RoleSiteMemberEnum.OWNER,
                )
            )
        if (
            not db.query(SiteMemberModel)
            .filter_by(site_id=site_1.id, user_id=user_1.id)
            .first()
        ):
            db.add(
                SiteMemberModel(
                    site_id=site_1.id,
                    user_id=user_1.id,
                    role=RoleSiteMemberEnum.MEMBER,
                )
            )
        if (
            not db.query(SiteMemberModel)
            .filter_by(site_id=site_1.id, user_id=user_2.id)
            .first()
        ):
            db.add(
                SiteMemberModel(
                    site_id=site_1.id,
                    user_id=user_2.id,
                    role=RoleSiteMemberEnum.MEMBER,
                )
            )

        # Site 2
        if (
            not db.query(SiteMemberModel)
            .filter_by(site_id=site_2.id, user_id=user_1.id)
            .first()
        ):
            db.add(
                SiteMemberModel(
                    site_id=site_2.id,
                    user_id=user_1.id,
                    role=RoleSiteMemberEnum.OWNER,
                )
            )
        if (
            not db.query(SiteMemberModel)
            .filter_by(site_id=site_2.id, user_id=user_2.id)
            .first()
        ):
            db.add(
                SiteMemberModel(
                    site_id=site_2.id,
                    user_id=user_2.id,
                    role=RoleSiteMemberEnum.MEMBER,
                )
            )

        db.commit()
        print("   -> Hoàn tất phân công Thành viên.")

        # 4. Seed Work Items (Hạng mục thi công)
        print("4. Đang seed Hạng mục thi công (Work Items)...")
        now = datetime.now(UTC)

        # Hạng mục cho Site 1
        work_item_1 = (
            db.query(WorkItemModel)
            .filter_by(site_id=site_1.id, title="Đào móng tòa nhà")
            .first()
        )
        if not work_item_1:
            work_item_1 = WorkItemModel(
                site_id=site_1.id,
                title="Đào móng tòa nhà",
                description=(
                    "Thi công đào móng và xử lý nền móng tầng hầm, "
                    "bao gồm cả đóng cọc nhồi."
                ),
                assignee_id=user_1.id,
                status=WorkStatusEnum.IN_PROGRESS,
                priority=PriorityEnum.HIGH,
                due_date=now + timedelta(days=7),
            )
            db.add(work_item_1)

        work_item_2 = (
            db.query(WorkItemModel)
            .filter_by(site_id=site_1.id, title="Đổ bê tông sàn tầng 1")
            .first()
        )
        if not work_item_2:
            work_item_2 = WorkItemModel(
                site_id=site_1.id,
                title="Đổ bê tông sàn tầng 1",
                description="Lắp dựng cốt thép và đổ bê tông sàn toàn khối tầng 1.",
                assignee_id=user_2.id,
                status=WorkStatusEnum.TODO,
                priority=PriorityEnum.MEDIUM,
                due_date=now + timedelta(days=14),
            )
            db.add(work_item_2)

        # Hạng mục cho Site 2
        work_item_3 = (
            db.query(WorkItemModel)
            .filter_by(site_id=site_2.id, title="Khảo sát địa hình")
            .first()
        )
        if not work_item_3:
            work_item_3 = WorkItemModel(
                site_id=site_2.id,
                title="Khảo sát địa hình",
                description=(
                    "Đo đạc và lập bản đồ địa hình toàn khu dự án tỷ lệ 1/500."
                ),
                assignee_id=user_1.id,
                status=WorkStatusEnum.DONE,
                priority=PriorityEnum.HIGH,
                due_date=now - timedelta(days=2),
            )
            db.add(work_item_3)

        db.commit()
        db.refresh(work_item_1)
        db.refresh(work_item_2)
        db.refresh(work_item_3)
        print("   -> Hoàn tất seed Hạng mục thi công.")

        print("\n=> TOÀN BỘ DỮ LIỆU MẪU ĐÃ ĐƯỢC TẠO THÀNH CÔNG!")
        print("\nThông tin tài khoản đăng nhập (Mật khẩu chung: Admin@123 / User@123):")
        print("- admin@example.com (Admin)")
        print("- nguyenvana@example.com (User)")
        print("- tranthib@example.com (User)")

        return {
            "users": {
                "admin": admin_user,
                "user_1": user_1,
                "user_2": user_2,
            },
            "sites": {
                "site_1": site_1,
                "site_2": site_2,
            },
            "work_items": {
                "work_item_1": work_item_1,
                "work_item_2": work_item_2,
                "work_item_3": work_item_3,
            },
        }

    except Exception as e:
        print(f"\n[LỖI] Có lỗi xảy ra trong quá trình seed dữ liệu: {e}")
        db.rollback()
        raise
    finally:
        if close_db_on_exit:
            db.close()


if __name__ == "__main__":
    seed_data()
