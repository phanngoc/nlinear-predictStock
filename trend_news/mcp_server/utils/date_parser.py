"""
Công cụ phân tích ngày

Hỗ trợ phân tích nhiều định dạng ngày ngôn ngữ tự nhiên, bao gồm ngày tương đối và ngày tuyệt đối.
"""

import re
from datetime import datetime, timedelta

from .errors import InvalidParameterError


class DateParser:
    """Lớp phân tích ngày"""

    # Ánh xạ ngày tiếng Trung
    CN_DATE_MAPPING = {
        "hôm nay": 0,
        "hôm qua": 1,
        "hôm kia": 2,
        "3 ngày trước": 3,
    }

    # Ánh xạ ngày tiếng Anh
    EN_DATE_MAPPING = {
        "today": 0,
        "yesterday": 1,
    }

    # Ánh xạ thứ trong tuần
    WEEKDAY_CN = {
        "một": 0, "hai": 1, "ba": 2, "bốn": 3,
        "năm": 4, "sáu": 5, "ngày": 6, "天": 6
    }

    WEEKDAY_EN = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6
    }

    @staticmethod
    def parse_date_query(date_query: str) -> datetime:
        """
        Phân tích chuỗi truy vấn ngày

        Các định dạng được hỗ trợ:
        - Ngày tương đối (tiếng Trung): hôm nay、hôm qua、hôm kia、3 ngày trước、N天前
        - Ngày tương đối (tiếng Anh): today、yesterday、N days ago
        - Thứ trong tuần (tiếng Trung): thứ hai tuần trước、trên周hai、thứ tư tuần này
        - Thứ trong tuần (tiếng Anh): last monday、this friday
        - Ngày tuyệt đối: 2025-10-10, 10 tháng 10, 2025 năm 10 tháng 10

        Args:
            date_query: Chuỗi truy vấn ngày

        Returns:
            Đối tượng datetime

        Raises:
            InvalidParameterError: Không thể nhận dạng định dạng ngày

        Ví dụ:
            >>> DateParser.parse_date_query("hôm nay")
            datetime(2025, 10, 11)
            >>> DateParser.parse_date_query("hôm qua")
            datetime(2025, 10, 10)
            >>> DateParser.parse_date_query("3天前")
            datetime(2025, 10, 8)
            >>> DateParser.parse_date_query("2025-10-10")
            datetime(2025, 10, 10)
        """
        if not date_query or not isinstance(date_query, str):
            raise InvalidParameterError(
                "Chuỗi truy vấn ngày không thể để trống",
                suggestion="Vui lòng cung cấp truy vấn ngày hợp lệ, ví dụ: hôm nay、hôm qua、2025-10-10"
            )

        date_query = date_query.strip().lower()

        # 1. Thử phân tích ngày tương đối thông dụng tiếng Trung
        if date_query in DateParser.CN_DATE_MAPPING:
            days_ago = DateParser.CN_DATE_MAPPING[date_query]
            return datetime.now() - timedelta(days=days_ago)

        # 2. Thử phân tích ngày tương đối thông dụng tiếng Anh
        if date_query in DateParser.EN_DATE_MAPPING:
            days_ago = DateParser.EN_DATE_MAPPING[date_query]
            return datetime.now() - timedelta(days=days_ago)

        # 3. Thử phân tích "N天前" hoặc "N days ago"
        cn_days_ago_match = re.match(r'(\d+)\s*天前', date_query)
        if cn_days_ago_match:
            days = int(cn_days_ago_match.group(1))
            if days > 365:
                raise InvalidParameterError(
                    f"Số ngày quá lớn: {days} ngày",
                    suggestion="Vui lòng sử dụng ngày tương đối dưới 365 ngày hoặc sử dụng ngày tuyệt đối"
                )
            return datetime.now() - timedelta(days=days)

        en_days_ago_match = re.match(r'(\d+)\s*days?\s+ago', date_query)
        if en_days_ago_match:
            days = int(en_days_ago_match.group(1))
            if days > 365:
                raise InvalidParameterError(
                    f"Số ngày quá lớn: {days} ngày",
                    suggestion="Vui lòng sử dụng ngày tương đối dưới 365 ngày hoặc sử dụng ngày tuyệt đối"
                )
            return datetime.now() - timedelta(days=days)

        # 4. Thử phân tích thứ trong tuần (tiếng Trung): thứ hai tuần trước、thứ tư tuần này
        cn_weekday_match = re.match(r'(trên|本)周([mộthaibabốnnămsáungày天])', date_query)
        if cn_weekday_match:
            week_type = cn_weekday_match.group(1)  # trên hoặc 本
            weekday_str = cn_weekday_match.group(2)
            target_weekday = DateParser.WEEKDAY_CN[weekday_str]
            return DateParser._get_date_by_weekday(target_weekday, week_type == "trên")

        # 5. Thử phân tích thứ trong tuần (tiếng Anh): last monday、this friday
        en_weekday_match = re.match(r'(last|this)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)', date_query)
        if en_weekday_match:
            week_type = en_weekday_match.group(1)  # last hoặc this
            weekday_str = en_weekday_match.group(2)
            target_weekday = DateParser.WEEKDAY_EN[weekday_str]
            return DateParser._get_date_by_weekday(target_weekday, week_type == "last")

        # 6. Thử phân tích ngày tuyệt đối: YYYY-MM-DD
        iso_date_match = re.match(r'(\d{4})-(\d{1,2})-(\d{1,2})', date_query)
        if iso_date_match:
            year = int(iso_date_match.group(1))
            month = int(iso_date_match.group(2))
            day = int(iso_date_match.group(3))
            try:
                return datetime(year, month, day)
            except ValueError as e:
                raise InvalidParameterError(
                    f"Ngày không hợp lệ: {date_query}",
                    suggestion=f"Lỗi giá trị ngày: {str(e)}"
                )

        # 7. Thử phân tích ngày tiếng Trung: MMthángDDngày hoặc YYYYnămMMthángDDngày
        cn_date_match = re.match(r'(?:(\d{4})năm)?(\d{1,2})tháng(\d{1,2})ngày', date_query)
        if cn_date_match:
            year_str = cn_date_match.group(1)
            month = int(cn_date_match.group(2))
            day = int(cn_date_match.group(3))

            # Nếu không có năm, sử dụng năm hiện tại
            if year_str:
                year = int(year_str)
            else:
                year = datetime.now().year
                # Nếu tháng lớn hơn tháng hiện tại, nghĩa là năm trước
                current_month = datetime.now().month
                if month > current_month:
                    year -= 1

            try:
                return datetime(year, month, day)
            except ValueError as e:
                raise InvalidParameterError(
                    f"Ngày không hợp lệ: {date_query}",
                    suggestion=f"Lỗi giá trị ngày: {str(e)}"
                )

        # 8. Thử phân tích định dạng dấu gạch chéo: YYYY/MM/DD hoặc MM/DD
        slash_date_match = re.match(r'(?:(\d{4})/)?(\d{1,2})/(\d{1,2})', date_query)
        if slash_date_match:
            year_str = slash_date_match.group(1)
            month = int(slash_date_match.group(2))
            day = int(slash_date_match.group(3))

            if year_str:
                year = int(year_str)
            else:
                year = datetime.now().year
                current_month = datetime.now().month
                if month > current_month:
                    year -= 1

            try:
                return datetime(year, month, day)
            except ValueError as e:
                raise InvalidParameterError(
                    f"Ngày không hợp lệ: {date_query}",
                    suggestion=f"Lỗi giá trị ngày: {str(e)}"
                )

        # Nếu tất cả định dạng đều không khớp
        raise InvalidParameterError(
            f"Không thể nhận dạng định dạng ngày: {date_query}",
            suggestion=(
                "Các định dạng được hỗ trợ:\n"
                "- Ngày tương đối: hôm nay、hôm qua、hôm kia、3天前、today、yesterday、3 days ago\n"
                "- Thứ trong tuần: thứ hai tuần trước, thứ tư tuần này, last monday, this friday\n"
                "- Ngày tuyệt đối: 2025-10-10, 10 tháng 10, 2025 năm 10 tháng 10"
            )
        )

    @staticmethod
    def _get_date_by_weekday(target_weekday: int, is_last_week: bool) -> datetime:
        """
        Lấy ngày dựa trên thứ trong tuần

        Args:
            target_weekday: Thứ mục tiêu (0=Thứ Hai, 6=Chủ Nhật)
            is_last_week: Có phải tuần trước không

        Returns:
            Đối tượng datetime
        """
        today = datetime.now()
        current_weekday = today.weekday()

        # Tính toán chênh lệch số ngày
        if is_last_week:
            # Một ngày nào đó của tuần trước
            days_diff = current_weekday - target_weekday + 7
        else:
            # Một ngày nào đó của tuần này
            days_diff = current_weekday - target_weekday
            if days_diff < 0:
                days_diff += 7

        return today - timedelta(days=days_diff)

    @staticmethod
    def format_date_folder(date: datetime) -> str:
        """
        Định dạng ngày thành tên thư mục

        Args:
            date: Đối tượng datetime

        Returns:
            Tên thư mục, định dạng: YYYY năm MM tháng DD ngày

        Ví dụ:
            >>> DateParser.format_date_folder(datetime(2025, 10, 11))
            '2025năm10tháng11ngày'
        """
        return date.strftime("%Ynăm%mtháng%dngày")

    @staticmethod
    def validate_date_not_future(date: datetime) -> None:
        """
        Xác thực ngày không nằm trong tương lai

        Args:
            date: Ngày cần xác thực

        Raises:
            InvalidParameterError: Ngày nằm trong tương lai
        """
        if date.date() > datetime.now().date():
            raise InvalidParameterError(
                f"Không thể truy vấn ngày trong tương lai: {date.strftime('%Y-%m-%d')}",
                suggestion="Vui lòng sử dụng ngày hôm nay hoặc ngày trong quá khứ"
            )

    @staticmethod
    def validate_date_not_too_old(date: datetime, max_days: int = 365) -> None:
        """
        Xác thực ngày không quá xa trong quá khứ

        Args:
            date: Ngày cần xác thực
            max_days: Số ngày tối đa

        Raises:
            InvalidParameterError: Ngày quá xa trong quá khứ
        """
        days_ago = (datetime.now().date() - date.date()).days
        if days_ago > max_days:
            raise InvalidParameterError(
                f"Ngày quá xa: {date.strftime('%Y-%m-%d')} ({days_ago} ngày trước)",
                suggestion=f"Vui lòng truy vấn dữ liệu trong vòng {max_days} ngày"
            )
