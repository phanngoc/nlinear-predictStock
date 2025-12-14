"""
TrendRadar MCP Server - Triển khai FastMCP 2.0

Sử dụng FastMCP 2.0 để cung cấp MCP tool server cấp production.
Hỗ trợ hai chế độ truyền tải: stdio và HTTP.
"""

import json
from typing import List, Optional, Dict

from fastmcp import FastMCP

from .tools.data_query import DataQueryTools
from .tools.analytics import AnalyticsTools
from .tools.search_tools import SearchTools
from .tools.config_mgmt import ConfigManagementTools
from .tools.system import SystemManagementTools


# Tạo ứng dụng FastMCP 2.0
mcp = FastMCP('trendradar-news')

# Instance công cụ toàn cục (được khởi tạo khi có request đầu tiên)
_tools_instances = {}


def _get_tools(project_root: Optional[str] = None):
    """Lấy hoặc tạo instance công cụ (singleton pattern)"""
    if not _tools_instances:
        _tools_instances['data'] = DataQueryTools(project_root)
        _tools_instances['analytics'] = AnalyticsTools(project_root)
        _tools_instances['search'] = SearchTools(project_root)
        _tools_instances['config'] = ConfigManagementTools(project_root)
        _tools_instances['system'] = SystemManagementTools(project_root)
    return _tools_instances


# ==================== Công cụ truy vấn dữ liệu ====================

@mcp.tool
async def get_latest_news(
    platforms: Optional[List[str]] = None,
    limit: int = 50,
    include_url: bool = False
) -> str:
    """
    Lấy dữ liệu tin tức mới nhất được thu thập, nhanh chóng nắm bắt các hot topic hiện tại

    Args:
        platforms: Danh sách ID nền tảng, ví dụ ['zhihu', 'weibo', 'douyin']
                   - Nếu không chỉ định: sử dụng tất cả nền tảng được cấu hình trong config.yaml
                   - Các nền tảng được hỗ trợ từ cấu hình platforms trong config/config.yaml
                   - Mỗi nền tảng có trường name tương ứng (như "Zhihu", "Weibo"), giúp AI dễ nhận biết
        limit: Giới hạn số lượng trả về, mặc định 50, tối đa 1000
               Lưu ý: Số lượng thực tế trả về có thể ít hơn giá trị yêu cầu, tùy thuộc vào tổng số tin tức hiện có
        include_url: Có bao gồm URL link không, mặc định False (tiết kiệm token)

    Returns:
        Danh sách tin tức định dạng JSON

    **Quan trọng: Khuyến nghị hiển thị dữ liệu**
    Công cụ này sẽ trả về danh sách tin tức đầy đủ (thường 50 bài) cho bạn. Nhưng lưu ý:
    - **Công cụ trả về**: Đầy đủ 50 bài dữ liệu ✅
    - **Khuyến nghị hiển thị**: Hiển thị toàn bộ dữ liệu cho người dùng, trừ khi họ yêu cầu tóm tắt rõ ràng
    - **Kỳ vọng người dùng**: Người dùng có thể cần dữ liệu đầy đủ, hãy cẩn thận khi tóm tắt

    **Khi nào có thể tóm tắt**:
    - Người dùng nói rõ "tóm tắt giúp tôi" hoặc "chọn điểm chính"
    - Khi dữ liệu vượt quá 100 bài, có thể hiển thị một phần và hỏi xem có muốn xem toàn bộ không

    **Lưu ý**: Nếu người dùng hỏi "tại sao chỉ hiển thị một phần", nghĩa là họ cần dữ liệu đầy đủ
    """
    tools = _get_tools()
    result = tools['data'].get_latest_news(platforms=platforms, limit=limit, include_url=include_url)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def get_trending_topics(
    top_n: int = 10,
    mode: str = 'current'
) -> str:
    """
    Lấy thống kê tần suất xuất hiện của từ khóa quan tâm cá nhân trong tin tức (dựa trên config/frequency_words.txt)

    Lưu ý: Công cụ này không tự động trích xuất hot topic từ tin tức, mà thống kê tần suất
    các từ khóa quan tâm cá nhân mà bạn đã thiết lập trong config/frequency_words.txt xuất hiện trong tin tức.
    Bạn có thể tùy chỉnh danh sách từ khóa quan tâm này.

    Args:
        top_n: Trả về TOP N từ khóa quan tâm, mặc định 10
        mode: Lựa chọn chế độ
            - daily: Thống kê dữ liệu tích lũy trong ngày
            - current: Thống kê dữ liệu batch mới nhất (mặc định)

    Returns:
        Danh sách thống kê tần suất từ khóa quan tâm định dạng JSON
    """
    tools = _get_tools()
    result = tools['data'].get_trending_topics(top_n=top_n, mode=mode)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def get_news_by_date(
    date_query: Optional[str] = None,
    platforms: Optional[List[str]] = None,
    limit: int = 50,
    include_url: bool = False
) -> str:
    """
    Lấy dữ liệu tin tức theo ngày chỉ định, dùng cho phân tích và so sánh dữ liệu lịch sử

    Args:
        date_query: Truy vấn ngày, các định dạng có thể:
            - Ngôn ngữ tự nhiên: "hôm nay", "hôm qua", "hôm kia", "3 ngày trước"
            - Định dạng chuẩn: "2024-01-15", "2024/01/15"
            - Giá trị mặc định: "hôm nay" (tiết kiệm token)
        platforms: Danh sách ID nền tảng, ví dụ ['zhihu', 'weibo', 'douyin']
                   - Nếu không chỉ định: sử dụng tất cả nền tảng được cấu hình trong config.yaml
                   - Các nền tảng được hỗ trợ từ cấu hình platforms trong config/config.yaml
                   - Mỗi nền tảng có trường name tương ứng (như "Zhihu", "Weibo"), giúp AI dễ nhận biết
        limit: Giới hạn số lượng trả về, mặc định 50, tối đa 1000
               Lưu ý: Số lượng thực tế trả về có thể ít hơn giá trị yêu cầu, tùy thuộc vào tổng số tin tức của ngày chỉ định
        include_url: Có bao gồm URL link không, mặc định False (tiết kiệm token)

    Returns:
        Danh sách tin tức định dạng JSON, bao gồm tiêu đề, nền tảng, thứ hạng và các thông tin khác

    **Quan trọng: Khuyến nghị hiển thị dữ liệu**
    Công cụ này sẽ trả về danh sách tin tức đầy đủ (thường 50 bài) cho bạn. Nhưng lưu ý:
    - **Công cụ trả về**: Đầy đủ 50 bài dữ liệu ✅
    - **Khuyến nghị hiển thị**: Hiển thị toàn bộ dữ liệu cho người dùng, trừ khi họ yêu cầu tóm tắt rõ ràng
    - **Kỳ vọng người dùng**: Người dùng có thể cần dữ liệu đầy đủ, hãy cẩn thận khi tóm tắt

    **Khi nào có thể tóm tắt**:
    - Người dùng nói rõ "tóm tắt giúp tôi" hoặc "chọn điểm chính"
    - Khi dữ liệu vượt quá 100 bài, có thể hiển thị một phần và hỏi xem có muốn xem toàn bộ không

    **Lưu ý**: Nếu người dùng hỏi "tại sao chỉ hiển thị một phần", nghĩa là họ cần dữ liệu đầy đủ
    """
    tools = _get_tools()
    result = tools['data'].get_news_by_date(
        date_query=date_query,
        platforms=platforms,
        limit=limit,
        include_url=include_url
    )
    return json.dumps(result, ensure_ascii=False, indent=2)



# ==================== Công cụ phân tích dữ liệu nâng cao ====================

@mcp.tool
async def analyze_topic_trend(
    topic: str,
    analysis_type: str = "trend",
    date_range: Optional[Dict[str, str]] = None,
    granularity: str = "day",
    threshold: float = 3.0,
    time_window: int = 24,
    lookahead_hours: int = 6,
    confidence_threshold: float = 0.7
) -> str:
    """
    Công cụ phân tích xu hướng chủ đề thống nhất - Tích hợp nhiều chế độ phân tích xu hướng

    Args:
        topic: Từ khóa chủ đề (bắt buộc)
        analysis_type: Loại phân tích, các giá trị có thể:
            - "trend": Phân tích xu hướng độ hot (theo dõi sự thay đổi độ hot của chủ đề)
            - "lifecycle": Phân tích vòng đời (chu kỳ hoàn chỉnh từ xuất hiện đến biến mất)
            - "viral": Phát hiện độ hot bất thường (nhận diện chủ đề đột nhiên nổi tiếng)
            - "predict": Dự đoán chủ đề (dự đoán hot topic tiềm năng trong tương lai)
        date_range: Phạm vi ngày (chế độ trend và lifecycle), tùy chọn
                    - **Định dạng**: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"} (phải là định dạng ngày chuẩn)
                    - **Giải thích**: AI phải tự động tính toán và điền ngày cụ thể dựa trên ngày hiện tại, không thể sử dụng ngôn ngữ tự nhiên như "hôm nay"
                    - **Ví dụ tính toán**:
                      - Người dùng nói "7 ngày gần đây" → AI tính: {"start": "2025-11-11", "end": "2025-11-17"} (giả sử hôm nay là 11-17)
                      - Người dùng nói "tuần trước" → AI tính: {"start": "2025-11-11", "end": "2025-11-17"} (thứ Hai đến Chủ nhật tuần trước)
                      - Người dùng nói "tháng này" → AI tính: {"start": "2025-11-01", "end": "2025-11-17"} (từ ngày 1 tháng 11 đến hôm nay)
                    - **Mặc định**: Không chỉ định sẽ mặc định phân tích 7 ngày gần nhất
        granularity: Độ chi tiết thời gian (chế độ trend), mặc định "day" (chỉ hỗ trợ day, vì dữ liệu cơ bản được tổng hợp theo ngày)
        threshold: Ngưỡng hệ số tăng đột biến độ hot (chế độ viral), mặc định 3.0
        time_window: Cửa sổ thời gian phát hiện tính bằng giờ (chế độ viral), mặc định 24
        lookahead_hours: Số giờ dự đoán tương lai (chế độ predict), mặc định 6
        confidence_threshold: Ngưỡng độ tin cậy (chế độ predict), mặc định 0.7

    Returns:
        Kết quả phân tích xu hướng định dạng JSON

    **Hướng dẫn sử dụng cho AI:**
    Khi người dùng sử dụng biểu thức thời gian tương đối (như "7 ngày gần đây", "tuần trước", "tháng trước"),
    AI phải tính toán ra ngày cụ thể định dạng YYYY-MM-DD dựa trên ngày hiện tại (lấy từ môi trường <env>).

    **Quan trọng**: date_range không chấp nhận ngôn ngữ tự nhiên như "hôm nay", "hôm qua", phải là định dạng YYYY-MM-DD!

    Ví dụ (giả sử hôm nay là 2025-11-17):
        - Người dùng: "Phân tích xu hướng AI 7 ngày gần đây"
          → analyze_topic_trend(topic="AI", analysis_type="trend", date_range={"start": "2025-11-11", "end": "2025-11-17"})
        - Người dùng: "Xem độ hot của Tesla tháng này"
          → analyze_topic_trend(topic="Tesla", analysis_type="lifecycle", date_range={"start": "2025-11-01", "end": "2025-11-17"})
        - analyze_topic_trend(topic="Bitcoin", analysis_type="viral", threshold=3.0)
        - analyze_topic_trend(topic="ChatGPT", analysis_type="predict", lookahead_hours=6)
    """
    tools = _get_tools()
    result = tools['analytics'].analyze_topic_trend_unified(
        topic=topic,
        analysis_type=analysis_type,
        date_range=date_range,
        granularity=granularity,
        threshold=threshold,
        time_window=time_window,
        lookahead_hours=lookahead_hours,
        confidence_threshold=confidence_threshold
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def analyze_data_insights(
    insight_type: str = "platform_compare",
    topic: Optional[str] = None,
    date_range: Optional[Dict[str, str]] = None,
    min_frequency: int = 3,
    top_n: int = 20
) -> str:
    """
    Công cụ phân tích data insight thống nhất - Tích hợp nhiều chế độ phân tích dữ liệu

    Args:
        insight_type: Loại insight, các giá trị có thể:
            - "platform_compare": Phân tích so sánh nền tảng (so sánh mức độ quan tâm của các nền tảng khác nhau đối với chủ đề)
            - "platform_activity": Thống kê độ hoạt động nền tảng (thống kê tần suất đăng bài và thời gian hoạt động của từng nền tảng)
            - "keyword_cooccur": Phân tích đồng xuất hiện từ khóa (phân tích mô hình các từ khóa xuất hiện cùng nhau)
        topic: Từ khóa chủ đề (tùy chọn, áp dụng cho chế độ platform_compare)
        date_range: **[Kiểu đối tượng]** Phạm vi ngày (tùy chọn)
                    - **Định dạng**: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                    - **Ví dụ**: {"start": "2025-01-01", "end": "2025-01-07"}
                    - **Quan trọng**: Phải là định dạng đối tượng, không thể truyền số nguyên
        min_frequency: Tần suất đồng xuất hiện tối thiểu (chế độ keyword_cooccur), mặc định 3
        top_n: Trả về TOP N kết quả (chế độ keyword_cooccur), mặc định 20

    Returns:
        Kết quả phân tích data insight định dạng JSON

    Ví dụ:
        - analyze_data_insights(insight_type="platform_compare", topic="AI")
        - analyze_data_insights(insight_type="platform_activity", date_range={"start": "2025-01-01", "end": "2025-01-07"})
        - analyze_data_insights(insight_type="keyword_cooccur", min_frequency=5, top_n=15)
    """
    tools = _get_tools()
    result = tools['analytics'].analyze_data_insights_unified(
        insight_type=insight_type,
        topic=topic,
        date_range=date_range,
        min_frequency=min_frequency,
        top_n=top_n
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def analyze_sentiment(
    topic: Optional[str] = None,
    platforms: Optional[List[str]] = None,
    date_range: Optional[Dict[str, str]] = None,
    limit: int = 50,
    sort_by_weight: bool = True,
    include_url: bool = False
) -> str:
    """
    Phân tích xu hướng cảm xúc và độ hot của tin tức

    Args:
        topic: Từ khóa chủ đề (tùy chọn)
        platforms: Danh sách ID nền tảng, ví dụ ['zhihu', 'weibo', 'douyin']
                   - Nếu không chỉ định: sử dụng tất cả nền tảng được cấu hình trong config.yaml
                   - Các nền tảng được hỗ trợ từ cấu hình platforms trong config/config.yaml
                   - Mỗi nền tảng có trường name tương ứng (như "Zhihu", "Weibo"), giúp AI dễ nhận biết
        date_range: **[Kiểu đối tượng]** Phạm vi ngày (tùy chọn)
                    - **Định dạng**: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                    - **Ví dụ**: {"start": "2025-01-01", "end": "2025-01-07"}
                    - **Quan trọng**: Phải là định dạng đối tượng, không thể truyền số nguyên
        limit: Số lượng tin tức trả về, mặc định 50, tối đa 100
               Lưu ý: Công cụ này sẽ loại bỏ trùng lặp tiêu đề tin tức (cùng tiêu đề trên các nền tảng khác nhau chỉ giữ một lần),
               vì vậy số lượng thực tế trả về có thể ít hơn giá trị limit yêu cầu
        sort_by_weight: Có sắp xếp theo trọng số độ hot không, mặc định True
        include_url: Có bao gồm URL link không, mặc định False (tiết kiệm token)

    Returns:
        Kết quả phân tích định dạng JSON, bao gồm phân bố cảm xúc, xu hướng độ hot và tin tức liên quan

    **Quan trọng: Chiến lược hiển thị dữ liệu**
    - Công cụ này trả về kết quả phân tích đầy đủ và danh sách tin tức
    - **Cách hiển thị mặc định**: Hiển thị kết quả phân tích đầy đủ (bao gồm tất cả tin tức)
    - Chỉ lọc khi người dùng yêu cầu rõ ràng "tóm tắt" hoặc "chọn điểm chính"
    """
    tools = _get_tools()
    result = tools['analytics'].analyze_sentiment(
        topic=topic,
        platforms=platforms,
        date_range=date_range,
        limit=limit,
        sort_by_weight=sort_by_weight,
        include_url=include_url
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def find_similar_news(
    reference_title: str,
    threshold: float = 0.6,
    limit: int = 50,
    include_url: bool = False
) -> str:
    """
    Tìm các tin tức khác tương tự với tiêu đề tin tức được chỉ định

    Args:
        reference_title: Tiêu đề tin tức (đầy đủ hoặc một phần)
        threshold: Ngưỡng độ tương tự, từ 0-1, mặc định 0.6
                   Lưu ý: Ngưỡng càng cao thì khớp càng chặt, kết quả trả về càng ít
        limit: Giới hạn số lượng trả về, mặc định 50, tối đa 100
               Lưu ý: Số lượng thực tế trả về phụ thuộc vào kết quả khớp độ tương tự, có thể ít hơn giá trị yêu cầu
        include_url: Có bao gồm URL link không, mặc định False (tiết kiệm token)

    Returns:
        Danh sách tin tức tương tự định dạng JSON, bao gồm điểm độ tương tự

    **Quan trọng: Chiến lược hiển thị dữ liệu**
    - Công cụ này trả về danh sách tin tức tương tự đầy đủ
    - **Cách hiển thị mặc định**: Hiển thị tất cả tin tức trả về (bao gồm điểm độ tương tự)
    - Chỉ lọc khi người dùng yêu cầu rõ ràng "tóm tắt" hoặc "chọn điểm chính"
    """
    tools = _get_tools()
    result = tools['analytics'].find_similar_news(
        reference_title=reference_title,
        threshold=threshold,
        limit=limit,
        include_url=include_url
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def generate_summary_report(
    report_type: str = "daily",
    date_range: Optional[Dict[str, str]] = None
) -> str:
    """
    Công cụ tạo tóm tắt hàng ngày/hàng tuần - Tự động tạo báo cáo tóm tắt hot topic

    Args:
        report_type: Loại báo cáo (daily/weekly)
        date_range: **[Kiểu đối tượng]** Phạm vi ngày tùy chỉnh (tùy chọn)
                    - **Định dạng**: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                    - **Ví dụ**: {"start": "2025-01-01", "end": "2025-01-07"}
                    - **Quan trọng**: Phải là định dạng đối tượng, không thể truyền số nguyên

    Returns:
        Báo cáo tóm tắt định dạng JSON, chứa nội dung định dạng Markdown
    """
    tools = _get_tools()
    result = tools['analytics'].generate_summary_report(
        report_type=report_type,
        date_range=date_range
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


# ==================== Công cụ tìm kiếm thông minh ====================

@mcp.tool
async def search_news(
    query: str,
    search_mode: str = "keyword",
    date_range: Optional[Dict[str, str]] = None,
    platforms: Optional[List[str]] = None,
    limit: int = 50,
    sort_by: str = "relevance",
    threshold: float = 0.6,
    include_url: bool = False
) -> str:
    """
    Giao diện tìm kiếm thống nhất, hỗ trợ nhiều chế độ tìm kiếm

    Args:
        query: Từ khóa tìm kiếm hoặc đoạn nội dung
        search_mode: Chế độ tìm kiếm, các giá trị có thể:
            - "keyword": Khớp từ khóa chính xác (mặc định, phù hợp để tìm kiếm chủ đề cụ thể)
            - "fuzzy": Khớp nội dung mờ (phù hợp để tìm kiếm đoạn nội dung, sẽ lọc kết quả có độ tương tự dưới ngưỡng)
            - "entity": Tìm kiếm tên thực thể (phù hợp để tìm kiếm người/địa điểm/tổ chức)
        date_range: Phạm vi ngày (tùy chọn)
                    - **Định dạng**: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                    - **Ví dụ**: {"start": "2025-01-01", "end": "2025-01-07"}
                    - **Giải thích**: AI cần tự động tính toán phạm vi ngày dựa trên ngôn ngữ tự nhiên của người dùng (như "7 ngày gần đây")
                    - **Mặc định**: Không chỉ định sẽ mặc định truy vấn tin tức hôm nay
                    - **Lưu ý**: start và end có thể giống nhau (truy vấn một ngày)
        platforms: Danh sách ID nền tảng, ví dụ ['zhihu', 'weibo', 'douyin']
                   - Nếu không chỉ định: sử dụng tất cả nền tảng được cấu hình trong config.yaml
                   - Các nền tảng được hỗ trợ từ cấu hình platforms trong config/config.yaml
                   - Mỗi nền tảng có trường name tương ứng (như "Zhihu", "Weibo"), giúp AI dễ nhận biết
        limit: Giới hạn số lượng trả về, mặc định 50, tối đa 1000
               Lưu ý: Số lượng thực tế trả về phụ thuộc vào kết quả tìm kiếm khớp (đặc biệt chế độ fuzzy sẽ lọc kết quả có độ tương tự thấp)
        sort_by: Cách sắp xếp, các giá trị có thể:
            - "relevance": Sắp xếp theo độ liên quan (mặc định)
            - "weight": Sắp xếp theo trọng số tin tức
            - "date": Sắp xếp theo ngày
        threshold: Ngưỡng độ tương tự (chỉ có hiệu lực ở chế độ fuzzy), từ 0-1, mặc định 0.6
                   Lưu ý: Ngưỡng càng cao thì khớp càng chặt, kết quả trả về càng ít
        include_url: Có bao gồm URL link không, mặc định False (tiết kiệm token)

    Returns:
        Kết quả tìm kiếm định dạng JSON, bao gồm tiêu đề, nền tảng, thứ hạng và các thông tin khác

    **Quan trọng: Chiến lược hiển thị dữ liệu**
    - Công cụ này trả về danh sách kết quả tìm kiếm đầy đủ
    - **Cách hiển thị mặc định**: Hiển thị tất cả tin tức trả về, không cần tóm tắt hoặc lọc
    - Chỉ lọc khi người dùng yêu cầu rõ ràng "tóm tắt" hoặc "chọn điểm chính"

    **Hướng dẫn sử dụng cho AI:**
    Khi người dùng sử dụng biểu thức thời gian tương đối (như "7 ngày gần đây", "tuần trước", "nửa tháng gần đây"),
    AI phải tính toán ra ngày cụ thể định dạng YYYY-MM-DD dựa trên ngày hiện tại (lấy từ môi trường <env>).

    **Quan trọng**: date_range không chấp nhận ngôn ngữ tự nhiên như "hôm nay", "hôm qua", phải là định dạng YYYY-MM-DD!

    **Quy tắc tính toán** (giả sử từ <env> lấy hôm nay là 2025-11-17):
    - "Hôm nay" → Không truyền date_range (mặc định truy vấn hôm nay)
    - "7 ngày gần đây" → {"start": "2025-11-11", "end": "2025-11-17"}
    - "Tuần trước" → {"start": "2025-11-11", "end": "2025-11-17"}
    - "Tuần trước" → Tính thứ Hai đến Chủ nhật tuần trước, như {"start": "2025-11-11", "end": "2025-11-17"}
    - "Tháng này" → {"start": "2025-11-01", "end": "2025-11-17"}
    - "30 ngày gần đây" → {"start": "2025-10-19", "end": "2025-11-17"}


    Ví dụ (giả sử hôm nay là 2025-11-17):
        - Người dùng: "Tin tức AI hôm nay" → search_news(query="AI")
        - Người dùng: "Tin tức AI 7 ngày gần đây" → search_news(query="AI", date_range={"start": "2025-11-11", "end": "2025-11-17"})
        - Ngày cụ thể: search_news(query="AI", date_range={"start": "2025-01-01", "end": "2025-01-07"})
        - Tìm kiếm mờ: search_news(query="Tesla giảm giá", search_mode="fuzzy", threshold=0.4)
    """
    tools = _get_tools()
    result = tools['search'].search_news_unified(
        query=query,
        search_mode=search_mode,
        date_range=date_range,
        platforms=platforms,
        limit=limit,
        sort_by=sort_by,
        threshold=threshold,
        include_url=include_url
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def search_related_news_history(
    reference_text: str,
    time_preset: str = "yesterday",
    threshold: float = 0.4,
    limit: int = 50,
    include_url: bool = False
) -> str:
    """
    Dựa trên tin tức nguồn, tìm kiếm tin tức liên quan trong dữ liệu lịch sử

    Args:
        reference_text: Tiêu đề tin tức tham chiếu (đầy đủ hoặc một phần)
        time_preset: Giá trị đặt trước phạm vi thời gian, có thể chọn:
            - "yesterday": Hôm qua
            - "last_week": Tuần trước (7 ngày)
            - "last_month": Tháng trước (30 ngày)
            - "custom": Phạm vi ngày tùy chỉnh (cần cung cấp start_date và end_date)
        threshold: Ngưỡng độ liên quan, từ 0-1, mặc định 0.4
                   Lưu ý: Tính toán độ tương tự tổng hợp (70% trùng từ khóa + 30% độ tương tự văn bản)
                   Ngưỡng càng cao thì khớp càng chặt, kết quả trả về càng ít
        limit: Giới hạn số lượng trả về, mặc định 50, tối đa 100
               Lưu ý: Số lượng thực tế trả về phụ thuộc vào kết quả khớp độ liên quan, có thể ít hơn giá trị yêu cầu
        include_url: Có bao gồm URL link không, mặc định False (tiết kiệm token)

    Returns:
        Danh sách tin tức liên quan định dạng JSON, bao gồm điểm độ liên quan và phân bố thời gian

    **Quan trọng: Chiến lược hiển thị dữ liệu**
    - Công cụ này trả về danh sách tin tức liên quan đầy đủ
    - **Cách hiển thị mặc định**: Hiển thị tất cả tin tức trả về (bao gồm điểm độ liên quan)
    - Chỉ lọc khi người dùng yêu cầu rõ ràng "tóm tắt" hoặc "chọn điểm chính"
    """
    tools = _get_tools()
    result = tools['search'].search_related_news_history(
        reference_text=reference_text,
        time_preset=time_preset,
        threshold=threshold,
        limit=limit,
        include_url=include_url
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


# ==================== Công cụ cấu hình và quản lý hệ thống ====================

@mcp.tool
async def get_current_config(
    section: str = "all"
) -> str:
    """
    Lấy cấu hình hệ thống hiện tại

    Args:
        section: Phần cấu hình, các giá trị có thể:
            - "all": Tất cả cấu hình (mặc định)
            - "crawler": Cấu hình crawler
            - "push": Cấu hình push notification
            - "keywords": Cấu hình từ khóa
            - "weights": Cấu hình trọng số

    Returns:
        Thông tin cấu hình định dạng JSON
    """
    tools = _get_tools()
    result = tools['config'].get_current_config(section=section)
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def get_system_status() -> str:
    """
    Lấy trạng thái hoạt động hệ thống và thông tin health check

    Trả về phiên bản hệ thống, thống kê dữ liệu, trạng thái cache và các thông tin khác

    Returns:
        Thông tin trạng thái hệ thống định dạng JSON
    """
    tools = _get_tools()
    result = tools['system'].get_system_status()
    return json.dumps(result, ensure_ascii=False, indent=2)


@mcp.tool
async def trigger_crawl(
    platforms: Optional[List[str]] = None,
    save_to_local: bool = False,
    include_url: bool = False
) -> str:
    """
    Kích hoạt thủ công một lần thu thập dữ liệu (tùy chọn lưu trữ vĩnh viễn)

    Args:
        platforms: Danh sách ID nền tảng được chỉ định, ví dụ ['zhihu', 'weibo', 'douyin']
                   - Nếu không chỉ định: sử dụng tất cả nền tảng được cấu hình trong config.yaml
                   - Các nền tảng được hỗ trợ từ cấu hình platforms trong config/config.yaml
                   - Mỗi nền tảng có trường name tương ứng (như "Zhihu", "Weibo"), giúp AI dễ nhận biết
                   - Lưu ý: Các nền tảng thất bại sẽ được liệt kê trong trường failed_platforms của kết quả trả về
        save_to_local: Có lưu vào thư mục output local không, mặc định False
        include_url: Có bao gồm URL link không, mặc định False (tiết kiệm token)

    Returns:
        Thông tin trạng thái task định dạng JSON, bao gồm:
        - platforms: Danh sách nền tảng thu thập thành công
        - failed_platforms: Danh sách nền tảng thất bại (nếu có)
        - total_news: Tổng số tin tức thu thập được
        - data: Dữ liệu tin tức

    Ví dụ:
        - Thu thập tạm thời: trigger_crawl(platforms=['zhihu'])
        - Thu thập và lưu: trigger_crawl(platforms=['weibo'], save_to_local=True)
        - Sử dụng nền tảng mặc định: trigger_crawl()  # Thu thập tất cả nền tảng được cấu hình trong config.yaml
    """
    tools = _get_tools()
    result = tools['system'].trigger_crawl(platforms=platforms, save_to_local=save_to_local, include_url=include_url)
    return json.dumps(result, ensure_ascii=False, indent=2)


# ==================== Điểm vào khởi động ====================

def run_server(
    project_root: Optional[str] = None,
    transport: str = 'stdio',
    host: str = '0.0.0.0',
    port: int = 3333
):
    """
    Khởi động MCP Server

    Args:
        project_root: Đường dẫn thư mục gốc dự án
        transport: Chế độ truyền tải, 'stdio' hoặc 'http'
        host: Địa chỉ lắng nghe cho chế độ HTTP, mặc định 0.0.0.0
        port: Cổng lắng nghe cho chế độ HTTP, mặc định 3333
    """
    # Khởi tạo instance công cụ
    _get_tools(project_root)

    # In thông tin khởi động
    print()
    print("=" * 60)
    print("  TrendRadar MCP Server - FastMCP 2.0")
    print("=" * 60)
    print(f"  Chế độ truyền tải: {transport.upper()}")

    if transport == 'stdio':
        print("  Giao thức: MCP over stdio (đầu vào/ra chuẩn)")
        print("  Mô tả: Giao tiếp với MCP client qua đầu vào/ra chuẩn")
    elif transport == 'http':
        print(f"  Địa chỉ lắng nghe: http://{host}:{port}")
        print(f"  HTTP endpoint: http://{host}:{port}/mcp")
        print("  Giao thức: MCP over HTTP (môi trường production)")

    if project_root:
        print(f"  Thư mục dự án: {project_root}")
    else:
        print("  Thư mục dự án: Thư mục hiện tại")

    print()
    print("  Các công cụ đã đăng ký:")
    print("    === Truy vấn dữ liệu cơ bản (P0 cốt lõi) ===")
    print("    1. get_latest_news        - Lấy tin tức mới nhất")
    print("    2. get_news_by_date       - Truy vấn tin tức theo ngày (hỗ trợ ngôn ngữ tự nhiên)")
    print("    3. get_trending_topics    - Lấy chủ đề xu hướng")
    print()
    print("    === Công cụ tìm kiếm thông minh ===")
    print("    4. search_news                  - Tìm kiếm tin tức thống nhất (từ khóa/mờ/thực thể)")
    print("    5. search_related_news_history  - Tìm kiếm tin tức liên quan trong lịch sử")
    print()
    print("    === Phân tích dữ liệu nâng cao ===")
    print("    6. analyze_topic_trend      - Phân tích xu hướng chủ đề thống nhất (độ hot/vòng đời/viral/dự đoán)")
    print("    7. analyze_data_insights    - Phân tích data insight thống nhất (so sánh nền tảng/hoạt động/đồng xuất hiện từ khóa)")
    print("    8. analyze_sentiment        - Phân tích xu hướng cảm xúc")
    print("    9. find_similar_news        - Tìm tin tức tương tự")
    print("    10. generate_summary_report - Tạo báo cáo tóm tắt hàng ngày/hàng tuần")
    print()
    print("    === Cấu hình và quản lý hệ thống ===")
    print("    11. get_current_config      - Lấy cấu hình hệ thống hiện tại")
    print("    12. get_system_status       - Lấy trạng thái hoạt động hệ thống")
    print("    13. trigger_crawl           - Kích hoạt thủ công task thu thập")
    print("=" * 60)
    print()

    # Chạy server theo chế độ truyền tải
    if transport == 'stdio':
        mcp.run(transport='stdio')
    elif transport == 'http':
        # Chế độ HTTP (khuyến nghị cho production)
        mcp.run(
            transport='http',
            host=host,
            port=port,
            path='/mcp'  # Đường dẫn HTTP endpoint
        )
    else:
        raise ValueError(f"Chế độ truyền tải không được hỗ trợ: {transport}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='TrendRadar MCP Server - MCP tool server tổng hợp tin tức hot',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Hướng dẫn cấu hình chi tiết xem tại: README-Cherry-Studio.md
        """
    )
    parser.add_argument(
        '--transport',
        choices=['stdio', 'http'],
        default='stdio',
        help='Chế độ truyền tải: stdio (mặc định) hoặc http (môi trường production)'
    )
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='Địa chỉ lắng nghe cho chế độ HTTP, mặc định 0.0.0.0'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=3333,
        help='Cổng lắng nghe cho chế độ HTTP, mặc định 3333'
    )
    parser.add_argument(
        '--project-root',
        help='Đường dẫn thư mục gốc dự án'
    )

    args = parser.parse_args()

    run_server(
        project_root=args.project_root,
        transport=args.transport,
        host=args.host,
        port=args.port
    )
