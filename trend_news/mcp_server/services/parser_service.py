"""
Dịch vụ phân tích file

Cung cấp chức năng phân tích dữ liệu tin tức định dạng txt và file cấu hình YAML.
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

import yaml

from ..utils.errors import FileParseError, DataNotFoundError
from .cache_service import get_cache


class ParserService:
    """Lớp dịch vụ phân tích file"""

    def __init__(self, project_root: str = None):
        """
        Khởi tạo dịch vụ phân tích

        Args:
            project_root: Thư mục gốc của dự án, mặc định là thư mục cha của thư mục hiện tại
        """
        if project_root is None:
            # Lấy thư mục cha của thư mục cha của file hiện tại
            current_file = Path(__file__)
            self.project_root = current_file.parent.parent.parent
        else:
            self.project_root = Path(project_root)

        # Khởi tạo dịch vụ cache
        self.cache = get_cache()

    @staticmethod
    def clean_title(title: str) -> str:
        """
        Làm sạch văn bản tiêu đề

        Args:
            title: Tiêu đề gốc

        Returns:
            Tiêu đề đã làm sạch
        """
        # Loại bỏ khoảng trắng thừa
        title = re.sub(r'\s+', ' ', title)
        # Loại bỏ ký tự đặc biệt
        title = title.strip()
        return title

    def parse_txt_file(self, file_path: Path) -> Tuple[Dict, Dict]:
        """
        Phân tích dữ liệu tiêu đề từ một file txt

        Args:
            file_path: Đường dẫn file txt

        Returns:
            Tuple (titles_by_id, id_to_name)
            - titles_by_id: {platform_id: {title: {ranks, url, mobileUrl}}}
            - id_to_name: {platform_id: platform_name}

        Raises:
            FileParseError: Lỗi phân tích file
        """
        if not file_path.exists():
            raise FileParseError(str(file_path), "File không tồn tại")

        titles_by_id = {}
        id_to_name = {}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                sections = content.split("\n\n")

                for section in sections:
                    if not section.strip() or "==== Các ID sau yêu cầu thất bại ====" in section:
                        continue

                    lines = section.strip().split("\n")
                    if len(lines) < 2:
                        continue

                    # Phân tích header: id | name hoặc id
                    header_line = lines[0].strip()
                    if " | " in header_line:
                        parts = header_line.split(" | ", 1)
                        source_id = parts[0].strip()
                        name = parts[1].strip()
                        id_to_name[source_id] = name
                    else:
                        source_id = header_line
                        id_to_name[source_id] = source_id

                    titles_by_id[source_id] = {}

                    # Phân tích các dòng tiêu đề
                    for line in lines[1:]:
                        if line.strip():
                            try:
                                title_part = line.strip()
                                rank = None

                                # Trích xuất thứ hạng
                                if ". " in title_part and title_part.split(". ")[0].isdigit():
                                    rank_str, title_part = title_part.split(". ", 1)
                                    rank = int(rank_str)

                                # Trích xuất MOBILE URL
                                mobile_url = ""
                                if " [MOBILE:" in title_part:
                                    title_part, mobile_part = title_part.rsplit(" [MOBILE:", 1)
                                    if mobile_part.endswith("]"):
                                        mobile_url = mobile_part[:-1]

                                # Trích xuất URL
                                url = ""
                                if " [URL:" in title_part:
                                    title_part, url_part = title_part.rsplit(" [URL:", 1)
                                    if url_part.endswith("]"):
                                        url = url_part[:-1]

                                title = self.clean_title(title_part.strip())
                                ranks = [rank] if rank is not None else [1]

                                titles_by_id[source_id][title] = {
                                    "ranks": ranks,
                                    "url": url,
                                    "mobileUrl": mobile_url,
                                }

                            except Exception as e:
                                # Bỏ qua lỗi phân tích dòng đơn lẻ
                                continue

        except Exception as e:
            raise FileParseError(str(file_path), str(e))

        return titles_by_id, id_to_name

    def get_date_folder_name(self, date: datetime = None) -> str:
        """
        Lấy tên thư mục ngày

        Args:
            date: Đối tượng ngày, mặc định là hôm nay

        Returns:
            Tên thư mục, định dạng: YYYY năm MM tháng DD ngày
        """
        if date is None:
            date = datetime.now()
        return date.strftime("%Ynăm%mtháng%dngày")

    def read_all_titles_for_date(
        self,
        date: datetime = None,
        platform_ids: Optional[List[str]] = None
    ) -> Tuple[Dict, Dict, Dict]:
        """
        Đọc tất cả file tiêu đề của ngày chỉ định (có cache)

        Args:
            date: Đối tượng ngày, mặc định là hôm nay
            platform_ids: Danh sách ID nền tảng, None nghĩa là tất cả nền tảng

        Returns:
            Tuple (all_titles, id_to_name, all_timestamps)
            - all_titles: {platform_id: {title: {ranks, url, mobileUrl, ...}}}
            - id_to_name: {platform_id: platform_name}
            - all_timestamps: {filename: timestamp}

        Raises:
            DataNotFoundError: Dữ liệu không tồn tại
        """
        # Tạo khóa cache
        date_str = self.get_date_folder_name(date)
        platform_key = ','.join(sorted(platform_ids)) if platform_ids else 'all'
        cache_key = f"read_all_titles:{date_str}:{platform_key}"

        # Thử lấy từ cache
        # Với dữ liệu lịch sử (không phải hôm nay), sử dụng thời gian cache dài hơn (1 giờ)
        # Với dữ liệu hôm nay, sử dụng thời gian cache ngắn hơn (15 phút), vì có thể có dữ liệu mới
        is_today = (date is None) or (date.date() == datetime.now().date())
        ttl = 900 if is_today else 3600  # 15 phút vs 1 giờ

        cached = self.cache.get(cache_key, ttl=ttl)
        if cached:
            return cached

        # Cache miss, đọc file
        date_folder = self.get_date_folder_name(date)
        txt_dir = self.project_root / "output" / date_folder / "txt"

        if not txt_dir.exists():
            raise DataNotFoundError(
                f"Không tìm thấy thư mục dữ liệu {date_folder}",
                suggestion="Vui lòng chạy crawler trước hoặc kiểm tra ngày có đúng không"
            )

        all_titles = {}
        id_to_name = {}
        all_timestamps = {}

        # Đọc tất cả file txt
        txt_files = sorted(txt_dir.glob("*.txt"))

        if not txt_files:
            raise DataNotFoundError(
                f"{date_folder} không có file dữ liệu",
                suggestion="Vui lòng đợi task crawler hoàn thành"
            )

        for txt_file in txt_files:
            try:
                titles_by_id, file_id_to_name = self.parse_txt_file(txt_file)

                # Cập nhật id_to_name
                id_to_name.update(file_id_to_name)

                # Hợp nhất dữ liệu tiêu đề
                for platform_id, titles in titles_by_id.items():
                    # Nếu có lọc nền tảng
                    if platform_ids and platform_id not in platform_ids:
                        continue

                    if platform_id not in all_titles:
                        all_titles[platform_id] = {}

                    for title, info in titles.items():
                        if title in all_titles[platform_id]:
                            # Hợp nhất thứ hạng
                            all_titles[platform_id][title]["ranks"].extend(info["ranks"])
                        else:
                            all_titles[platform_id][title] = info.copy()

                # Ghi nhận timestamp của file
                all_timestamps[txt_file.name] = txt_file.stat().st_mtime

            except Exception as e:
                # Bỏ qua lỗi phân tích file đơn lẻ, tiếp tục xử lý các file khác
                print(f"Cảnh báo: Phân tích file {txt_file} thất bại: {e}")
                continue

        if not all_titles:
            raise DataNotFoundError(
                f"{date_folder} không có dữ liệu hợp lệ",
                suggestion="Vui lòng kiểm tra định dạng file dữ liệu hoặc chạy lại crawler"
            )

        # Lưu kết quả vào cache
        result = (all_titles, id_to_name, all_timestamps)
        self.cache.set(cache_key, result)

        return result

    def parse_yaml_config(self, config_path: str = None) -> dict:
        """
        Phân tích file cấu hình YAML

        Args:
            config_path: Đường dẫn file cấu hình, mặc định là config/config.yaml

        Returns:
            Dictionary cấu hình

        Raises:
            FileParseError: Lỗi phân tích file cấu hình
        """
        if config_path is None:
            config_path = self.project_root / "config" / "config.yaml"
        else:
            config_path = Path(config_path)

        if not config_path.exists():
            raise FileParseError(str(config_path), "File cấu hình không tồn tại")

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)
            return config_data
        except Exception as e:
            raise FileParseError(str(config_path), str(e))

    def parse_frequency_words(self, words_file: str = None) -> List[Dict]:
        """
        Phân tích file cấu hình từ khóa

        Args:
            words_file: Đường dẫn file từ khóa, mặc định là config/frequency_words.txt

        Returns:
            Danh sách nhóm từ

        Raises:
            FileParseError: Lỗi phân tích file
        """
        if words_file is None:
            words_file = self.project_root / "config" / "frequency_words.txt"
        else:
            words_file = Path(words_file)

        if not words_file.exists():
            return []

        word_groups = []

        try:
            with open(words_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue

                    # Sử dụng dấu phân cách |
                    parts = [p.strip() for p in line.split("|")]
                    if not parts:
                        continue

                    group = {
                        "required": [],
                        "normal": [],
                        "filter_words": []
                    }

                    for part in parts:
                        if not part:
                            continue

                        words = [w.strip() for w in part.split(",")]
                        for word in words:
                            if not word:
                                continue
                            if word.endswith("+"):
                                # Từ bắt buộc
                                group["required"].append(word[:-1])
                            elif word.endswith("!"):
                                # Từ lọc
                                group["filter_words"].append(word[:-1])
                            else:
                                # Từ thông thường
                                group["normal"].append(word)

                    if group["required"] or group["normal"]:
                        word_groups.append(group)

        except Exception as e:
            raise FileParseError(str(words_file), str(e))

        return word_groups
