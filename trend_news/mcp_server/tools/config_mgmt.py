"""
Công cụ quản lý cấu hình

Triển khai chức năng truy vấn và quản lý cấu hình.
"""

from typing import Dict, Optional

from ..services.data_service import DataService
from ..utils.validators import validate_config_section
from ..utils.errors import MCPError


class ConfigManagementTools:
    """Lớp công cụ quản lý cấu hình"""

    def __init__(self, project_root: str = None):
        """
        Khởi tạo công cụ quản lý cấu hình

        Args:
            project_root: Thư mục gốc của dự án
        """
        self.data_service = DataService(project_root)

    def get_current_config(self, section: Optional[str] = None) -> Dict:
        """
        Lấy cấu hình hệ thống hiện tại

        Args:
            section: Phần cấu hình - all/crawler/push/keywords/weights, mặc định all

        Returns:
            Dictionary cấu hình

        Ví dụ:
            >>> tools = ConfigManagementTools()
            >>> result = tools.get_current_config(section="crawler")
            >>> print(result['crawler']['platforms'])
        """
        try:
            # Xác thực tham số
            section = validate_config_section(section)

            # Lấy cấu hình
            config = self.data_service.get_current_config(section=section)

            return {
                "config": config,
                "section": section,
                "success": True
            }

        except MCPError as e:
            return {
                "success": False,
                "error": e.to_dict()
            }
        except Exception as e:
            return {
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(e)
                }
            }
