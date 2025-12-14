"""
Công cụ phân tích dữ liệu nâng cao

Cung cấp chức năng phân tích nâng cao như phân tích xu hướng độ nóng, so sánh nền tảng, đồng xuất hiện từ khóa, phân tích cảm xúc, v.v.。
"""

import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from difflib import SequenceMatcher

from ..services.data_service import DataService
from ..utils.validators import (
    validate_platforms,
    validate_limit,
    validate_keyword,
    validate_top_n,
    validate_date_range
)
from ..utils.errors import MCPError, InvalidParameterError, DataNotFoundError


def calculate_news_weight(news_data: Dict, rank_threshold: int = 5) -> float:
    """
    Tính trọng số tin tức (dùng để sắp xếp)

    Triển khai thuật toán trọng số dựa trên main.py, xem xét tổng hợp：
    - Trọng số xếp hạng (60%)：Xếp hạng tin tức trong bảng xếp hạng
    - 频lần权重 (30%)：tin tức出现củalần数
    - 热度权重 (10%)：高排名出现của比例

    Args:
        news_data: tin tức数据字典，包含 ranks và count 字段
        rank_threshold: 高排名阈值，默认5

    Returns:
        权重phút数（0-100之间của浮点数）
    """
    ranks = news_data.get("ranks", [])
    if not ranks:
        return 0.0

    count = news_data.get("count", len(ranks))

    # 权重cấu hình（với config.yaml 保持một致）
    RANK_WEIGHT = 0.6
    FREQUENCY_WEIGHT = 0.3
    HOTNESS_WEIGHT = 0.1

    # 1. Trọng số thứ hạng：Σ(11 - min(rank, 10)) / Số lần xuất hiện
    rank_scores = []
    for rank in ranks:
        score = 11 - min(rank, 10)
        rank_scores.append(score)

    rank_weight = sum(rank_scores) / len(ranks) if ranks else 0

    # 2. Trọng số tần suất：min(Số lần xuất hiện, 10) × 10
    frequency_weight = min(count, 10) * 10

    # 3. Tăng cường độ nóng：Số lần xếp hạng cao / 总Số lần xuất hiện × 100
    high_rank_count = sum(1 for rank in ranks if rank <= rank_threshold)
    hotness_ratio = high_rank_count / len(ranks) if ranks else 0
    hotness_weight = hotness_ratio * 100

    # 综合权重
    total_weight = (
        rank_weight * RANK_WEIGHT
        + frequency_weight * FREQUENCY_WEIGHT
        + hotness_weight * HOTNESS_WEIGHT
    )

    return total_weight


class AnalyticsTools:
    """Công cụ phân tích dữ liệu nâng cao类"""

    def __init__(self, project_root: str = None):
        """
        初始化phút析工具

        Args:
            project_root: 项目根目录
        """
        self.data_service = DataService(project_root)

    def analyze_data_insights_unified(
        self,
        insight_type: str = "platform_compare",
        topic: Optional[str] = None,
        date_range: Optional[Dict[str, str]] = None,
        min_frequency: int = 3,
        top_n: int = 20
    ) -> Dict:
        """
        统một数据洞察phút析工具 - 整合多种数据phút析chế độ

        Args:
            insight_type: 洞察loại，có thể选值：
                - "platform_compare": 平台đối比phút析（đối比không同平台đối话题của关注度）
                - "platform_activity": 平台活跃度统计（统计各平台发布频率và活跃giờ间）
                - "keyword_cooccur": 关键词tổng现phút析（phút析关键词同giờ出现củachế độ）
            topic: 话题关键词（có thể选，platform_comparechế độ适用）
            date_range: ngày期范围，định dạng: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
            min_frequency: nhất小tổng现频lần（keyword_cooccurchế độ），默认3
            top_n: 返回TOP N结果（keyword_cooccurchế độ），默认20

        Returns:
            数据洞察phút析结果字典

        Examples:
            - analyze_data_insights_unified(insight_type="platform_compare", topic="trí tuệ nhân tạo")
            - analyze_data_insights_unified(insight_type="platform_activity", date_range={...})
            - analyze_data_insights_unified(insight_type="keyword_cooccur", min_frequency=5)
        """
        try:
            # tham số验证
            if insight_type not in ["platform_compare", "platform_activity", "keyword_cooccur"]:
                raise InvalidParameterError(
                    f"无效của洞察loại: {insight_type}",
                    suggestion="支持củaloại: platform_compare, platform_activity, keyword_cooccur"
                )

            # 根据洞察lớp型调用相应phương thức
            if insight_type == "platform_compare":
                return self.compare_platforms(
                    topic=topic,
                    date_range=date_range
                )
            elif insight_type == "platform_activity":
                return self.get_platform_activity_stats(
                    date_range=date_range
                )
            else:  # keyword_cooccur
                return self.analyze_keyword_cooccurrence(
                    min_frequency=min_frequency,
                    top_n=top_n
                )

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

    def analyze_topic_trend_unified(
        self,
        topic: str,
        analysis_type: str = "trend",
        date_range: Optional[Dict[str, str]] = None,
        granularity: str = "day",
        threshold: float = 3.0,
        time_window: int = 24,
        lookahead_hours: int = 6,
        confidence_threshold: float = 0.7
    ) -> Dict:
        """
        统một话题趋势phút析工具 - 整合多种趋势phút析chế độ

        Args:
            topic: 话题关键词（必需）
            analysis_type: phút析loại，có thể选值：
                - "trend": 热度趋势phút析（追踪话题của热度变化）
                - "lifecycle": 生命周期phút析（từ出现đến消失của完整周期）
                - "viral": ngoại lệ热度检测（识别突然爆火của话题）
                - "predict": 话题预测（预测未đếncó thể能củaxu hướng nóng）
            date_range: ngày期范围（trendvàlifecyclechế độ），có thể选
                       - **định dạng**: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                       - **默认**: không指定giờ默认phút析nhất近7天
            granularity: giờ间粒度（trendchế độ），默认"day"（hour/day）
            threshold: 热度突增倍数阈值（viralchế độ），默认3.0
            time_window: 检测giờ间窗口小giờ数（viralchế độ），默认24
            lookahead_hours: 预测未đến小giờ数（predictchế độ），默认6
            confidence_threshold: 置信度阈值（predictchế độ），默认0.7

        Returns:
            趋势phút析结果字典

        Examples (假设hôm naylà 2025-11-17):
            - 用户："phút析AInhất近7天của趋势" → analyze_topic_trend_unified(topic="trí tuệ nhân tạo", analysis_type="trend", date_range={"start": "2025-11-11", "end": "2025-11-17"})
            - 用户："xemxem特斯拉本thángcủa热度" → analyze_topic_trend_unified(topic="特斯拉", analysis_type="lifecycle", date_range={"start": "2025-11-01", "end": "2025-11-17"})
            - analyze_topic_trend_unified(topic="比特币", analysis_type="viral", threshold=3.0)
            - analyze_topic_trend_unified(topic="ChatGPT", analysis_type="predict", lookahead_hours=6)
        """
        try:
            # tham số验证
            topic = validate_keyword(topic)

            if analysis_type not in ["trend", "lifecycle", "viral", "predict"]:
                raise InvalidParameterError(
                    f"无效củaphút析loại: {analysis_type}",
                    suggestion="支持củaloại: trend, lifecycle, viral, predict"
                )

            # 根据phân tíchlớp型调用相应phương thức
            if analysis_type == "trend":
                return self.get_topic_trend_analysis(
                    topic=topic,
                    date_range=date_range,
                    granularity=granularity
                )
            elif analysis_type == "lifecycle":
                return self.analyze_topic_lifecycle(
                    topic=topic,
                    date_range=date_range
                )
            elif analysis_type == "viral":
                # viralChế độkhông需muốntopictham số，Sử dụng chung检测
                return self.detect_viral_topics(
                    threshold=threshold,
                    time_window=time_window
                )
            else:  # predict
                # predictChế độkhông需muốntopictham số，Sử dụng chung预测
                return self.predict_trending_topics(
                    lookahead_hours=lookahead_hours,
                    confidence_threshold=confidence_threshold
                )

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

    def get_topic_trend_analysis(
        self,
        topic: str,
        date_range: Optional[Dict[str, str]] = None,
        granularity: str = "day"
    ) -> Dict:
        """
        热度趋势phút析 - 追踪特定话题của热度变化趋势

        Args:
            topic: 话题关键词
            date_range: ngày期范围（có thể选）
                       - **định dạng**: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                       - **默认**: không指定giờ默认phút析nhất近7天
            granularity: giờ间粒度，仅支持 day（天）

        Returns:
            趋势phút析结果字典

        Examples:
            用户询问示例：
            - "帮tôiphút析mộtdưới'trí tuệ nhân tạo'này个话题nhất近một周của热度趋势"
            - "查xem'比特币'过đimột周của热度变化"
            - "xemxem'iPhone'nhất近7天của趋势如何"
            - "phút析'特斯拉'nhất近mộtthángcủa热度趋势"
            - "查xem'ChatGPT'2024năm12thángcủa趋势变化"

            代码调用示例：
            >>> tools = AnalyticsTools()
            >>> # phút析7天趋势（假设hôm naylà 2025-11-17）
            >>> result = tools.get_topic_trend_analysis(
            ...     topic="trí tuệ nhân tạo",
            ...     date_range={"start": "2025-11-11", "end": "2025-11-17"},
            ...     granularity="day"
            ... )
            >>> # phút析历史tháng份趋势
            >>> result = tools.get_topic_trend_analysis(
            ...     topic="特斯拉",
            ...     date_range={"start": "2024-12-01", "end": "2024-12-31"},
            ...     granularity="day"
            ... )
            >>> print(result['trend_data'])
        """
        try:
            # 验证tham số
            topic = validate_keyword(topic)

            # 验证粒度tham số（只支持day）
            if granularity != "day":
                from ..utils.errors import InvalidParameterError
                raise InvalidParameterError(
                    f"không支持của粒度参数: {granularity}",
                    suggestion="当前仅支持 'day' 粒度，vì底层数据theo天聚合"
                )

            # Xử lýngày范围（không指定giờ默认nhất近7天）
            if date_range:
                from ..utils.validators import validate_date_range
                date_range_tuple = validate_date_range(date_range)
                start_date, end_date = date_range_tuple
            else:
                # 默认nhất近7天
                end_date = datetime.now()
                start_date = end_date - timedelta(days=6)

            # 收集趋势dữ liệu
            trend_data = []
            current_date = start_date

            while current_date <= end_date:
                try:
                    all_titles, _, _ = self.data_service.parser.read_all_titles_for_date(
                        date=current_date
                    )

                    # thống kê该thời gian点của话题Số lần xuất hiện
                    count = 0
                    matched_titles = []

                    for _, titles in all_titles.items():
                        for title in titles.keys():
                            if topic.lower() in title.lower():
                                count += 1
                                matched_titles.append(title)

                    trend_data.append({
                        "date": current_date.strftime("%Y-%m-%d"),
                        "count": count,
                        "sample_titles": matched_titles[:3]  # 只giữ lại前3个样本
                    })

                except DataNotFoundError:
                    trend_data.append({
                        "date": current_date.strftime("%Y-%m-%d"),
                        "count": 0,
                        "sample_titles": []
                    })

                # theo天增加thời gian
                current_date += timedelta(days=1)

            # tính toán趋势指标
            counts = [item["count"] for item in trend_data]
            total_days = (end_date - start_date).days + 1

            if len(counts) >= 2:
                # tính toán涨跌幅度
                first_non_zero = next((c for c in counts if c > 0), 0)
                last_count = counts[-1]

                if first_non_zero > 0:
                    change_rate = ((last_count - first_non_zero) / first_non_zero) * 100
                else:
                    change_rate = 0

                # 找đến峰giá trịthời gian
                max_count = max(counts)
                peak_index = counts.index(max_count)
                peak_time = trend_data[peak_index]["date"]
            else:
                change_rate = 0
                peak_time = None
                max_count = 0

            return {
                "success": True,
                "topic": topic,
                "date_range": {
                    "start": start_date.strftime("%Y-%m-%d"),
                    "end": end_date.strftime("%Y-%m-%d"),
                    "total_days": total_days
                },
                "granularity": granularity,
                "trend_data": trend_data,
                "statistics": {
                    "total_mentions": sum(counts),
                    "average_mentions": round(sum(counts) / len(counts), 2) if counts else 0,
                    "peak_count": max_count,
                    "peak_time": peak_time,
                    "change_rate": round(change_rate, 2)
                },
                "trend_direction": "trên升" if change_rate > 10 else "dưới降" if change_rate < -10 else "稳定"
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

    def compare_platforms(
        self,
        topic: Optional[str] = None,
        date_range: Optional[Dict[str, str]] = None
    ) -> Dict:
        """
        平台đối比phút析 - đối比không同平台đối同một话题của关注度

        Args:
            topic: 话题关键词（có thể选，không指定则đối比整体活跃度）
            date_range: ngày期范围，định dạng: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}

        Returns:
            平台đối比phút析结果

        Examples:
            用户询问示例：
            - "đối比mộtdưới各个平台đối'trí tuệ nhân tạo'话题của关注度"
            - "xemxem知乎và微博哪个平台hơn关注科技tin tức"
            - "phút析各平台hôm naycủaxu hướng nóngphút布"

            代码调用示例：
            >>> # đối比各平台（假设hôm naylà 2025-11-17）
            >>> result = tools.compare_platforms(
            ...     topic="trí tuệ nhân tạo",
            ...     date_range={"start": "2025-11-08", "end": "2025-11-17"}
            ... )
            >>> print(result['platform_stats'])
        """
        try:
            # tham số验证
            if topic:
                topic = validate_keyword(topic)
            date_range_tuple = validate_date_range(date_range)

            # 确定ngày范围
            if date_range_tuple:
                start_date, end_date = date_range_tuple
            else:
                start_date = end_date = datetime.now()

            # 收集各平台dữ liệu
            platform_stats = defaultdict(lambda: {
                "total_news": 0,
                "topic_mentions": 0,
                "unique_titles": set(),
                "top_keywords": Counter()
            })

            # 遍历ngày范围
            current_date = start_date
            while current_date <= end_date:
                try:
                    all_titles, id_to_name, _ = self.data_service.parser.read_all_titles_for_date(
                        date=current_date
                    )

                    for platform_id, titles in all_titles.items():
                        platform_name = id_to_name.get(platform_id, platform_id)

                        for title in titles.keys():
                            platform_stats[platform_name]["total_news"] += 1
                            platform_stats[platform_name]["unique_titles"].add(title)

                            # nếu指定rồi话题，thống kê包含话题củamới闻
                            if topic and topic.lower() in title.lower():
                                platform_stats[platform_name]["topic_mentions"] += 1

                            # Trích xuất关键词（简单phút词）
                            keywords = self._extract_keywords(title)
                            platform_stats[platform_name]["top_keywords"].update(keywords)

                except DataNotFoundError:
                    pass

                current_date += timedelta(days=1)

            # 转换vìcó thể序列化củađịnh dạng
            result_stats = {}
            for platform, stats in platform_stats.items():
                coverage_rate = 0
                if stats["total_news"] > 0:
                    coverage_rate = (stats["topic_mentions"] / stats["total_news"]) * 100

                result_stats[platform] = {
                    "total_news": stats["total_news"],
                    "topic_mentions": stats["topic_mentions"],
                    "unique_titles": len(stats["unique_titles"]),
                    "coverage_rate": round(coverage_rate, 2),
                    "top_keywords": [
                        {"keyword": k, "count": v}
                        for k, v in stats["top_keywords"].most_common(5)
                    ]
                }

            # 找出各平台独cócủaxu hướng nóng
            unique_topics = self._find_unique_topics(platform_stats)

            return {
                "success": True,
                "topic": topic,
                "date_range": {
                    "start": start_date.strftime("%Y-%m-%d"),
                    "end": end_date.strftime("%Y-%m-%d")
                },
                "platform_stats": result_stats,
                "unique_topics": unique_topics,
                "total_platforms": len(result_stats)
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

    def analyze_keyword_cooccurrence(
        self,
        min_frequency: int = 3,
        top_n: int = 20
    ) -> Dict:
        """
        关键词tổng现phút析 - phút析哪些关键词经常同giờ出现

        Args:
            min_frequency: nhất小tổng现频lần
            top_n: 返回TOP N关键词đối

        Returns:
            关键词tổng现phút析结果

        Examples:
            用户询问示例：
            - "phút析mộtdưới哪些关键词经常một起出现"
            - "xemxem'trí tuệ nhân tạo'经常và哪些词một起出现"
            - "找出hôm naytin tứctrongcủa关键词关联"

            代码调用示例：
            >>> tools = AnalyticsTools()
            >>> result = tools.analyze_keyword_cooccurrence(
            ...     min_frequency=5,
            ...     top_n=15
            ... )
            >>> print(result['cooccurrence_pairs'])
        """
        try:
            # tham số验证
            min_frequency = validate_limit(min_frequency, default=3, max_limit=100)
            top_n = validate_top_n(top_n, default=20)

            # đọchôm naycủadữ liệu
            all_titles, _, _ = self.data_service.parser.read_all_titles_for_date()

            # 关键词tổng现thống kê
            cooccurrence = Counter()
            keyword_titles = defaultdict(list)

            for platform_id, titles in all_titles.items():
                for title in titles.keys():
                    # Trích xuất关键词
                    keywords = self._extract_keywords(title)

                    # bản ghimỗi关键词出现của标题
                    for kw in keywords:
                        keyword_titles[kw].append(title)

                    # tính toán两两tổng现
                    if len(keywords) >= 2:
                        for i, kw1 in enumerate(keywords):
                            for kw2 in keywords[i+1:]:
                                # 统mộtsắp xếp，tránh重复
                                pair = tuple(sorted([kw1, kw2]))
                                cooccurrence[pair] += 1

            # lọc低频tổng现
            filtered_pairs = [
                (pair, count) for pair, count in cooccurrence.items()
                if count >= min_frequency
            ]

            # sắp xếp并取TOP N
            top_pairs = sorted(filtered_pairs, key=lambda x: x[1], reverse=True)[:top_n]

            # 构建结果
            result_pairs = []
            for (kw1, kw2), count in top_pairs:
                # 找出同giờ包含两个关键词của标题样本
                titles_with_both = [
                    title for title in keyword_titles[kw1]
                    if kw2 in self._extract_keywords(title)
                ]

                result_pairs.append({
                    "keyword1": kw1,
                    "keyword2": kw2,
                    "cooccurrence_count": count,
                    "sample_titles": titles_with_both[:3]
                })

            return {
                "success": True,
                "cooccurrence_pairs": result_pairs,
                "total_pairs": len(result_pairs),
                "min_frequency": min_frequency,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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

    def analyze_sentiment(
        self,
        topic: Optional[str] = None,
        platforms: Optional[List[str]] = None,
        date_range: Optional[Dict[str, str]] = None,
        limit: int = 50,
        sort_by_weight: bool = True,
        include_url: bool = False
    ) -> Dict:
        """
        情感倾向phút析 - tạo用ở AI 情感phút析của结构化提示词

        本工具收集tin tức数据并tạo优化của AI 提示词，bạncó thểsẽ其gửi给 AI 进行深度情感phút析。

        Args:
            topic: 话题关键词（có thể选），只phút析包含该关键词củatin tức
            platforms: 平台lọc列表（có thể选），如 ['zhihu', 'weibo']
            date_range: ngày期范围（có thể选），định dạng: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                       không指定则默认查询hôm naycủa数据
            limit: 返回tin tức数量giới hạn，默认50，nhất大100
            sort_by_weight: là否theo权重排序，默认True（推荐）
            include_url: là否包含URL链接，默认False（节省token）

        Returns:
            包含 AI 提示词vàtin tức数据của结构化结果

        Examples:
            用户询问示例：
            - "phút析mộtdướihôm naytin tứccủa情感倾向"
            - "xemxem'特斯拉'相关tin tứclà正面cònlà负面của"
            - "phút析各平台đối'trí tuệ nhân tạo'của情感态度"
            - "xemxem'特斯拉'相关tin tứclà正面cònlà负面của，请选择một周trongcủa前10tintin tứcđếnphút析"

            代码调用示例：
            >>> tools = AnalyticsTools()
            >>> # phút析hôm naycủa特斯拉tin tức，返回前10tin
            >>> result = tools.analyze_sentiment(
            ...     topic="特斯拉",
            ...     limit=10
            ... )
            >>> # phút析một周trongcủa特斯拉tin tức（假设hôm naylà 2025-11-17）
            >>> result = tools.analyze_sentiment(
            ...     topic="特斯拉",
            ...     date_range={"start": "2025-11-11", "end": "2025-11-17"},
            ...     limit=10
            ... )
            >>> print(result['ai_prompt'])  # Lấytạocủa提示词
        """
        try:
            # tham số验证
            if topic:
                topic = validate_keyword(topic)
            platforms = validate_platforms(platforms)
            limit = validate_limit(limit, default=50)

            # Xử lýngày范围
            if date_range:
                date_range_tuple = validate_date_range(date_range)
                start_date, end_date = date_range_tuple
            else:
                # 默认hôm nay
                start_date = end_date = datetime.now()

            # 收集mới闻dữ liệu（支持多天）
            all_news_items = []
            current_date = start_date

            while current_date <= end_date:
                try:
                    all_titles, id_to_name, _ = self.data_service.parser.read_all_titles_for_date(
                        date=current_date,
                        platform_ids=platforms
                    )

                    # 收集该ngàycủamới闻
                    for platform_id, titles in all_titles.items():
                        platform_name = id_to_name.get(platform_id, platform_id)
                        for title, info in titles.items():
                            # nếu指定rồi话题，只收集包含话题của标题
                            if topic and topic.lower() not in title.lower():
                                continue

                            news_item = {
                                "platform": platform_name,
                                "title": title,
                                "ranks": info.get("ranks", []),
                                "count": len(info.get("ranks", [])),
                                "date": current_date.strftime("%Y-%m-%d")
                            }

                            # tin件性thêm URL 字段
                            if include_url:
                                news_item["url"] = info.get("url", "")
                                news_item["mobileUrl"] = info.get("mobileUrl", "")

                            all_news_items.append(news_item)

                except DataNotFoundError:
                    # 该ngàykhông códữ liệu，tiếp tụcdướimột天
                    pass

                # dướimột天
                current_date += timedelta(days=1)

            if not all_news_items:
                time_desc = "hôm nay" if start_date == end_date else f"{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}"
                raise DataNotFoundError(
                    f"未找đến相关tin tức（{time_desc}）",
                    suggestion="请尝试其他话题、ngày期范围hoặc平台"
                )

            # đi重（同một标题只giữ lạimộtlần）
            unique_news = {}
            for item in all_news_items:
                key = f"{item['platform']}::{item['title']}"
                if key not in unique_news:
                    unique_news[key] = item
                else:
                    # 合并 ranks（nếu同mộtmới闻ở多天出现）
                    existing = unique_news[key]
                    existing["ranks"].extend(item["ranks"])
                    existing["count"] = len(existing["ranks"])

            deduplicated_news = list(unique_news.values())

            # Sắp xếp theo trọng số（nếu启用）
            if sort_by_weight:
                deduplicated_news.sort(
                    key=lambda x: calculate_news_weight(x),
                    reverse=True
                )

            # giới hạn返回số lượng
            selected_news = deduplicated_news[:limit]

            # tạo AI 提示词
            ai_prompt = self._create_sentiment_analysis_prompt(
                news_data=selected_news,
                topic=topic
            )

            # 构建thời gian范围描述
            if start_date == end_date:
                time_range_desc = start_date.strftime("%Y-%m-%d")
            else:
                time_range_desc = f"{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}"

            result = {
                "success": True,
                "method": "ai_prompt_generation",
                "summary": {
                    "total_found": len(deduplicated_news),
                    "returned_count": len(selected_news),
                    "requested_limit": limit,
                    "duplicates_removed": len(all_news_items) - len(deduplicated_news),
                    "topic": topic,
                    "time_range": time_range_desc,
                    "platforms": list(set(item["platform"] for item in selected_news)),
                    "sorted_by_weight": sort_by_weight
                },
                "ai_prompt": ai_prompt,
                "news_sample": selected_news,
                "usage_note": "请sẽ ai_prompt 字段củanội dunggửi给 AI 进行情感phút析"
            }

            # nếu返回số lượng少ởYêu cầusố lượng，增加提示
            if len(selected_news) < limit and len(deduplicated_news) >= limit:
                result["note"] = "返回数量少ở请求数量làvìđi重逻辑（同một标题ởkhông同平台只giữ lạimộtlần）"
            elif len(deduplicated_news) < limit:
                result["note"] = f"ở指定giờ间范围trong仅找đến {len(deduplicated_news)} tinkhớpcủatin tức"

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

    def _create_sentiment_analysis_prompt(
        self,
        news_data: List[Dict],
        topic: Optional[str]
    ) -> str:
        """
        tạo情感phút析của AI 提示词

        Args:
            news_data: tin tức数据列表（đã排序vàgiới hạn数量）
            topic: 话题关键词

        Returns:
            định dạng化của AI 提示词
        """
        # theo平台phút组
        platform_news = defaultdict(list)
        for item in news_data:
            platform_news[item["platform"]].append({
                "title": item["title"],
                "date": item.get("date", "")
            })

        # 构建提示词
        prompt_parts = []

        # 1. 任务nói明
        if topic:
            prompt_parts.append(f"请phút析đểdưới关ở「{topic}」củatin tức标题của情感倾向。")
        else:
            prompt_parts.append("请phút析đểdướitin tức标题của情感倾向。")

        prompt_parts.append("")
        prompt_parts.append("phút析muốn求：")
        prompt_parts.append("1. 识别每tintin tứccủa情感倾向（正面/负面/trong性）")
        prompt_parts.append("2. 统计各情感类别của数量và百phút比")
        prompt_parts.append("3. phút析không同平台của情感差异")
        prompt_parts.append("4. 总结整体情感趋势")
        prompt_parts.append("5. 列举典型của正面và负面tin tức样本")
        prompt_parts.append("")

        # 2. dữ liệu概览
        prompt_parts.append(f"数据概览：")
        prompt_parts.append(f"- Tổng số tin tức：{len(news_data)}")
        prompt_parts.append(f"- 覆盖平台：{len(platform_news)}")

        # thời gian范围
        dates = set(item.get("date", "") for item in news_data if item.get("date"))
        if dates:
            date_list = sorted(dates)
            if len(date_list) == 1:
                prompt_parts.append(f"- giờ间范围：{date_list[0]}")
            else:
                prompt_parts.append(f"- giờ间范围：{date_list[0]} 至 {date_list[-1]}")

        prompt_parts.append("")

        # 3. theo平台展示mới闻
        prompt_parts.append("tin tức列表（theo平台phút类，đãtheo重muốn性排序）：")
        prompt_parts.append("")

        for platform, items in sorted(platform_news.items()):
            prompt_parts.append(f"【{platform}】({len(items)} tin)")
            for i, item in enumerate(items, 1):
                title = item["title"]
                date_str = f" [{item['date']}]" if item.get("date") else ""
                prompt_parts.append(f"{i}. {title}{date_str}")
            prompt_parts.append("")

        # 4. 输出định dạngnói明
        prompt_parts.append("请theođểdướiđịnh dạng输出phút析结果：")
        prompt_parts.append("")
        prompt_parts.append("## 情感phút布统计")
        prompt_parts.append("- 正面：XXtin (XX%)")
        prompt_parts.append("- 负面：XXtin (XX%)")
        prompt_parts.append("- trong性：XXtin (XX%)")
        prompt_parts.append("")
        prompt_parts.append("## 平台情感đối比")
        prompt_parts.append("[各平台của情感倾向差异]")
        prompt_parts.append("")
        prompt_parts.append("## 整体情感趋势")
        prompt_parts.append("[总体phút析và关键发现]")
        prompt_parts.append("")
        prompt_parts.append("## 典型样本")
        prompt_parts.append("正面tin tức样本：")
        prompt_parts.append("[列举3-5tin]")
        prompt_parts.append("")
        prompt_parts.append("负面tin tức样本：")
        prompt_parts.append("[列举3-5tin]")

        return "\n".join(prompt_parts)

    def find_similar_news(
        self,
        reference_title: str,
        threshold: float = 0.6,
        limit: int = 50,
        include_url: bool = False
    ) -> Dict:
        """
        相似tin tức查找 - 基ở标题相似度查找相关tin tức

        Args:
            reference_title: 参考标题
            threshold: 相似度阈值（0-1之间）
            limit: 返回tin数giới hạn，默认50
            include_url: là否包含URL链接，默认False（节省token）

        Returns:
            相似tin tức列表

        Examples:
            用户询问示例：
            - "找出và'特斯拉降价'相似củatin tức"
            - "查找关ởiPhone发布của类似报道"
            - "xemxemcókhông cóvànàytintin tức相似của报道"

            代码调用示例：
            >>> tools = AnalyticsTools()
            >>> result = tools.find_similar_news(
            ...     reference_title="特斯拉宣布降价",
            ...     threshold=0.6,
            ...     limit=10
            ... )
            >>> print(result['similar_news'])
        """
        try:
            # tham số验证
            reference_title = validate_keyword(reference_title)

            if not 0 <= threshold <= 1:
                raise InvalidParameterError(
                    "threshold 必须ở 0 đến 1 之间",
                    suggestion="推荐值：0.5-0.8"
                )

            limit = validate_limit(limit, default=50)

            # đọcdữ liệu
            all_titles, id_to_name, _ = self.data_service.parser.read_all_titles_for_date()

            # tính toán相似度
            similar_items = []

            for platform_id, titles in all_titles.items():
                platform_name = id_to_name.get(platform_id, platform_id)

                for title, info in titles.items():
                    if title == reference_title:
                        continue

                    # tính toán相似度
                    similarity = self._calculate_similarity(reference_title, title)

                    if similarity >= threshold:
                        news_item = {
                            "title": title,
                            "platform": platform_id,
                            "platform_name": platform_name,
                            "similarity": round(similarity, 3),
                            "rank": info["ranks"][0] if info["ranks"] else 0
                        }

                        # tin件性thêm URL 字段
                        if include_url:
                            news_item["url"] = info.get("url", "")

                        similar_items.append(news_item)

            # theo相似度sắp xếp
            similar_items.sort(key=lambda x: x["similarity"], reverse=True)

            # giới hạnsố lượng
            result_items = similar_items[:limit]

            if not result_items:
                raise DataNotFoundError(
                    f"未找đến相似度超过 {threshold} củatin tức",
                    suggestion="请降低相似度阈值hoặc尝试其他标题"
                )

            result = {
                "success": True,
                "summary": {
                    "total_found": len(similar_items),
                    "returned_count": len(result_items),
                    "requested_limit": limit,
                    "threshold": threshold,
                    "reference_title": reference_title
                },
                "similar_news": result_items
            }

            if len(similar_items) < limit:
                result["note"] = f"相似度阈值 {threshold} dưới仅找đến {len(similar_items)} tin相似tin tức"

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

    def search_by_entity(
        self,
        entity: str,
        entity_type: Optional[str] = None,
        limit: int = 50,
        sort_by_weight: bool = True
    ) -> Dict:
        """
        实体识别搜索 - 搜索包含特定người物/地点/机构củatin tức

        Args:
            entity: 实体名称
            entity_type: 实体loại（person/location/organization），có thể选
            limit: 返回tin数giới hạn，默认50，nhất大200
            sort_by_weight: là否theo权重排序，默认True

        Returns:
            实体相关tin tức列表

        Examples:
            用户询问示例：
            - "搜索马斯克相关củatin tức"
            - "查找关ở特斯拉公司của报道，返回前20tin"
            - "xemxem北京có什么tin tức"

            代码调用示例：
            >>> tools = AnalyticsTools()
            >>> result = tools.search_by_entity(
            ...     entity="马斯克",
            ...     entity_type="person",
            ...     limit=20
            ... )
            >>> print(result['related_news'])
        """
        try:
            # tham số验证
            entity = validate_keyword(entity)
            limit = validate_limit(limit, default=50)

            if entity_type and entity_type not in ["person", "location", "organization"]:
                raise InvalidParameterError(
                    f"无效của实体loại: {entity_type}",
                    suggestion="支持củaloại: person, location, organization"
                )

            # đọcdữ liệu
            all_titles, id_to_name, _ = self.data_service.parser.read_all_titles_for_date()

            # tìm kiếm包含实体củamới闻
            related_news = []
            entity_context = Counter()  # 统计实体周边của词

            for platform_id, titles in all_titles.items():
                platform_name = id_to_name.get(platform_id, platform_id)

                for title, info in titles.items():
                    if entity in title:
                        url = info.get("url", "")
                        mobile_url = info.get("mobileUrl", "")
                        ranks = info.get("ranks", [])
                        count = len(ranks)

                        related_news.append({
                            "title": title,
                            "platform": platform_id,
                            "platform_name": platform_name,
                            "url": url,
                            "mobileUrl": mobile_url,
                            "ranks": ranks,
                            "count": count,
                            "rank": ranks[0] if ranks else 999
                        })

                        # Trích xuất实体周边của关键词
                        keywords = self._extract_keywords(title)
                        entity_context.update(keywords)

            if not related_news:
                raise DataNotFoundError(
                    f"未找đến包含实体 '{entity}' củatin tức",
                    suggestion="请尝试其他实体名称"
                )

            # 移除实体本身
            if entity in entity_context:
                del entity_context[entity]

            # Sắp xếp theo trọng số（nếu启用）
            if sort_by_weight:
                related_news.sort(
                    key=lambda x: calculate_news_weight(x),
                    reverse=True
                )
            else:
                # theo排名sắp xếp
                related_news.sort(key=lambda x: x["rank"])

            # giới hạn返回số lượng
            result_news = related_news[:limit]

            return {
                "success": True,
                "entity": entity,
                "entity_type": entity_type or "auto",
                "related_news": result_news,
                "total_found": len(related_news),
                "returned_count": len(result_news),
                "sorted_by_weight": sort_by_weight,
                "related_keywords": [
                    {"keyword": k, "count": v}
                    for k, v in entity_context.most_common(10)
                ]
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

    def generate_summary_report(
        self,
        report_type: str = "daily",
        date_range: Optional[Dict[str, str]] = None
    ) -> Dict:
        """
        每ngày/每周摘muốntạo器 - 自动tạoxu hướng nóng摘muốnbáo cáo

        Args:
            report_type: Loại báo cáo（daily/weekly）
            date_range: tùy chỉnhngày期范围（có thể选）

        Returns:
            Markdownđịnh dạngcủa摘muốnbáo cáo

        Examples:
            用户询问示例：
            - "tạohôm naycủatin tức摘muốnbáo cáo"
            - "给tôimột份本周củaxu hướng nóng总结"
            - "tạo过đi7天củatin tứcphút析báo cáo"

            代码调用示例：
            >>> tools = AnalyticsTools()
            >>> result = tools.generate_summary_report(
            ...     report_type="daily"
            ... )
            >>> print(result['markdown_report'])
        """
        try:
            # tham số验证
            if report_type not in ["daily", "weekly"]:
                raise InvalidParameterError(
                    f"无效củaLoại báo cáo: {report_type}",
                    suggestion="支持củaloại: daily, weekly"
                )

            # 确定ngày范围
            if date_range:
                date_range_tuple = validate_date_range(date_range)
                start_date, end_date = date_range_tuple
            else:
                if report_type == "daily":
                    start_date = end_date = datetime.now()
                else:  # weekly
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=6)

            # 收集dữ liệu
            all_keywords = Counter()
            all_platforms_news = defaultdict(int)
            all_titles_list = []

            current_date = start_date
            while current_date <= end_date:
                try:
                    all_titles, id_to_name, _ = self.data_service.parser.read_all_titles_for_date(
                        date=current_date
                    )

                    for platform_id, titles in all_titles.items():
                        platform_name = id_to_name.get(platform_id, platform_id)
                        all_platforms_news[platform_name] += len(titles)

                        for title in titles.keys():
                            all_titles_list.append({
                                "title": title,
                                "platform": platform_name,
                                "date": current_date.strftime("%Y-%m-%d")
                            })

                            # Trích xuất关键词
                            keywords = self._extract_keywords(title)
                            all_keywords.update(keywords)

                except DataNotFoundError:
                    pass

                current_date += timedelta(days=1)

            # tạobáo cáo
            report_title = f"{'每ngày' if report_type == 'daily' else '每周'}tin tứcxu hướng nóng摘muốn"
            date_str = f"{start_date.strftime('%Y-%m-%d')}" if report_type == "daily" else f"{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}"

            # 构建Markdownbáo cáo
            markdown = f"""# {report_title}

**báo cáongày期**: {date_str}
**tạogiờ间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📊 dữ liệu概览

- **Tổng số tin tức**: {len(all_titles_list)}
- **覆盖平台**: {len(all_platforms_news)}
- **热门关键词数**: {len(all_keywords)}

## 🔥 TOP 10 热门话题

"""

            # thêmTOP 10关键词
            for i, (keyword, count) in enumerate(all_keywords.most_common(10), 1):
                markdown += f"{i}. **{keyword}** - 出现 {count} lần\n"

            # 平台phân tích
            markdown += "\n## 📱 平台活跃度\n\n"
            sorted_platforms = sorted(all_platforms_news.items(), key=lambda x: x[1], reverse=True)

            for platform, count in sorted_platforms:
                markdown += f"- **{platform}**: {count} tintin tức\n"

            # 趋势变化（Nếu là周报）
            if report_type == "weekly":
                markdown += "\n## 📈 趋势phút析\n\n"
                markdown += "本周热度持续của话题（样本数据）：\n\n"

                # 简单của趋势phân tích
                top_keywords = [kw for kw, _ in all_keywords.most_common(5)]
                for keyword in top_keywords:
                    markdown += f"- **{keyword}**: 持续热门\n"

            # thêm样本mới闻（theo权重选择，đảm bảo确定性）
            markdown += "\n## 📰 精选tin tức样本\n\n"

            # 确定性选取：theo标题của权重sắp xếp，取前5tin
            # này样相同输入总là返回相同结果
            if all_titles_list:
                # tính toán每tin tứccủa权重phút数（基ở关键词Số lần xuất hiện）
                news_with_scores = []
                for news in all_titles_list:
                    # 简单权重：thống kê包含TOP关键词củalần数
                    score = 0
                    title_lower = news['title'].lower()
                    for keyword, count in all_keywords.most_common(10):
                        if keyword.lower() in title_lower:
                            score += count
                    news_with_scores.append((news, score))

                # theo权重降序sắp xếp，权重相同则theo标题字母顺序（đảm bảo确定性）
                news_with_scores.sort(key=lambda x: (-x[1], x[0]['title']))

                # 取前5tin
                sample_news = [item[0] for item in news_with_scores[:5]]

                for news in sample_news:
                    markdown += f"- [{news['platform']}] {news['title']}\n"

            markdown += "\n---\n\n*本báo cáodo TrendRadar MCP 自动tạo*\n"

            return {
                "success": True,
                "report_type": report_type,
                "date_range": {
                    "start": start_date.strftime("%Y-%m-%d"),
                    "end": end_date.strftime("%Y-%m-%d")
                },
                "markdown_report": markdown,
                "statistics": {
                    "total_news": len(all_titles_list),
                    "platforms_count": len(all_platforms_news),
                    "keywords_count": len(all_keywords),
                    "top_keyword": all_keywords.most_common(1)[0] if all_keywords else None
                }
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

    def get_platform_activity_stats(
        self,
        date_range: Optional[Dict[str, str]] = None
    ) -> Dict:
        """
        平台活跃度统计 - 统计各平台của发布频率và活跃giờ间段

        Args:
            date_range: ngày期范围（có thể选）

        Returns:
            平台活跃度统计结果

        Examples:
            用户询问示例：
            - "统计各平台hôm naycủa活跃度"
            - "xemxem哪个平台hơn新nhất频繁"
            - "phút析各平台của发布giờ间规律"

            代码调用示例：
            >>> # 查xem各平台活跃度（假设hôm naylà 2025-11-17）
            >>> result = tools.get_platform_activity_stats(
            ...     date_range={"start": "2025-11-08", "end": "2025-11-17"}
            ... )
            >>> print(result['platform_activity'])
        """
        try:
            # tham số验证
            date_range_tuple = validate_date_range(date_range)

            # 确定ngày范围
            if date_range_tuple:
                start_date, end_date = date_range_tuple
            else:
                start_date = end_date = datetime.now()

            # thống kê各平台活跃度
            platform_activity = defaultdict(lambda: {
                "total_updates": 0,
                "days_active": set(),
                "news_count": 0,
                "hourly_distribution": Counter()
            })

            # 遍历ngày范围
            current_date = start_date
            while current_date <= end_date:
                try:
                    all_titles, id_to_name, timestamps = self.data_service.parser.read_all_titles_for_date(
                        date=current_date
                    )

                    for platform_id, titles in all_titles.items():
                        platform_name = id_to_name.get(platform_id, platform_id)

                        platform_activity[platform_name]["news_count"] += len(titles)
                        platform_activity[platform_name]["days_active"].add(current_date.strftime("%Y-%m-%d"))

                        # thống kêcập nhậtlần数（基ởfilesố lượng）
                        platform_activity[platform_name]["total_updates"] += len(timestamps)

                        # thống kêthời gianphút布（基ởfile名trongcủathời gian）
                        for filename in timestamps.keys():
                            # Phân tíchfile名trongcủa小giờ（định dạng：HHMM.txt）
                            match = re.match(r'(\d{2})(\d{2})\.txt', filename)
                            if match:
                                hour = int(match.group(1))
                                platform_activity[platform_name]["hourly_distribution"][hour] += 1

                except DataNotFoundError:
                    pass

                current_date += timedelta(days=1)

            # 转换vìcó thể序列化củađịnh dạng
            result_activity = {}
            for platform, stats in platform_activity.items():
                days_count = len(stats["days_active"])
                avg_news_per_day = stats["news_count"] / days_count if days_count > 0 else 0

                # 找出nhất活跃củathời gian段
                most_active_hours = stats["hourly_distribution"].most_common(3)

                result_activity[platform] = {
                    "total_updates": stats["total_updates"],
                    "news_count": stats["news_count"],
                    "days_active": days_count,
                    "avg_news_per_day": round(avg_news_per_day, 2),
                    "most_active_hours": [
                        {"hour": f"{hour:02d}:00", "count": count}
                        for hour, count in most_active_hours
                    ],
                    "activity_score": round(stats["news_count"] / max(days_count, 1), 2)
                }

            # theo活跃度sắp xếp
            sorted_platforms = sorted(
                result_activity.items(),
                key=lambda x: x[1]["activity_score"],
                reverse=True
            )

            return {
                "success": True,
                "date_range": {
                    "start": start_date.strftime("%Y-%m-%d"),
                    "end": end_date.strftime("%Y-%m-%d")
                },
                "platform_activity": dict(sorted_platforms),
                "most_active_platform": sorted_platforms[0][0] if sorted_platforms else None,
                "total_platforms": len(result_activity)
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

    def analyze_topic_lifecycle(
        self,
        topic: str,
        date_range: Optional[Dict[str, str]] = None
    ) -> Dict:
        """
        话题生命周期phút析 - 追踪话题từ出现đến消失của完整周期

        Args:
            topic: 话题关键词
            date_range: ngày期范围（có thể选）
                       - **định dạng**: {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
                       - **默认**: không指定giờ默认phút析nhất近7天

        Returns:
            话题生命周期phút析结果

        Examples:
            用户询问示例：
            - "phút析'trí tuệ nhân tạo'này个话题của生命周期"
            - "xemxem'iPhone'话题là昙花một现cònlà持续xu hướng nóng"
            - "追踪'比特币'话题của热度变化"

            代码调用示例：
            >>> # phút析话题生命周期（假设hôm naylà 2025-11-17）
            >>> result = tools.analyze_topic_lifecycle(
            ...     topic="trí tuệ nhân tạo",
            ...     date_range={"start": "2025-10-19", "end": "2025-11-17"}
            ... )
            >>> print(result['lifecycle_stage'])
        """
        try:
            # tham số验证
            topic = validate_keyword(topic)

            # Xử lýngày范围（không指定giờ默认nhất近7天）
            if date_range:
                from ..utils.validators import validate_date_range
                date_range_tuple = validate_date_range(date_range)
                start_date, end_date = date_range_tuple
            else:
                # 默认nhất近7天
                end_date = datetime.now()
                start_date = end_date - timedelta(days=6)

            # 收集话题lịch sửdữ liệu
            lifecycle_data = []
            current_date = start_date
            while current_date <= end_date:
                try:
                    all_titles, _, _ = self.data_service.parser.read_all_titles_for_date(
                        date=current_date
                    )

                    # thống kê该ngàycủa话题Số lần xuất hiện
                    count = 0
                    for _, titles in all_titles.items():
                        for title in titles.keys():
                            if topic.lower() in title.lower():
                                count += 1

                    lifecycle_data.append({
                        "date": current_date.strftime("%Y-%m-%d"),
                        "count": count
                    })

                except DataNotFoundError:
                    lifecycle_data.append({
                        "date": current_date.strftime("%Y-%m-%d"),
                        "count": 0
                    })

                current_date += timedelta(days=1)

            # tính toánphân tích天数
            total_days = (end_date - start_date).days + 1

            # phân tích生命周期阶段
            counts = [item["count"] for item in lifecycle_data]

            if not any(counts):
                time_desc = f"{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}"
                raise DataNotFoundError(
                    f"ở {time_desc} trong未找đến话题 '{topic}'",
                    suggestion="请尝试其他话题hoặc扩大giờ间范围"
                )

            # 找đến首lần出现vàcuối cùng出现
            first_appearance = next((item["date"] for item in lifecycle_data if item["count"] > 0), None)
            last_appearance = next((item["date"] for item in reversed(lifecycle_data) if item["count"] > 0), None)

            # tính toán峰giá trị
            max_count = max(counts)
            peak_index = counts.index(max_count)
            peak_date = lifecycle_data[peak_index]["date"]

            # tính toán平均giá trịvà标准差（简单实现）
            non_zero_counts = [c for c in counts if c > 0]
            avg_count = sum(non_zero_counts) / len(non_zero_counts) if non_zero_counts else 0

            # 判断生命周期阶段
            recent_counts = counts[-3:]  # nhất近3天
            early_counts = counts[:3]    # 前3天

            if sum(recent_counts) > sum(early_counts):
                lifecycle_stage = "trên升期"
            elif sum(recent_counts) < sum(early_counts) * 0.5:
                lifecycle_stage = "衰退期"
            elif max_count in recent_counts:
                lifecycle_stage = "爆发期"
            else:
                lifecycle_stage = "稳定期"

            # phútlớp：昙花một现 vs 持续xu hướng nóng
            active_days = sum(1 for c in counts if c > 0)

            if active_days <= 2 and max_count > avg_count * 2:
                topic_type = "昙花một现"
            elif active_days >= total_days * 0.6:
                topic_type = "持续xu hướng nóng"
            else:
                topic_type = "周期性xu hướng nóng"

            return {
                "success": True,
                "topic": topic,
                "date_range": {
                    "start": start_date.strftime("%Y-%m-%d"),
                    "end": end_date.strftime("%Y-%m-%d"),
                    "total_days": total_days
                },
                "lifecycle_data": lifecycle_data,
                "analysis": {
                    "first_appearance": first_appearance,
                    "last_appearance": last_appearance,
                    "peak_date": peak_date,
                    "peak_count": max_count,
                    "active_days": active_days,
                    "avg_daily_mentions": round(avg_count, 2),
                    "lifecycle_stage": lifecycle_stage,
                    "topic_type": topic_type
                }
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

    def detect_viral_topics(
        self,
        threshold: float = 3.0,
        time_window: int = 24
    ) -> Dict:
        """
        ngoại lệ热度检测 - 自动识别突然爆火của话题

        Args:
            threshold: 热度突增倍数阈值
            time_window: 检测giờ间窗口（小giờ）

        Returns:
            爆火话题列表

        Examples:
            用户询问示例：
            - "检测hôm naycó哪些突然爆火của话题"
            - "xemxemcókhông có热度ngoại lệcủatin tức"
            - "预警có thể能của重大事件"

            代码调用示例：
            >>> tools = AnalyticsTools()
            >>> result = tools.detect_viral_topics(
            ...     threshold=3.0,
            ...     time_window=24
            ... )
            >>> print(result['viral_topics'])
        """
        try:
            # tham số验证
            if threshold < 1.0:
                raise InvalidParameterError(
                    "threshold 必须大ởv.v.ở 1.0",
                    suggestion="推荐值：2.0-5.0"
                )

            time_window = validate_limit(time_window, default=24, max_limit=72)

            # đọchiện tạivà之前củadữ liệu
            current_all_titles, _, _ = self.data_service.parser.read_all_titles_for_date()

            # đọchôm quacủadữ liệu作vì基准
            yesterday = datetime.now() - timedelta(days=1)
            try:
                previous_all_titles, _, _ = self.data_service.parser.read_all_titles_for_date(
                    date=yesterday
                )
            except DataNotFoundError:
                previous_all_titles = {}

            # thống kêhiện tạicủa关键词频率
            current_keywords = Counter()
            current_keyword_titles = defaultdict(list)

            for _, titles in current_all_titles.items():
                for title in titles.keys():
                    keywords = self._extract_keywords(title)
                    current_keywords.update(keywords)

                    for kw in keywords:
                        current_keyword_titles[kw].append(title)

            # thống kê之前của关键词频率
            previous_keywords = Counter()

            for _, titles in previous_all_titles.items():
                for title in titles.keys():
                    keywords = self._extract_keywords(title)
                    previous_keywords.update(keywords)

            # 检测ngoại lệ热度
            viral_topics = []

            for keyword, current_count in current_keywords.items():
                previous_count = previous_keywords.get(keyword, 0)

                # tính toán增长倍数
                if previous_count == 0:
                    # mới出现của话题
                    if current_count >= 5:  # ít nhất出现5lần才认vìlà爆火
                        growth_rate = float('inf')
                        is_viral = True
                    else:
                        continue
                else:
                    growth_rate = current_count / previous_count
                    is_viral = growth_rate >= threshold

                if is_viral:
                    viral_topics.append({
                        "keyword": keyword,
                        "current_count": current_count,
                        "previous_count": previous_count,
                        "growth_rate": round(growth_rate, 2) if growth_rate != float('inf') else "新话题",
                        "sample_titles": current_keyword_titles[keyword][:3],
                        "alert_level": "高" if growth_rate > threshold * 2 else "trong"
                    })

            # theo增长率sắp xếp
            viral_topics.sort(
                key=lambda x: x["current_count"] if x["growth_rate"] == "新话题" else x["growth_rate"],
                reverse=True
            )

            if not viral_topics:
                return {
                    "success": True,
                    "viral_topics": [],
                    "total_detected": 0,
                    "message": f"未检测đến热度增长超过 {threshold} 倍của话题"
                }

            return {
                "success": True,
                "viral_topics": viral_topics,
                "total_detected": len(viral_topics),
                "threshold": threshold,
                "time_window": time_window,
                "detection_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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

    def predict_trending_topics(
        self,
        lookahead_hours: int = 6,
        confidence_threshold: float = 0.7
    ) -> Dict:
        """
        话题预测 - 基ở历史数据预测未đếncó thể能củaxu hướng nóng

        Args:
            lookahead_hours: 预测未đến多少小giờ
            confidence_threshold: 置信度阈值

        Returns:
            预测của潜力话题列表

        Examples:
            用户询问示例：
            - "预测接dướiđến6小giờcó thể能củaxu hướng nóng话题"
            - "có哪些话题có thể能sẽ火起đến"
            - "早期发现潜力话题"

            代码调用示例：
            >>> tools = AnalyticsTools()
            >>> result = tools.predict_trending_topics(
            ...     lookahead_hours=6,
            ...     confidence_threshold=0.7
            ... )
            >>> print(result['predicted_topics'])
        """
        try:
            # tham số验证
            lookahead_hours = validate_limit(lookahead_hours, default=6, max_limit=48)

            if not 0 <= confidence_threshold <= 1:
                raise InvalidParameterError(
                    "confidence_threshold 必须ở 0 đến 1 之间",
                    suggestion="推荐值：0.6-0.8"
                )

            # 收集nhất近3天củadữ liệu用ở预测
            keyword_trends = defaultdict(list)

            for days_ago in range(3, 0, -1):
                date = datetime.now() - timedelta(days=days_ago)

                try:
                    all_titles, _, _ = self.data_service.parser.read_all_titles_for_date(
                        date=date
                    )

                    # thống kê关键词
                    keywords_count = Counter()
                    for _, titles in all_titles.items():
                        for title in titles.keys():
                            keywords = self._extract_keywords(title)
                            keywords_count.update(keywords)

                    # bản ghimỗi关键词củalịch sửdữ liệu
                    for keyword, count in keywords_count.items():
                        keyword_trends[keyword].append(count)

                except DataNotFoundError:
                    pass

            # thêmhôm naycủadữ liệu
            try:
                all_titles, _, _ = self.data_service.parser.read_all_titles_for_date()

                keywords_count = Counter()
                keyword_titles = defaultdict(list)

                for _, titles in all_titles.items():
                    for title in titles.keys():
                        keywords = self._extract_keywords(title)
                        keywords_count.update(keywords)

                        for kw in keywords:
                            keyword_titles[kw].append(title)

                for keyword, count in keywords_count.items():
                    keyword_trends[keyword].append(count)

            except DataNotFoundError:
                raise DataNotFoundError(
                    "未找đếnhôm naycủa数据",
                    suggestion="请v.v.待爬虫任务hoàn thành"
                )

            # 预测潜力话题
            predicted_topics = []

            for keyword, trend_data in keyword_trends.items():
                if len(trend_data) < 2:
                    continue

                # 简单của线性趋势预测
                # tính toán增长率
                recent_value = trend_data[-1]
                previous_value = trend_data[-2] if len(trend_data) >= 2 else 0

                if previous_value == 0:
                    if recent_value >= 3:
                        growth_rate = 1.0
                    else:
                        continue
                else:
                    growth_rate = (recent_value - previous_value) / previous_value

                # 判断là否làtrên升趋势
                if growth_rate > 0.3:  # 增长超过30%
                    # tính toán置信度（基ở趋势của稳定性）
                    if len(trend_data) >= 3:
                        # 检查là否连续增长
                        is_consistent = all(
                            trend_data[i] <= trend_data[i+1]
                            for i in range(len(trend_data)-1)
                        )
                        confidence = 0.9 if is_consistent else 0.7
                    else:
                        confidence = 0.6

                    if confidence >= confidence_threshold:
                        predicted_topics.append({
                            "keyword": keyword,
                            "current_count": recent_value,
                            "growth_rate": round(growth_rate * 100, 2),
                            "confidence": round(confidence, 2),
                            "trend_data": trend_data,
                            "prediction": "trên升趋势，có thể能成vìxu hướng nóng",
                            "sample_titles": keyword_titles.get(keyword, [])[:3]
                        })

            # theo置信度và增长率sắp xếp
            predicted_topics.sort(
                key=lambda x: (x["confidence"], x["growth_rate"]),
                reverse=True
            )

            return {
                "success": True,
                "predicted_topics": predicted_topics[:20],  # 返回TOP 20
                "total_predicted": len(predicted_topics),
                "lookahead_hours": lookahead_hours,
                "confidence_threshold": confidence_threshold,
                "prediction_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "note": "预测基ở历史趋势，实际结果có thể能có偏差"
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

    # ==================== 辅助phương thức ====================

    def _extract_keywords(self, title: str, min_length: int = 2) -> List[str]:
        """
        từ标题trong提取关键词（简单实现）

        Args:
            title: 标题文本
            min_length: nhất小关键词长度

        Returns:
            关键词列表
        """
        # 移除URLvà特殊字符
        title = re.sub(r'http[s]?://\S+', '', title)
        title = re.sub(r'[^\w\s]', ' ', title)

        # 简单phút词（theo空格và常见phút隔符）
        words = re.split(r'[\s，。！？、]+', title)

        # lọc停用词và短词
        stopwords = {'của', 'rồi', 'ở', 'là', 'tôi', 'có', 'và', 'thì', 'không', 'người', 'đều', 'một', 'một', 'trên', 'cũng', 'rất', 'đến', 'nói', 'muốn', 'đi', 'bạn', 'sẽ', 'đang', 'không có', 'xem', 'tốt', 'tự mình', 'này'}

        keywords = [
            word.strip() for word in words
            if word.strip() and len(word.strip()) >= min_length and word.strip() not in stopwords
        ]

        return keywords

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        计算两个文本của相似度

        Args:
            text1: 文本1
            text2: 文本2

        Returns:
            相似度phút数（0-1之间）
        """
        # Sử dụng SequenceMatcher tính toán相似度
        return SequenceMatcher(None, text1, text2).ratio()

    def _find_unique_topics(self, platform_stats: Dict) -> Dict[str, List[str]]:
        """
        找出各平台独cócủaxu hướng nóng话题

        Args:
            platform_stats: 平台统计数据

        Returns:
            各平台独có话题字典
        """
        unique_topics = {}

        # Lấymỗi平台củaTOP关键词
        platform_keywords = {}
        for platform, stats in platform_stats.items():
            top_keywords = set([kw for kw, _ in stats["top_keywords"].most_common(10)])
            platform_keywords[platform] = top_keywords

        # 找出独có关键词
        for platform, keywords in platform_keywords.items():
            # 找出其他平台của所có关键词
            other_keywords = set()
            for other_platform, other_kws in platform_keywords.items():
                if other_platform != platform:
                    other_keywords.update(other_kws)

            # 找出独cócủa
            unique = keywords - other_keywords
            if unique:
                unique_topics[platform] = list(unique)[:5]  # nhất多5个

        return unique_topics
