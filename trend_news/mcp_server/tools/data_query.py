"""
Công cụ truy vấn dữ liệu

Triển khai các công cụ truy vấn dữ liệu cốt lõi P0.
"""

from typing import Dict, List, Optional

from ..services.data_service import DataService
from ..utils.validators import (
    validate_platforms,
    validate_limit,
    validate_keyword,
    validate_date_range,
    validate_top_n,
    validate_mode,
    validate_date_query
)
from ..utils.errors import MCPError


class DataQueryTools:
    """Lớp công cụ truy vấn dữ liệu"""

    def __init__(self, project_root: str = None):
        """
        Khởi tạo công cụ truy vấn dữ liệu

        Args:
            project_root: Thư mục gốc của dự án
        """
        self.data_service = DataService(project_root)

    def get_latest_news(
        self,
        platforms: Optional[List[str]] = None,
        limit: Optional[int] = None,
        include_url: bool = False
    ) -> Dict:
        """
        Lấy dữ liệu tin tức từ đợt thu thập mới nhất

        Args:
            platforms: Danh sách ID nền tảng, ví dụ ['zhihu', 'weibo']
            limit: Giới hạn số lượng trả về, mặc định 20
            include_url: Có bao gồm liên kết URL không, mặc định False (tiết kiệm token)

        Returns:
            Dictionary danh sách tin tức

        Ví dụ:
            >>> tools = DataQueryTools()
            >>> result = tools.get_latest_news(platforms=['zhihu'], limit=10)
            >>> print(result['total'])
            10
        """
        try:
            # Xác thực tham số
            platforms = validate_platforms(platforms)
            limit = validate_limit(limit, default=50)

            # Lấy dữ liệu
            news_list = self.data_service.get_latest_news(
                platforms=platforms,
                limit=limit,
                include_url=include_url
            )

            return {
                "news": news_list,
                "total": len(news_list),
                "platforms": platforms,
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

    def search_news_by_keyword(
        self,
        keyword: str,
        date_range: Optional[Dict] = None,
        platforms: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> Dict:
        """
        Tìm kiếm tin tức lịch sử theo từ khóa

        Args:
            keyword: Từ khóa tìm kiếm (bắt buộc)
            date_range: Phạm vi ngày, định dạng: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
            platforms: Danh sách nền tảng để lọc
            limit: Giới hạn số lượng trả về (tùy chọn, mặc định trả về tất cả)

        Returns:
            Dictionary kết quả tìm kiếm

        Ví dụ (giả sử hôm nay là 2025-11-17):
            >>> tools = DataQueryTools()
            >>> result = tools.search_news_by_keyword(
            ...     keyword="trí tuệ nhân tạo",
            ...     date_range={"start": "2025-11-08", "end": "2025-11-17"},
            ...     limit=50
            ... )
            >>> print(result['total'])
        """
        try:
            # Xác thực tham số
            keyword = validate_keyword(keyword)
            date_range_tuple = validate_date_range(date_range)
            platforms = validate_platforms(platforms)

            if limit is not None:
                limit = validate_limit(limit, default=100)

            # Tìm kiếm dữ liệu
            search_result = self.data_service.search_news_by_keyword(
                keyword=keyword,
                date_range=date_range_tuple,
                platforms=platforms,
                limit=limit
            )

            return {
                **search_result,
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

    def get_trending_topics(
        self,
        top_n: Optional[int] = None,
        mode: Optional[str] = None
    ) -> Dict:
        """
        Lấy thống kê tần suất xuất hiện của các từ khóa quan tâm cá nhân

        Lưu ý: Công cụ này dựa trên danh sách từ khóa quan tâm cá nhân trong config/frequency_words.txt,
        không phải tự động trích xuất chủ đề hot từ tin tức. Đây là danh sách từ khóa quan tâm
        có thể tùy chỉnh, người dùng có thể thêm hoặc xóa từ khóa theo sở thích của mình.

        Args:
            top_n: Trả về TOP N từ khóa quan tâm, mặc định 10
            mode: Chế độ - daily (tích lũy trong ngày), current (đợt mới nhất), incremental (tăng dần)

        Returns:
            Dictionary thống kê tần suất từ khóa quan tâm, bao gồm số lần xuất hiện của mỗi từ khóa trong tin tức

        Ví dụ:
            >>> tools = DataQueryTools()
            >>> result = tools.get_trending_topics(top_n=5, mode="current")
            >>> print(len(result['topics']))
            5
            >>> # Trả về thống kê tần suất của các từ khóa bạn đã thiết lập trong frequency_words.txt
        """
        try:
            # Xác thực tham số
            top_n = validate_top_n(top_n, default=10)
            valid_modes = ["daily", "current", "incremental"]
            mode = validate_mode(mode, valid_modes, default="current")

            # Lấy chủ đề xu hướng
            trending_result = self.data_service.get_trending_topics(
                top_n=top_n,
                mode=mode
            )

            return {
                **trending_result,
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

    def get_news_by_date(
        self,
        date_query: Optional[str] = None,
        platforms: Optional[List[str]] = None,
        limit: Optional[int] = None,
        include_url: bool = False
    ) -> Dict:
        """
        Truy vấn tin tức theo ngày, hỗ trợ ngày ngôn ngữ tự nhiên

        Args:
            date_query: Chuỗi truy vấn ngày (tùy chọn, mặc định "hôm nay"), hỗ trợ:
                - Ngày tương đối: hôm nay, hôm qua, hôm kia, 3 ngày trước, yesterday, 3 days ago
                - Thứ trong tuần: thứ hai tuần trước, thứ tư tuần này, last monday, this friday
                - Ngày tuyệt đối: 2025-10-10, 10 tháng 10, 2025 năm 10 tháng 10
            platforms: Danh sách ID nền tảng, ví dụ ['zhihu', 'weibo']
            limit: Giới hạn số lượng trả về, mặc định 50
            include_url: Có bao gồm liên kết URL không, mặc định False (tiết kiệm token)

        Returns:
            Dictionary danh sách tin tức

        Ví dụ:
            >>> tools = DataQueryTools()
            >>> # Không chỉ định ngày, mặc định truy vấn hôm nay
            >>> result = tools.get_news_by_date(platforms=['zhihu'], limit=20)
            >>> # Chỉ định ngày
            >>> result = tools.get_news_by_date(
            ...     date_query="hôm qua",
            ...     platforms=['zhihu'],
            ...     limit=20
            ... )
            >>> print(result['total'])
            20
        """
        try:
            # Xác thực tham số - mặc định hôm nay
            if date_query is None:
                date_query = "hôm nay"
            target_date = validate_date_query(date_query)
            platforms = validate_platforms(platforms)
            limit = validate_limit(limit, default=50)

            # Lấy dữ liệu
            news_list = self.data_service.get_news_by_date(
                target_date=target_date,
                platforms=platforms,
                limit=limit,
                include_url=include_url
            )

            return {
                "news": news_list,
                "total": len(news_list),
                "date": target_date.strftime("%Y-%m-%d"),
                "date_query": date_query,
                "platforms": platforms,
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
