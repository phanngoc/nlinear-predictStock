"""
Các lớp lỗi tùy chỉnh

Định nghĩa tất cả các loại exception tùy chỉnh được sử dụng bởi MCP Server.
"""

from typing import Optional


class MCPError(Exception):
    """Lớp lỗi cơ sở cho công cụ MCP"""

    def __init__(self, message: str, code: str = "MCP_ERROR", suggestion: Optional[str] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.suggestion = suggestion

    def to_dict(self) -> dict:
        """Chuyển đổi sang định dạng dictionary"""
        error_dict = {
            "code": self.code,
            "message": self.message
        }
        if self.suggestion:
            error_dict["suggestion"] = self.suggestion
        return error_dict


class DataNotFoundError(MCPError):
    """Lỗi dữ liệu không tồn tại"""

    def __init__(self, message: str, suggestion: Optional[str] = None):
        super().__init__(
            message=message,
            code="DATA_NOT_FOUND",
            suggestion=suggestion or "Vui lòng kiểm tra phạm vi ngày hoặc đợi task thu thập hoàn thành"
        )


class InvalidParameterError(MCPError):
    """Lỗi tham số không hợp lệ"""

    def __init__(self, message: str, suggestion: Optional[str] = None):
        super().__init__(
            message=message,
            code="INVALID_PARAMETER",
            suggestion=suggestion or "Vui lòng kiểm tra xem định dạng tham số có đúng không"
        )


class ConfigurationError(MCPError):
    """Lỗi cấu hình"""

    def __init__(self, message: str, suggestion: Optional[str] = None):
        super().__init__(
            message=message,
            code="CONFIGURATION_ERROR",
            suggestion=suggestion or "Vui lòng kiểm tra xem file cấu hình có đúng không"
        )


class PlatformNotSupportedError(MCPError):
    """Lỗi nền tảng không được hỗ trợ"""

    def __init__(self, platform: str):
        super().__init__(
            message=f"Nền tảng '{platform}' không được hỗ trợ",
            code="PLATFORM_NOT_SUPPORTED",
            suggestion="Các nền tảng được hỗ trợ: zhihu, weibo, douyin, bilibili, baidu, toutiao, qq, 36kr, sspai, hellogithub, thepaper"
        )


class CrawlTaskError(MCPError):
    """Lỗi task thu thập"""

    def __init__(self, message: str, suggestion: Optional[str] = None):
        super().__init__(
            message=message,
            code="CRAWL_TASK_ERROR",
            suggestion=suggestion or "Vui lòng thử lại sau hoặc xem log"
        )


class FileParseError(MCPError):
    """Lỗi phân tích file"""

    def __init__(self, file_path: str, reason: str):
        super().__init__(
            message=f"Phân tích file {file_path} thất bại: {reason}",
            code="FILE_PARSE_ERROR",
            suggestion="Vui lòng kiểm tra xem định dạng file có đúng không"
        )
