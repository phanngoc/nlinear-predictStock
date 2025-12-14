"""
Dịch vụ truy cập dữ liệu

Cung cấp giao diện truy vấn dữ liệu thống nhất, đóng gói logic truy cập dữ liệu.
"""

import re
from collections import Counter
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from .cache_service import get_cache
from .parser_service import ParserService
from ..utils.errors import DataNotFoundError


class DataService:
    """Lớp dịch vụ truy cập dữ liệu"""

    def __init__(self, project_root: str = None):
        """
        Khởi tạo dịch vụ dữ liệu

        Args:
            project_root: Thư mục gốc của dự án
        """
        self.parser = ParserService(project_root)
        self.cache = get_cache()

    def get_latest_news(
        self,
        platforms: Optional[List[str]] = None,
        limit: int = 50,
        include_url: bool = False
    ) -> List[Dict]:
        """
        Lấy dữ liệu tin tức từ đợt thu thập mới nhất

        Args:
            platforms: Danh sách ID nền tảng, None nghĩa là tất cả nền tảng
            limit: Giới hạn số lượng trả về
            include_url: Có bao gồm liên kết URL không, mặc định False (tiết kiệm token)

        Returns:
            Danh sách tin tức

        Raises:
            DataNotFoundError: Dữ liệu không tồn tại
        """
        # Thử lấy từ cache
        cache_key = f"latest_news:{','.join(platforms or [])}:{limit}:{include_url}"
        cached = self.cache.get(cache_key, ttl=900)  # Cache 15 phút
        if cached:
            return cached

        # Đọc dữ liệu hôm nay
        all_titles, id_to_name, timestamps = self.parser.read_all_titles_for_date(
            date=None,
            platform_ids=platforms
        )

        # Lấy thời gian file mới nhất
        if timestamps:
            latest_timestamp = max(timestamps.values())
            fetch_time = datetime.fromtimestamp(latest_timestamp)
        else:
            fetch_time = datetime.now()

        # Chuyển đổi thành danh sách tin tức
        news_list = []
        for platform_id, titles in all_titles.items():
            platform_name = id_to_name.get(platform_id, platform_id)

            for title, info in titles.items():
                # Lấy thứ hạng đầu tiên
                rank = info["ranks"][0] if info["ranks"] else 0

                news_item = {
                    "title": title,
                    "platform": platform_id,
                    "platform_name": platform_name,
                    "rank": rank,
                    "timestamp": fetch_time.strftime("%Y-%m-%d %H:%M:%S")
                }

                # Thêm trường URL có điều kiện
                if include_url:
                    news_item["url"] = info.get("url", "")
                    news_item["mobileUrl"] = info.get("mobileUrl", "")

                news_list.append(news_item)

        # Sắp xếp theo thứ hạng
        news_list.sort(key=lambda x: x["rank"])

        # Giới hạn số lượng trả về
        result = news_list[:limit]

        # Lưu kết quả vào cache
        self.cache.set(cache_key, result)

        return result

    def get_news_by_date(
        self,
        target_date: datetime,
        platforms: Optional[List[str]] = None,
        limit: int = 50,
        include_url: bool = False
    ) -> List[Dict]:
        """
        Lấy tin tức theo ngày chỉ định

        Args:
            target_date: Ngày mục tiêu
            platforms: Danh sách ID nền tảng, None nghĩa là tất cả nền tảng
            limit: Giới hạn số lượng trả về
            include_url: Có bao gồm liên kết URL không, mặc định False (tiết kiệm token)

        Returns:
            Danh sách tin tức

        Raises:
            DataNotFoundError: Dữ liệu không tồn tại

        Examples:
            >>> service = DataService()
            >>> news = service.get_news_by_date(
            ...     target_date=datetime(2025, 10, 10),
            ...     platforms=['zhihu'],
            ...     limit=20
            ... )
        """
        # Thử lấy từ cache
        date_str = target_date.strftime("%Y-%m-%d")
        cache_key = f"news_by_date:{date_str}:{','.join(platforms or [])}:{limit}:{include_url}"
        cached = self.cache.get(cache_key, ttl=1800)  # Cache 30 phút
        if cached:
            return cached

        # Đọc dữ liệu của ngày chỉ định
        all_titles, id_to_name, timestamps = self.parser.read_all_titles_for_date(
            date=target_date,
            platform_ids=platforms
        )

        # Chuyển đổi thành danh sách tin tức
        news_list = []
        for platform_id, titles in all_titles.items():
            platform_name = id_to_name.get(platform_id, platform_id)

            for title, info in titles.items():
                # Tính thứ hạng trung bình
                avg_rank = sum(info["ranks"]) / len(info["ranks"]) if info["ranks"] else 0

                news_item = {
                    "title": title,
                    "platform": platform_id,
                    "platform_name": platform_name,
                    "rank": info["ranks"][0] if info["ranks"] else 0,
                    "avg_rank": round(avg_rank, 2),
                    "count": len(info["ranks"]),
                    "date": date_str
                }

                # Thêm trường URL có điều kiện
                if include_url:
                    news_item["url"] = info.get("url", "")
                    news_item["mobileUrl"] = info.get("mobileUrl", "")

                news_list.append(news_item)

        # Sắp xếp theo thứ hạng
        news_list.sort(key=lambda x: x["rank"])

        # Giới hạn số lượng trả về
        result = news_list[:limit]

        # Lưu kết quả vào cache (dữ liệu lịch sử cache lâu hơn)
        self.cache.set(cache_key, result)

        return result

    def search_news_by_keyword(
        self,
        keyword: str,
        date_range: Optional[Tuple[datetime, datetime]] = None,
        platforms: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> Dict:
        """
        Tìm kiếm tin tức theo từ khóa

        Args:
            keyword: Từ khóa tìm kiếm
            date_range: Phạm vi ngày (start_date, end_date)
            platforms: Danh sách nền tảng để lọc
            limit: Giới hạn số lượng trả về (tùy chọn)

        Returns:
            Dictionary kết quả tìm kiếm

        Raises:
            DataNotFoundError: Dữ liệu không tồn tại
        """
        # Xác định phạm vi ngày tìm kiếm
        if date_range:
            start_date, end_date = date_range
        else:
            # Mặc định tìm kiếm hôm nay
            start_date = end_date = datetime.now()

        # Thu thập tất cả tin tức khớp
        results = []
        platform_distribution = Counter()

        # Duyệt qua phạm vi ngày
        current_date = start_date
        while current_date <= end_date:
            try:
                all_titles, id_to_name, _ = self.parser.read_all_titles_for_date(
                    date=current_date,
                    platform_ids=platforms
                )

                # Tìm kiếm tiêu đề chứa từ khóa
                for platform_id, titles in all_titles.items():
                    platform_name = id_to_name.get(platform_id, platform_id)

                    for title, info in titles.items():
                        if keyword.lower() in title.lower():
                            # Tính thứ hạng trung bình
                            avg_rank = sum(info["ranks"]) / len(info["ranks"]) if info["ranks"] else 0

                            results.append({
                                "title": title,
                                "platform": platform_id,
                                "platform_name": platform_name,
                                "ranks": info["ranks"],
                                "count": len(info["ranks"]),
                                "avg_rank": round(avg_rank, 2),
                                "url": info.get("url", ""),
                                "mobileUrl": info.get("mobileUrl", ""),
                                "date": current_date.strftime("%Y-%m-%d")
                            })

                            platform_distribution[platform_id] += 1

            except DataNotFoundError:
                # Ngày đó không có dữ liệu, tiếp tục ngày tiếp theo
                pass

            # Ngày tiếp theo
            current_date += timedelta(days=1)

        if not results:
            raise DataNotFoundError(
                f"Không tìm thấy tin tức chứa từ khóa '{keyword}'",
                suggestion="Vui lòng thử từ khóa khác hoặc mở rộng phạm vi ngày"
            )

        # Tính thông tin thống kê
        total_ranks = []
        for item in results:
            total_ranks.extend(item["ranks"])

        avg_rank = sum(total_ranks) / len(total_ranks) if total_ranks else 0

        # Giới hạn số lượng trả về (nếu được chỉ định)
        total_found = len(results)
        if limit is not None and limit > 0:
            results = results[:limit]

        return {
            "results": results,
            "total": len(results),
            "total_found": total_found,
            "statistics": {
                "platform_distribution": dict(platform_distribution),
                "avg_rank": round(avg_rank, 2),
                "keyword": keyword
            }
        }

    def get_trending_topics(
        self,
        top_n: int = 10,
        mode: str = "current"
    ) -> Dict:
        """
        Lấy thống kê tần suất xuất hiện của các từ khóa quan tâm cá nhân

        Lưu ý: Công cụ này dựa trên danh sách từ khóa quan tâm cá nhân trong config/frequency_words.txt,
        không phải tự động trích xuất chủ đề hot từ tin tức. Người dùng có thể tùy chỉnh danh sách từ khóa này.

        Args:
            top_n: Trả về TOP N từ khóa quan tâm
            mode: Chế độ - daily (tích lũy trong ngày), current (đợt mới nhất)

        Returns:
            Dictionary thống kê tần suất từ khóa quan tâm

        Raises:
            DataNotFoundError: Dữ liệu không tồn tại
        """
        # Thử lấy từ cache
        cache_key = f"trending_topics:{top_n}:{mode}"
        cached = self.cache.get(cache_key, ttl=1800)  # Cache 30 phút
        if cached:
            return cached

        # Đọc dữ liệu hôm nay
        all_titles, id_to_name, timestamps = self.parser.read_all_titles_for_date()

        if not all_titles:
            raise DataNotFoundError(
                "Không tìm thấy dữ liệu tin tức hôm nay",
                suggestion="Vui lòng đảm bảo crawler đã chạy và tạo dữ liệu"
            )

        # Tải cấu hình từ khóa
        word_groups = self.parser.parse_frequency_words()

        # Chọn dữ liệu tiêu đề để xử lý theo mode
        titles_to_process = {}

        if mode == "daily":
            # Chế độ daily: xử lý tất cả dữ liệu tích lũy trong ngày
            titles_to_process = all_titles

        elif mode == "current":
            # Chế độ current: chỉ xử lý đợt dữ liệu mới nhất (timestamp mới nhất)
            if timestamps:
                # Tìm timestamp mới nhất
                latest_timestamp = max(timestamps.values())

                # Đọc lại, chỉ lấy dữ liệu thời gian mới nhất
                # Ở đây ta tra ngược timestamps để tìm nền tảng tương ứng với file mới nhất
                latest_titles, _, _ = self.parser.read_all_titles_for_date()

                # Vì read_all_titles_for_date trả về dữ liệu hợp nhất của tất cả file,
                # chúng ta cần lọc theo timestamps để lấy đợt mới nhất
                # Đơn giản hóa: sử dụng tất cả dữ liệu hiện tại làm đợt mới nhất
                # (triển khai chính xác hơn cần dịch vụ phân tích hỗ trợ lọc theo thời gian)
                titles_to_process = latest_titles
            else:
                titles_to_process = all_titles

        else:
            raise ValueError(
                f"Chế độ không được hỗ trợ: {mode}. Các chế độ hỗ trợ: daily, current"
            )

        # Thống kê tần suất từ
        word_frequency = Counter()
        keyword_to_news = {}

        # Duyệt qua các tiêu đề cần xử lý
        for platform_id, titles in titles_to_process.items():
            for title in titles.keys():
                # Khớp với từng nhóm từ khóa
                for group in word_groups:
                    all_words = group.get("required", []) + group.get("normal", [])

                    for word in all_words:
                        if word and word in title:
                            word_frequency[word] += 1

                            if word not in keyword_to_news:
                                keyword_to_news[word] = []
                            keyword_to_news[word].append(title)

        # Lấy TOP N từ khóa
        top_keywords = word_frequency.most_common(top_n)

        # Xây dựng danh sách chủ đề
        topics = []
        for keyword, frequency in top_keywords:
            matched_news = keyword_to_news.get(keyword, [])

            topics.append({
                "keyword": keyword,
                "frequency": frequency,
                "matched_news": len(set(matched_news)),  # Số lượng tin tức sau khi loại trùng
                "trend": "stable",  # TODO: Cần dữ liệu lịch sử để tính xu hướng
                "weight_score": 0.0  # TODO: Cần triển khai tính điểm trọng số
            })

        # Xây dựng kết quả
        result = {
            "topics": topics,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "mode": mode,
            "total_keywords": len(word_frequency),
            "description": self._get_mode_description(mode)
        }

        # Lưu kết quả vào cache
        self.cache.set(cache_key, result)

        return result

    def _get_mode_description(self, mode: str) -> str:
        """Lấy mô tả chế độ"""
        descriptions = {
            "daily": "Thống kê tích lũy trong ngày",
            "current": "Thống kê đợt mới nhất"
        }
        return descriptions.get(mode, "Chế độ không xác định")

    def get_current_config(self, section: str = "all") -> Dict:
        """
        Lấy cấu hình hệ thống hiện tại

        Args:
            section: Phần cấu hình - all/crawler/push/keywords/weights

        Returns:
            Dictionary cấu hình

        Raises:
            FileParseError: Lỗi phân tích file cấu hình
        """
        # Thử lấy từ cache
        cache_key = f"config:{section}"
        cached = self.cache.get(cache_key, ttl=3600)  # Cache 1 giờ
        if cached:
            return cached

        # Phân tích file cấu hình
        config_data = self.parser.parse_yaml_config()
        word_groups = self.parser.parse_frequency_words()

        # Trả về cấu hình tương ứng theo section
        if section == "all" or section == "crawler":
            crawler_config = {
                "enable_crawler": config_data.get("crawler", {}).get("enable_crawler", True),
                "use_proxy": config_data.get("crawler", {}).get("use_proxy", False),
                "request_interval": config_data.get("crawler", {}).get("request_interval", 1),
                "retry_times": 3,
                "platforms": [p["id"] for p in config_data.get("platforms", [])]
            }

        if section == "all" or section == "push":
            push_config = {
                "enable_notification": config_data.get("notification", {}).get("enable_notification", True),
                "enabled_channels": [],
                "message_batch_size": config_data.get("notification", {}).get("message_batch_size", 20),
                "push_window": config_data.get("notification", {}).get("push_window", {})
            }

            # Phát hiện các kênh thông báo đã cấu hình
            webhooks = config_data.get("notification", {}).get("webhooks", {})
            if webhooks.get("feishu_url"):
                push_config["enabled_channels"].append("feishu")
            if webhooks.get("dingtalk_url"):
                push_config["enabled_channels"].append("dingtalk")
            if webhooks.get("wework_url"):
                push_config["enabled_channels"].append("wework")

        if section == "all" or section == "keywords":
            keywords_config = {
                "word_groups": word_groups,
                "total_groups": len(word_groups)
            }

        if section == "all" or section == "weights":
            weights_config = {
                "rank_weight": config_data.get("weight", {}).get("rank_weight", 0.6),
                "frequency_weight": config_data.get("weight", {}).get("frequency_weight", 0.3),
                "hotness_weight": config_data.get("weight", {}).get("hotness_weight", 0.1)
            }

        # Tổ hợp kết quả
        if section == "all":
            result = {
                "crawler": crawler_config,
                "push": push_config,
                "keywords": keywords_config,
                "weights": weights_config
            }
        elif section == "crawler":
            result = crawler_config
        elif section == "push":
            result = push_config
        elif section == "keywords":
            result = keywords_config
        elif section == "weights":
            result = weights_config
        else:
            result = {}

        # Lưu kết quả vào cache
        self.cache.set(cache_key, result)

        return result

    def get_available_date_range(self) -> Tuple[Optional[datetime], Optional[datetime]]:
        """
        Quét thư mục output, trả về phạm vi ngày thực tế có sẵn

        Returns:
            Tuple (ngày sớm nhất, ngày mới nhất), nếu không có dữ liệu trả về (None, None)

        Examples:
            >>> service = DataService()
            >>> earliest, latest = service.get_available_date_range()
            >>> print(f"Phạm vi ngày có sẵn: {earliest} đến {latest}")
        """
        output_dir = self.parser.project_root / "output"

        if not output_dir.exists():
            return (None, None)

        available_dates = []

        # Duyệt qua các thư mục ngày
        for date_folder in output_dir.iterdir():
            if date_folder.is_dir() and not date_folder.name.startswith('.'):
                # Phân tích ngày (định dạng: YYYY năm MM tháng DD ngày)
                try:
                    date_match = re.match(r'(\d{4})năm(\d{2})tháng(\d{2})ngày', date_folder.name)
                    if date_match:
                        folder_date = datetime(
                            int(date_match.group(1)),
                            int(date_match.group(2)),
                            int(date_match.group(3))
                        )
                        available_dates.append(folder_date)
                except Exception:
                    pass

        if not available_dates:
            return (None, None)

        return (min(available_dates), max(available_dates))

    def get_system_status(self) -> Dict:
        """
        Lấy trạng thái vận hành hệ thống

        Returns:
            Dictionary trạng thái hệ thống
        """
        # Lấy thống kê dữ liệu
        output_dir = self.parser.project_root / "output"

        total_storage = 0
        oldest_record = None
        latest_record = None
        total_news = 0

        if output_dir.exists():
            # Duyệt qua các thư mục ngày
            for date_folder in output_dir.iterdir():
                if date_folder.is_dir():
                    # Phân tích ngày
                    try:
                        date_str = date_folder.name
                        # Định dạng: YYYY năm MM tháng DD ngày
                        date_match = re.match(r'(\d{4})năm(\d{2})tháng(\d{2})ngày', date_str)
                        if date_match:
                            folder_date = datetime(
                                int(date_match.group(1)),
                                int(date_match.group(2)),
                                int(date_match.group(3))
                            )

                            if oldest_record is None or folder_date < oldest_record:
                                oldest_record = folder_date
                            if latest_record is None or folder_date > latest_record:
                                latest_record = folder_date

                    except:
                        pass

                    # Tính kích thước lưu trữ
                    for item in date_folder.rglob("*"):
                        if item.is_file():
                            total_storage += item.stat().st_size

        # Đọc thông tin phiên bản
        version_file = self.parser.project_root / "version"
        version = "unknown"
        if version_file.exists():
            try:
                with open(version_file, "r") as f:
                    version = f.read().strip()
            except:
                pass

        return {
            "system": {
                "version": version,
                "project_root": str(self.parser.project_root)
            },
            "data": {
                "total_storage": f"{total_storage / 1024 / 1024:.2f} MB",
                "oldest_record": oldest_record.strftime("%Y-%m-%d") if oldest_record else None,
                "latest_record": latest_record.strftime("%Y-%m-%d") if latest_record else None,
            },
            "cache": self.cache.get_stats(),
            "health": "healthy"
        }
