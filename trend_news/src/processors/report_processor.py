from typing import Dict, List, Optional
from src.config import CONFIG
from src.processors.statistics import matches_word_groups
from src.processors.frequency_words import load_frequency_words


def prepare_report_data(
    stats: List[Dict],
    failed_ids: Optional[List] = None,
    new_titles: Optional[Dict] = None,
    id_to_name: Optional[Dict] = None,
    mode: str = "daily",
) -> Dict:
    """Chuẩn bị dữ liệu báo cáo"""
    processed_new_titles = []

    # ởChế độ tăng dầndướiẩnmới增mới闻khu vực
    hide_new_section = mode == "incremental"

    # Chỉ xử lý phần tin tức mới trong chế độ không ẩn
    if not hide_new_section:
        filtered_new_titles = {}
        if new_titles and id_to_name:
            word_groups, filter_words = load_frequency_words()
            for source_id, titles_data in new_titles.items():
                filtered_titles = {}
                for title, title_data in titles_data.items():
                    if matches_word_groups(title, word_groups, filter_words):
                        filtered_titles[title] = title_data
                if filtered_titles:
                    filtered_new_titles[source_id] = filtered_titles

        if filtered_new_titles and id_to_name:
            for source_id, titles_data in filtered_new_titles.items():
                source_name = id_to_name.get(source_id, source_id)
                source_titles = []

                for title, title_data in titles_data.items():
                    url = title_data.get("url", "")
                    mobile_url = title_data.get("mobileUrl", "")
                    ranks = title_data.get("ranks", [])

                    processed_title = {
                        "title": title,
                        "source_name": source_name,
                        "time_display": "",
                        "count": 1,
                        "ranks": ranks,
                        "rank_threshold": CONFIG["RANK_THRESHOLD"],
                        "url": url,
                        "mobile_url": mobile_url,
                        "is_new": True,
                    }
                    source_titles.append(processed_title)

                if source_titles:
                    processed_new_titles.append(
                        {
                            "source_id": source_id,
                            "source_name": source_name,
                            "titles": source_titles,
                        }
                    )

    processed_stats = []
    for stat in stats:
        if stat["count"] <= 0:
            continue

        processed_titles = []
        for title_data in stat["titles"]:
            processed_title = {
                "title": title_data["title"],
                "source_name": title_data["source_name"],
                "time_display": title_data["time_display"],
                "count": title_data["count"],
                "ranks": title_data["ranks"],
                "rank_threshold": title_data["rank_threshold"],
                "url": title_data.get("url", ""),
                "mobile_url": title_data.get("mobileUrl", ""),
                "is_new": title_data.get("is_new", False),
            }
            processed_titles.append(processed_title)

        processed_stats.append(
            {
                "word": stat["word"],
                "count": stat["count"],
                "percentage": stat.get("percentage", 0),
                "titles": processed_titles,
            }
        )

    return {
        "stats": processed_stats,
        "new_titles": processed_new_titles,
        "failed_ids": failed_ids or [],
        "total_new_count": sum(
            len(source["titles"]) for source in processed_new_titles
        ),
    }
