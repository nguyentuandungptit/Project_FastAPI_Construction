import sys
from pathlib import Path

# Thêm thư mục hiện tại vào sys.path để các import dạng `from app.xyz import ...` hoạt động
package_dir = str(Path(__file__).parent.resolve())
if package_dir not in sys.path:
    sys.path.insert(0, package_dir)

def start():
    from construction_site_management.main import start as main_start
    main_start()
