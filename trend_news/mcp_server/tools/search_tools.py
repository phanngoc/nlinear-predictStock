"""
Công cụ tìm kiếm tin tức thông minh

Cung cấp các chức năng tìm kiếm nâng cao như tìm kiếm mờ, truy vấn liên kết, tìm kiếm tin tức liên quan trong lịch sử.
"""

import re
from collections import Counter
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple

from ..services.data_service import DataService
from ..utils.validators import validate_keyword, validate_limit
from ..utils.errors import MCPError, InvalidParameterError, DataNotFoundError


class SearchTools:
    """Lớp công cụ tìm kiếm tin tức thông minh"""

    def __init__(self, project_root: str = None):
        """
        Khởi tạo công cụ tìm kiếm thông minh

        Args:
            project_root: Thư mục gốc của dự án
        """
        self.data_service = DataService(project_root)
        # Danh sách từ dừng tiếng Trung
        self.stopwords = {
            'của', 'rồi', 'ở', 'là', 'tôi', 'có', 'và', 'thì', 'không', 'người', 'đều', 'một',
            'một', 'trên', 'cũng', 'rất', 'đến', 'nói', 'muốn', 'đi', 'bạn', 'sẽ', 'đang', 'không có',
            'xem', 'tốt', 'tự mình', 'này', 'kia', 'đến', 'bị', 'với', 'vì', 'đối', 'sẽ', 'từ',
            'để', 'và', 'v.v.', 'nhưng', 'hoặc', 'mà', 'ở', 'trong', 'do', 'có thể', 'có thể', 'đã',
            'đã', 'còn', 'hơn', 'nhất', 'lại', 'vì', 'nên', 'nếu', 'mặc dù', 'tuy nhiên'
        }

    def search_news_unified(
        self,
        query: str,
        search_mode: str = "keyword",
        date_range: Optional[Dict[str, str]] = None,
        platforms: Optional[List[str]] = None,
        limit: int = 50,
        sort_by: str = "relevance",
        threshold: float = 0.6,
        include_url: bool = False
    ) -> Dict:
        """
        Công cụ tìm kiếm tin tức thống nhất - Tích hợp nhiều chế độ tìm kiếm

        Args:
            query: Nội dung truy vấn (bắt buộc) - từ khóa, đoạn nội dung hoặc tên thực thể
            search_mode: Chế độ tìm kiếm, các giá trị:
                - "keyword": Khớp từ khóa chính xác (mặc định)
                - "fuzzy": Khớp nội dung mờ (sử dụng thuật toán tương tự)
                - "entity": Tìm kiếm tên thực thể (tự động sắp xếp theo trọng số)
            date_range: Phạm vi ngày (tùy chọn)
                       - **Định dạng**: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                       - **Ví dụ**: {"start": "2025-01-01", "end": "2025-01-07"}
                       - **Mặc định**: Không chỉ định thì mặc định truy vấn hôm nay
                       - **Lưu ý**: start và end có thể giống nhau (truy vấn ngày đơn)
            platforms: Danh sách lọc nền tảng, ví dụ ['zhihu', 'weibo']
            limit: Giới hạn số lượng trả về, mặc định 50
            sort_by: Cách sắp xếp, các giá trị:
                - "relevance": Sắp xếp theo độ liên quan (mặc định)
                - "weight": Sắp xếp theo trọng số tin tức
                - "date": Sắp xếp theo ngày
            threshold: Ngưỡng tương tự (chỉ có hiệu lực ở chế độ fuzzy), 0-1, mặc định 0.6
            include_url: Có bao gồm liên kết URL không, mặc định False (tiết kiệm token)

        Returns:
            Dictionary kết quả tìm kiếm, bao gồm danh sách tin tức khớp

        Ví dụ:
            - search_news_unified(query="trí tuệ nhân tạo", search_mode="keyword")
            - search_news_unified(query="特斯拉降价", search_mode="fuzzy", threshold=0.4)
            - search_news_unified(query="马斯克", search_mode="entity", limit=20)
            - search_news_unified(query="iPhone 16", date_range={"start": "2025-01-01", "end": "2025-01-07"})
        """
        try:
            # Xác thực tham số
            query = validate_keyword(query)

            if search_mode not in ["keyword", "fuzzy", "entity"]:
                raise InvalidParameterError(
                    f"Chế độ tìm kiếm không hợp lệ: {search_mode}",
                    suggestion="Các chế độ hỗ trợ: keyword, fuzzy, entity"
                )

            if sort_by not in ["relevance", "weight", "date"]:
                raise InvalidParameterError(
                    f"Cách sắp xếp không hợp lệ: {sort_by}",
                    suggestion="Các cách sắp xếp hỗ trợ: relevance, weight, date"
                )

            limit = validate_limit(limit, default=50)
            threshold = max(0.0, min(1.0, threshold))

            # Xử lý phạm vi ngày
            if date_range:
                from ..utils.validators import validate_date_range
                date_range_tuple = validate_date_range(date_range)
                start_date, end_date = date_range_tuple
            else:
                # Khi không chỉ định ngày, sử dụng ngày dữ liệu khả dụng mới nhất (không phải datetime.now())
                earliest, latest = self.data_service.get_available_date_range()

                if latest is None:
                    # Không có dữ liệu khả dụng
                    return {
                        "success": False,
                        "error": {
                            "code": "NO_DATA_AVAILABLE",
                            "message": "Không có dữ liệu tin tức khả dụng trong thư mục output",
                            "suggestion": "Vui lòng chạy crawler để tạo dữ liệu hoặc kiểm tra thư mục output"
                        }
                    }

                # Sử dụng ngày khả dụng mới nhất
                start_date = end_date = latest

            # Thu thập tất cả tin tức khớp
            all_matches = []
            current_date = start_date

            while current_date <= end_date:
                try:
                    all_titles, id_to_name, timestamps = self.data_service.parser.read_all_titles_for_date(
                        date=current_date,
                        platform_ids=platforms
                    )

                    # Thực hiện logic tìm kiếm khác nhau theo chế độ tìm kiếm
                    if search_mode == "keyword":
                        matches = self._search_by_keyword_mode(
                            query, all_titles, id_to_name, current_date, include_url
                        )
                    elif search_mode == "fuzzy":
                        matches = self._search_by_fuzzy_mode(
                            query, all_titles, id_to_name, current_date, threshold, include_url
                        )
                    else:  # entity
                        matches = self._search_by_entity_mode(
                            query, all_titles, id_to_name, current_date, include_url
                        )

                    all_matches.extend(matches)

                except DataNotFoundError:
                    # Ngày đó không có dữ liệu, tiếp tục ngày tiếp theo
                    pass

                current_date += timedelta(days=1)

            if not all_matches:
                # Lấy phạm vi ngày khả dụng để hiển thị gợi ý lỗi
                earliest, latest = self.data_service.get_available_date_range()

                # Xác định mô tả phạm vi thời gian
                if start_date.date() == datetime.now().date() and start_date == end_date:
                    time_desc = "hôm nay"
                elif start_date == end_date:
                    time_desc = start_date.strftime("%Y-%m-%d")
                else:
                    time_desc = f"{start_date.strftime('%Y-%m-%d')} đến {end_date.strftime('%Y-%m-%d')}"

                # Xây dựng thông báo lỗi
                if earliest and latest:
                    available_desc = f"{earliest.strftime('%Y-%m-%d')} đến {latest.strftime('%Y-%m-%d')}"
                    message = f"Không tìm thấy tin tức khớp (phạm vi truy vấn: {time_desc}, dữ liệu khả dụng: {available_desc})"
                else:
                    message = f"Không tìm thấy tin tức khớp ({time_desc})"

                result = {
                    "success": True,
                    "results": [],
                    "total": 0,
                    "query": query,
                    "search_mode": search_mode,
                    "time_range": time_desc,
                    "message": message
                }
                return result

            # Logic sắp xếp thống nhất
            if sort_by == "relevance":
                all_matches.sort(key=lambda x: x.get("similarity_score", 1.0), reverse=True)
            elif sort_by == "weight":
                from .analytics import calculate_news_weight
                all_matches.sort(key=lambda x: calculate_news_weight(x), reverse=True)
            elif sort_by == "date":
                all_matches.sort(key=lambda x: x.get("date", ""), reverse=True)

            # Giới hạn số lượng trả về
            results = all_matches[:limit]

            # Xây dựng mô tả phạm vi thời gian (xác định chính xác có phải hôm nay không)
            if start_date.date() == datetime.now().date() and start_date == end_date:
                time_range_desc = "hôm nay"
            elif start_date == end_date:
                time_range_desc = start_date.strftime("%Y-%m-%d")
            else:
                time_range_desc = f"{start_date.strftime('%Y-%m-%d')} đến {end_date.strftime('%Y-%m-%d')}"

            result = {
                "success": True,
                "summary": {
                    "total_found": len(all_matches),
                    "returned_count": len(results),
                    "requested_limit": limit,
                    "search_mode": search_mode,
                    "query": query,
                    "platforms": platforms or "tất cả nền tảng",
                    "time_range": time_range_desc,
                    "sort_by": sort_by
                },
                "results": results
            }

            if search_mode == "fuzzy":
                result["summary"]["threshold"] = threshold
                if len(all_matches) < limit:
                    result["note"] = f"Ở chế độ tìm kiếm mờ, ngưỡng tương tự {threshold} chỉ khớp được {len(all_matches)} kết quả"

            return result

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

    def _search_by_keyword_mode(
        self,
        query: str,
        all_titles: Dict,
        id_to_name: Dict,
        current_date: datetime,
        include_url: bool
    ) -> List[Dict]:
        """
        Chế độ tìm kiếm từ khóa (khớp chính xác)

        Args:
            query: Từ khóa tìm kiếm
            all_titles: Dictionary tất cả tiêu đề
            id_to_name: Ánh xạ ID nền tảng sang tên
            current_date: Ngày hiện tại

        Returns:
            Danh sách tin tức khớp
        """
        matches = []
        query_lower = query.lower()

        for platform_id, titles in all_titles.items():
            platform_name = id_to_name.get(platform_id, platform_id)

            for title, info in titles.items():
                # Kiểm tra chứa chính xác
                if query_lower in title.lower():
                    news_item = {
                        "title": title,
                        "platform": platform_id,
                        "platform_name": platform_name,
                        "date": current_date.strftime("%Y-%m-%d"),
                        "similarity_score": 1.0,  # Khớp chính xác, độ tương tự là 1
                        "ranks": info.get("ranks", []),
                        "count": len(info.get("ranks", [])),
                        "rank": info["ranks"][0] if info["ranks"] else 999
                    }

                    # Thêm trường URL có điều kiện
                    if include_url:
                        news_item["url"] = info.get("url", "")
                        news_item["mobileUrl"] = info.get("mobileUrl", "")

                    matches.append(news_item)

        return matches

    def _search_by_fuzzy_mode(
        self,
        query: str,
        all_titles: Dict,
        id_to_name: Dict,
        current_date: datetime,
        threshold: float,
        include_url: bool
    ) -> List[Dict]:
        """
        Chế độ tìm kiếm mờ (sử dụng thuật toán tương tự)

        Args:
            query: Nội dung tìm kiếm
            all_titles: Dictionary tất cả tiêu đề
            id_to_name: Ánh xạ ID nền tảng sang tên
            current_date: Ngày hiện tại
            threshold: Ngưỡng tương tự

        Returns:
            Danh sách tin tức khớp
        """
        matches = []

        for platform_id, titles in all_titles.items():
            platform_name = id_to_name.get(platform_id, platform_id)

            for title, info in titles.items():
                # Khớp mờ
                is_match, similarity = self._fuzzy_match(query, title, threshold)

                if is_match:
                    news_item = {
                        "title": title,
                        "platform": platform_id,
                        "platform_name": platform_name,
                        "date": current_date.strftime("%Y-%m-%d"),
                        "similarity_score": round(similarity, 4),
                        "ranks": info.get("ranks", []),
                        "count": len(info.get("ranks", [])),
                        "rank": info["ranks"][0] if info["ranks"] else 999
                    }

                    # Thêm trường URL có điều kiện
                    if include_url:
                        news_item["url"] = info.get("url", "")
                        news_item["mobileUrl"] = info.get("mobileUrl", "")

                    matches.append(news_item)

        return matches

    def _search_by_entity_mode(
        self,
        query: str,
        all_titles: Dict,
        id_to_name: Dict,
        current_date: datetime,
        include_url: bool
    ) -> List[Dict]:
        """
        Chế độ tìm kiếm thực thể (tự động sắp xếp theo trọng số)

        Args:
            query: Tên thực thể
            all_titles: Dictionary tất cả tiêu đề
            id_to_name: Ánh xạ ID nền tảng sang tên
            current_date: Ngày hiện tại

        Returns:
            Danh sách tin tức khớp
        """
        matches = []

        for platform_id, titles in all_titles.items():
            platform_name = id_to_name.get(platform_id, platform_id)

            for title, info in titles.items():
                # Tìm kiếm thực thể: chứa chính xác tên thực thể
                if query in title:
                    news_item = {
                        "title": title,
                        "platform": platform_id,
                        "platform_name": platform_name,
                        "date": current_date.strftime("%Y-%m-%d"),
                        "similarity_score": 1.0,
                        "ranks": info.get("ranks", []),
                        "count": len(info.get("ranks", [])),
                        "rank": info["ranks"][0] if info["ranks"] else 999
                    }

                    # Thêm trường URL có điều kiện
                    if include_url:
                        news_item["url"] = info.get("url", "")
                        news_item["mobileUrl"] = info.get("mobileUrl", "")

                    matches.append(news_item)

        return matches

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Tính độ tương tự của hai văn bản

        Args:
            text1: Văn bản 1
            text2: Văn bản 2

        Returns:
            Điểm tương tự (từ 0-1)
        """
        # Sử dụng difflib.SequenceMatcher để tính độ tương tự chuỗi
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    def _fuzzy_match(self, query: str, text: str, threshold: float = 0.3) -> Tuple[bool, float]:
        """
        Hàm khớp mờ

        Args:
            query: Văn bản truy vấn
            text: Văn bản cần khớp
            threshold: Ngưỡng khớp

        Returns:
            (có khớp không, điểm tương tự)
        """
        # Kiểm tra chứa trực tiếp
        if query.lower() in text.lower():
            return True, 1.0

        # Tính độ tương tự tổng thể
        similarity = self._calculate_similarity(query, text)
        if similarity >= threshold:
            return True, similarity

        # Khớp từng phần sau khi tách từ
        query_words = set(self._extract_keywords(query))
        text_words = set(self._extract_keywords(text))

        if not query_words or not text_words:
            return False, 0.0

        # Tính độ trùng lặp từ khóa
        common_words = query_words & text_words
        keyword_overlap = len(common_words) / len(query_words)

        if keyword_overlap >= 0.5:  # 50% từ khóa trùng lặp
            return True, keyword_overlap

        return False, similarity

    def _extract_keywords(self, text: str, min_length: int = 2) -> List[str]:
        """
        Trích xuất từ khóa từ văn bản

        Args:
            text: Văn bản đầu vào
            min_length: Độ dài từ tối thiểu

        Returns:
            Danh sách từ khóa
        """
        # Loại bỏ URL và ký tự đặc biệt
        text = re.sub(r'http[s]?://\S+', '', text)
        text = re.sub(r'\[.*?\]', '', text)  # Loại bỏ nội dung trong ngoặc vuông

        # Sử dụng biểu thức chính quy để tách từ (tiếng Trung và tiếng Anh)
        words = re.findall(r'[\w]+', text)

        # Lọc từ dừng và từ ngắn
        keywords = [
            word for word in words
            if word and len(word) >= min_length and word not in self.stopwords
        ]

        return keywords

    def _calculate_keyword_overlap(self, keywords1: List[str], keywords2: List[str]) -> float:
        """
        Tính độ trùng lặp của hai danh sách từ khóa

        Args:
            keywords1: Danh sách từ khóa 1
            keywords2: Danh sách từ khóa 2

        Returns:
            Điểm trùng lặp (từ 0-1)
        """
        if not keywords1 or not keywords2:
            return 0.0

        set1 = set(keywords1)
        set2 = set(keywords2)

        # Độ tương tự Jaccard
        intersection = len(set1 & set2)
        union = len(set1 | set2)

        if union == 0:
            return 0.0

        return intersection / union

    def search_related_news_history(
        self,
        reference_text: str,
        time_preset: str = "yesterday",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        threshold: float = 0.4,
        limit: int = 50,
        include_url: bool = False
    ) -> Dict:
        """
        Tìm kiếm tin tức liên quan trong dữ liệu lịch sử

        Args:
            reference_text: Tiêu đề hoặc nội dung tin tức tham chiếu
            time_preset: Giá trị đặt trước phạm vi thời gian, tùy chọn:
                - "yesterday": Hôm qua
                - "last_week": Tuần trước (7 ngày)
                - "last_month": Tháng trước (30 ngày)
                - "custom": Phạm vi ngày tùy chỉnh (cần cung cấp start_date và end_date)
            start_date: Ngày bắt đầu tùy chỉnh (chỉ có hiệu lực khi time_preset="custom")
            end_date: Ngày kết thúc tùy chỉnh (chỉ có hiệu lực khi time_preset="custom")
            threshold: Ngưỡng tương tự (từ 0-1), mặc định 0.4
            limit: Giới hạn số lượng trả về, mặc định 50
            include_url: Có bao gồm liên kết URL không, mặc định False (tiết kiệm token)

        Returns:
            Dictionary kết quả tìm kiếm, bao gồm danh sách tin tức liên quan

        Ví dụ:
            >>> tools = SearchTools()
            >>> result = tools.search_related_news_history(
            ...     reference_text="trí tuệ nhân tạo技术突破",
            ...     time_preset="last_week",
            ...     threshold=0.4,
            ...     limit=50
            ... )
            >>> for news in result['results']:
            ...     print(f"{news['date']}: {news['title']} (tương tự: {news['similarity_score']})")
        """
        try:
            # Xác thực tham số
            reference_text = validate_keyword(reference_text)
            threshold = max(0.0, min(1.0, threshold))
            limit = validate_limit(limit, default=50)

            # Xác định phạm vi ngày truy vấn
            today = datetime.now()

            if time_preset == "yesterday":
                search_start = today - timedelta(days=1)
                search_end = today - timedelta(days=1)
            elif time_preset == "last_week":
                search_start = today - timedelta(days=7)
                search_end = today - timedelta(days=1)
            elif time_preset == "last_month":
                search_start = today - timedelta(days=30)
                search_end = today - timedelta(days=1)
            elif time_preset == "custom":
                if not start_date or not end_date:
                    raise InvalidParameterError(
                        "Phạm vi thời gian tùy chỉnh cần cung cấp start_date và end_date",
                        suggestion="Vui lòng cung cấp tham số start_date và end_date"
                    )
                search_start = start_date
                search_end = end_date
            else:
                raise InvalidParameterError(
                    f"Phạm vi thời gian không được hỗ trợ: {time_preset}",
                    suggestion="Vui lòng sử dụng 'yesterday', 'last_week', 'last_month' hoặc 'custom'"
                )

            # Trích xuất từ khóa từ văn bản tham chiếu
            reference_keywords = self._extract_keywords(reference_text)

            if not reference_keywords:
                raise InvalidParameterError(
                    "Không thể trích xuất từ khóa từ văn bản tham chiếu",
                    suggestion="Vui lòng cung cấp nội dung văn bản chi tiết hơn"
                )

            # Thu thập tất cả tin tức liên quan
            all_related_news = []
            current_date = search_start

            while current_date <= search_end:
                try:
                    # Đọc dữ liệu của ngày đó
                    all_titles, id_to_name, _ = self.data_service.parser.read_all_titles_for_date(current_date)

                    # Tìm kiếm tin tức liên quan
                    for platform_id, titles in all_titles.items():
                        platform_name = id_to_name.get(platform_id, platform_id)

                        for title, info in titles.items():
                            # Tính độ tương tự tiêu đề
                            title_similarity = self._calculate_similarity(reference_text, title)

                            # Trích xuất từ khóa tiêu đề
                            title_keywords = self._extract_keywords(title)

                            # Tính độ trùng lặp từ khóa
                            keyword_overlap = self._calculate_keyword_overlap(
                                reference_keywords,
                                title_keywords
                            )

                            # Độ tương tự tổng hợp (70% trùng lặp từ khóa + 30% tương tự văn bản)
                            combined_score = keyword_overlap * 0.7 + title_similarity * 0.3

                            if combined_score >= threshold:
                                news_item = {
                                    "title": title,
                                    "platform": platform_id,
                                    "platform_name": platform_name,
                                    "date": current_date.strftime("%Y-%m-%d"),
                                    "similarity_score": round(combined_score, 4),
                                    "keyword_overlap": round(keyword_overlap, 4),
                                    "text_similarity": round(title_similarity, 4),
                                    "common_keywords": list(set(reference_keywords) & set(title_keywords)),
                                    "rank": info["ranks"][0] if info["ranks"] else 0
                                }

                                # Thêm trường URL có điều kiện
                                if include_url:
                                    news_item["url"] = info.get("url", "")
                                    news_item["mobileUrl"] = info.get("mobileUrl", "")

                                all_related_news.append(news_item)

                except DataNotFoundError:
                    # Ngày đó không có dữ liệu, tiếp tục ngày tiếp theo
                    pass
                except Exception as e:
                    # Ghi nhận lỗi nhưng tiếp tục xử lý các ngày khác
                    print(f"Cảnh báo: Xử lý ngày {current_date.strftime('%Y-%m-%d')} bị lỗi: {e}")

                # Chuyển sang ngày tiếp theo
                current_date += timedelta(days=1)

            if not all_related_news:
                return {
                    "success": True,
                    "results": [],
                    "total": 0,
                    "query": reference_text,
                    "time_preset": time_preset,
                    "date_range": {
                        "start": search_start.strftime("%Y-%m-%d"),
                        "end": search_end.strftime("%Y-%m-%d")
                    },
                    "message": "Không tìm thấy tin tức liên quan"
                }

            # Sắp xếp theo độ tương tự
            all_related_news.sort(key=lambda x: x["similarity_score"], reverse=True)

            # Giới hạn số lượng trả về
            results = all_related_news[:limit]

            # Thông tin thống kê
            platform_distribution = Counter([news["platform"] for news in all_related_news])
            date_distribution = Counter([news["date"] for news in all_related_news])

            result = {
                "success": True,
                "summary": {
                    "total_found": len(all_related_news),
                    "returned_count": len(results),
                    "requested_limit": limit,
                    "threshold": threshold,
                    "reference_text": reference_text,
                    "reference_keywords": reference_keywords,
                    "time_preset": time_preset,
                    "date_range": {
                        "start": search_start.strftime("%Y-%m-%d"),
                        "end": search_end.strftime("%Y-%m-%d")
                    }
                },
                "results": results,
                "statistics": {
                    "platform_distribution": dict(platform_distribution),
                    "date_distribution": dict(date_distribution),
                    "avg_similarity": round(
                        sum([news["similarity_score"] for news in all_related_news]) / len(all_related_news),
                        4
                    ) if all_related_news else 0.0
                }
            }

            if len(all_related_news) < limit:
                result["note"] = f"Với ngưỡng liên quan {threshold}, chỉ tìm thấy {len(all_related_news)} tin tức liên quan"

            return result

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
