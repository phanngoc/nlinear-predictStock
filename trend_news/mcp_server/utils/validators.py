"""
Công cụ xác thực tham số

Cung cấp chức năng xác thực tham số thống nhất.
"""

from datetime import datetime
from typing import List, Optional
import os
import yaml

from .errors import InvalidParameterError
from .date_parser import DateParser


def get_supported_platforms() -> List[str]:
    """
    Lấy danh sách nền tảng được hỗ trợ từ config.yaml một cách động

    Returns:
        Danh sách ID nền tảng

    Lưu ý:
        - Khi đọc thất bại, trả về danh sách rỗng, cho phép tất cả nền tảng đi qua (chiến lược giảm cấp)
        - Danh sách nền tảng lấy từ cấu hình platforms trong config/config.yaml
    """
    try:
        # Lấy đường dẫn config.yaml (tương đối với file hiện tại)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(current_dir, "..", "..", "config", "config.yaml")
        config_path = os.path.normpath(config_path)

        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            platforms = config.get('platforms', [])
            return [p['id'] for p in platforms if 'id' in p]
    except Exception as e:
        # Phương án giảm cấp: trả về danh sách rỗng, cho phép tất cả nền tảng
        print(f"Cảnh báo: Không thể tải cấu hình nền tảng ({config_path}): {e}")
        return []


def validate_platforms(platforms: Optional[List[str]]) -> List[str]:
    """
    Xác thực danh sách nền tảng

    Args:
        platforms: Danh sách ID nền tảng, None nghĩa là sử dụng tất cả nền tảng được cấu hình trong config.yaml

    Returns:
        Danh sách nền tảng đã xác thực

    Raises:
        InvalidParameterError: Nền tảng không được hỗ trợ

    Lưu ý:
        - Khi platforms=None, trả về danh sách nền tảng được cấu hình trong config.yaml
        - Sẽ xác thực xem ID nền tảng có trong cấu hình platforms của config.yaml không
        - Khi tải cấu hình thất bại, cho phép tất cả nền tảng đi qua (chiến lược giảm cấp)
    """
    supported_platforms = get_supported_platforms()

    if platforms is None:
        # Trả về danh sách nền tảng trong file cấu hình (cấu hình mặc định của người dùng)
        return supported_platforms if supported_platforms else []

    if not isinstance(platforms, list):
        raise InvalidParameterError("Tham số platforms phải là kiểu danh sách")

    if not platforms:
        # Khi danh sách rỗng, trả về danh sách nền tảng trong file cấu hình
        return supported_platforms if supported_platforms else []

    # Nếu tải cấu hình thất bại (supported_platforms rỗng), cho phép tất cả nền tảng đi qua
    if not supported_platforms:
        print("Cảnh báo: Cấu hình nền tảng chưa được tải, bỏ qua xác thực nền tảng")
        return platforms

    # Xác thực xem mỗi nền tảng có trong cấu hình không
    invalid_platforms = [p for p in platforms if p not in supported_platforms]
    if invalid_platforms:
        raise InvalidParameterError(
            f"Nền tảng không được hỗ trợ: {', '.join(invalid_platforms)}",
            suggestion=f"Các nền tảng được hỗ trợ (từ config.yaml): {', '.join(supported_platforms)}"
        )

    return platforms


def validate_limit(limit: Optional[int], default: int = 20, max_limit: int = 1000) -> int:
    """
    Xác thực tham số giới hạn số lượng

    Args:
        limit: Số lượng giới hạn
        default: Giá trị mặc định
        max_limit: Giới hạn tối đa

    Returns:
        Giá trị giới hạn đã xác thực

    Raises:
        InvalidParameterError: Tham số không hợp lệ
    """
    if limit is None:
        return default

    if not isinstance(limit, int):
        raise InvalidParameterError("Tham số limit phải là kiểu số nguyên")

    if limit <= 0:
        raise InvalidParameterError("limit phải lớn hơn 0")

    if limit > max_limit:
        raise InvalidParameterError(
            f"limit không thể vượt quá {max_limit}",
            suggestion=f"Vui lòng sử dụng phân trang hoặc giảm giá trị limit"
        )

    return limit


def validate_date(date_str: str) -> datetime:
    """
    Xác thực định dạng ngày

    Args:
        date_str: Chuỗi ngày (YYYY-MM-DD)

    Returns:
        Đối tượng datetime

    Raises:
        InvalidParameterError: Định dạng ngày sai
    """
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise InvalidParameterError(
            f"Định dạng ngày sai: {date_str}",
            suggestion="Vui lòng sử dụng định dạng YYYY-MM-DD, ví dụ: 2025-10-11"
        )


def validate_date_range(date_range: Optional[dict]) -> Optional[tuple]:
    """
    Xác thực phạm vi ngày

    Args:
        date_range: Dictionary phạm vi ngày {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}

    Returns:
        Tuple (start_date, end_date), hoặc None

    Raises:
        InvalidParameterError: Phạm vi ngày không hợp lệ
    """
    if date_range is None:
        return None

    if not isinstance(date_range, dict):
        raise InvalidParameterError("date_range phải là kiểu dictionary")

    start_str = date_range.get("start")
    end_str = date_range.get("end")

    if not start_str or not end_str:
        raise InvalidParameterError(
            "date_range phải chứa trường start và end",
            suggestion='Ví dụ: {"start": "2025-10-01", "end": "2025-10-11"}'
        )

    start_date = validate_date(start_str)
    end_date = validate_date(end_str)

    if start_date > end_date:
        raise InvalidParameterError(
            "Ngày bắt đầu không thể sau ngày kết thúc",
            suggestion=f"start: {start_str}, end: {end_str}"
        )

    # Kiểm tra xem ngày có trong tương lai không
    today = datetime.now().date()
    if start_date.date() > today or end_date.date() > today:
        # Lấy gợi ý phạm vi ngày khả dụng
        try:
            from ..services.data_service import DataService
            data_service = DataService()
            earliest, latest = data_service.get_available_date_range()

            if earliest and latest:
                available_range = f"{earliest.strftime('%Y-%m-%d')} đến {latest.strftime('%Y-%m-%d')}"
            else:
                available_range = "Không có dữ liệu khả dụng"
        except Exception:
            available_range = "Không xác định (vui lòng kiểm tra thư mục output)"

        future_dates = []
        if start_date.date() > today:
            future_dates.append(start_str)
        if end_date.date() > today and end_str != start_str:
            future_dates.append(end_str)

        raise InvalidParameterError(
            f"Không cho phép truy vấn ngày tương lai: {', '.join(future_dates)} (Ngày hiện tại: {today.strftime('%Y-%m-%d')})",
            suggestion=f"Phạm vi dữ liệu khả dụng hiện tại: {available_range}"
        )

    return (start_date, end_date)


def validate_keyword(keyword: str) -> str:
    """
    Xác thực từ khóa

    Args:
        keyword: Từ khóa tìm kiếm

    Returns:
        Từ khóa đã xử lý

    Raises:
        InvalidParameterError: Từ khóa không hợp lệ
    """
    if not keyword:
        raise InvalidParameterError("keyword không thể để trống")

    if not isinstance(keyword, str):
        raise InvalidParameterError("keyword phải là kiểu chuỗi")

    keyword = keyword.strip()

    if not keyword:
        raise InvalidParameterError("keyword không thể chỉ chứa khoảng trắng")

    if len(keyword) > 100:
        raise InvalidParameterError(
            "Độ dài keyword không thể vượt quá 100 ký tự",
            suggestion="Vui lòng sử dụng từ khóa ngắn gọn hơn"
        )

    return keyword


def validate_top_n(top_n: Optional[int], default: int = 10) -> int:
    """
    Xác thực tham số TOP N

    Args:
        top_n: Số lượng TOP N
        default: Giá trị mặc định

    Returns:
        Giá trị đã xác thực

    Raises:
        InvalidParameterError: Tham số không hợp lệ
    """
    return validate_limit(top_n, default=default, max_limit=100)


def validate_mode(mode: Optional[str], valid_modes: List[str], default: str) -> str:
    """
    Xác thực tham số chế độ

    Args:
        mode: Chuỗi chế độ
        valid_modes: Danh sách chế độ hợp lệ
        default: Chế độ mặc định

    Returns:
        Chế độ đã xác thực

    Raises:
        InvalidParameterError: Chế độ không hợp lệ
    """
    if mode is None:
        return default

    if not isinstance(mode, str):
        raise InvalidParameterError("mode phải là kiểu chuỗi")

    if mode not in valid_modes:
        raise InvalidParameterError(
            f"Chế độ không hợp lệ: {mode}",
            suggestion=f"Các chế độ được hỗ trợ: {', '.join(valid_modes)}"
        )

    return mode


def validate_config_section(section: Optional[str]) -> str:
    """
    Xác thực tham số phần cấu hình

    Args:
        section: Tên phần cấu hình

    Returns:
        Phần cấu hình đã xác thực

    Raises:
        InvalidParameterError: Phần cấu hình không hợp lệ
    """
    valid_sections = ["all", "crawler", "push", "keywords", "weights"]
    return validate_mode(section, valid_sections, "all")


def validate_date_query(
    date_query: str,
    allow_future: bool = False,
    max_days_ago: int = 365
) -> datetime:
    """
    Xác thực và phân tích chuỗi truy vấn ngày

    Args:
        date_query: Chuỗi truy vấn ngày
        allow_future: Có cho phép ngày tương lai không
        max_days_ago: Số ngày tối đa cho phép truy vấn

    Returns:
        Đối tượng datetime đã phân tích

    Raises:
        InvalidParameterError: Truy vấn ngày không hợp lệ

    Ví dụ:
        >>> validate_date_query("hôm qua")
        datetime(2025, 10, 10)
        >>> validate_date_query("2025-10-10")
        datetime(2025, 10, 10)
    """
    if not date_query:
        raise InvalidParameterError(
            "Chuỗi truy vấn ngày không thể để trống",
            suggestion="Vui lòng cung cấp truy vấn ngày, ví dụ: hôm nay, hôm qua, 2025-10-10"
        )

    # Sử dụng DateParser để phân tích ngày
    parsed_date = DateParser.parse_date_query(date_query)

    # Xác thực ngày không nằm trong tương lai
    if not allow_future:
        DateParser.validate_date_not_future(parsed_date)

    # Xác thực ngày không quá xa
    DateParser.validate_date_not_too_old(parsed_date, max_days=max_days_ago)

    return parsed_date
