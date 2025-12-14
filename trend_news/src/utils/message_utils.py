from typing import List, Dict, Optional
from src.config import CONFIG
from src.utils import get_beijing_time
from src.utils.format_utils import format_title_for_platform


def split_content_into_batches(
    report_data: Dict,
    format_type: str,
    update_info: Optional[Dict] = None,
    max_bytes: int = None,
    mode: str = "daily",
) -> List[str]:
    """
    Split content into batches for messaging platforms.
    Ensures integrity of word group title + first news item.
    """
    if max_bytes is None:
        # Default safe size for Telegram is 4096, we use 4000 to be safe
        max_bytes = CONFIG.get("MESSAGE_BATCH_SIZE", 4000)

    batches = []
    total_titles = sum(
        len(stat["titles"]) for stat in report_data["stats"] if stat["count"] > 0
    )
    now = get_beijing_time()

    # Base Header
    base_header = ""
    if format_type == "telegram":
        base_header = f"Tổng số tin tức： {total_titles}\n\n"
    else:
        base_header = f"Tổng số tin tức： {total_titles}\n\n"

    # Base Footer
    base_footer = ""
    if format_type == "telegram":
        base_footer = f"\n\nCập nhật lúc：{now.strftime('%Y-%m-%d %H:%M:%S')}"
        if update_info:
            base_footer += f"\nTrendRadar phát hiện phiên bản mới {update_info['remote_version']}，hiện tại {update_info['current_version']}"
    else:
        base_footer = f"\n\nCập nhật lúc：{now.strftime('%Y-%m-%d %H:%M:%S')}"

    # Stats Header
    stats_header = ""
    if report_data["stats"]:
        if format_type == "telegram":
            stats_header = f"📊 Thống kê từ khóa nóng\n\n"
        else:
            stats_header = f"📊 Thống kê từ khóa nóng\n\n"

    current_batch = base_header
    current_batch_has_content = False

    if (
        not report_data["stats"]
        and not report_data["new_titles"]
        and not report_data["failed_ids"]
    ):
        if mode == "incremental":
            mode_text = "Chế độ tăng dần: Tạm thời không có từ khóa nóng khớp"
        elif mode == "current":
            mode_text = "Chế độ hiện tại: Tạm thời không có từ khóa nóng khớp"
        else:
            mode_text = "Tạm thời không có từ khóa nóng khớp"
        simple_content = f"📭 {mode_text}\n\n"
        final_content = base_header + simple_content + base_footer
        batches.append(final_content)
        return batches

    # Helper function to format title
    def format_title(f_type, t_data, show_src=True):
        from src.renderers.telegram_renderer import TelegramRenderer
        from src.renderers.html_renderer import HTMLRenderer

        if f_type == "telegram":
            return TelegramRenderer.format_title(t_data, show_source=show_src)
        elif f_type == "html":
            return HTMLRenderer.format_title(t_data, show_source=show_src)
        else:
            return format_title_for_platform(f_type, t_data, show_source=show_src)

    # Process Stats
    if report_data["stats"]:
        total_count = len(report_data["stats"])

        # Add stats header
        test_content = current_batch + stats_header
        if (
            len(test_content.encode("utf-8")) + len(base_footer.encode("utf-8"))
            < max_bytes
        ):
            current_batch = test_content
            current_batch_has_content = True
        else:
            if current_batch_has_content:
                batches.append(current_batch + base_footer)
            current_batch = base_header + stats_header
            current_batch_has_content = True

        for i, stat in enumerate(report_data["stats"]):
            word = stat["word"]
            count = stat["count"]
            sequence_display = f"[{i + 1}/{total_count}]"

            # Word Header
            word_header = ""
            if format_type == "telegram":
                if count >= 10:
                    word_header = f"🔥 {sequence_display} {word} : {count} tin\n\n"
                elif count >= 5:
                    word_header = f"📈 {sequence_display} {word} : {count} tin\n\n"
                else:
                    word_header = f"📌 {sequence_display} {word} : {count} tin\n\n"
            else:
                word_header = f"{sequence_display} {word} : {count} tin\n\n"

            # First News Item
            first_news_line = ""
            if stat["titles"]:
                first_title_data = stat["titles"][0]
                formatted_title = format_title(
                    format_type, first_title_data, show_src=True
                )
                first_news_line = f"  1. {formatted_title}\n"
                if len(stat["titles"]) > 1:
                    first_news_line += "\n"

            # Check atomicity
            word_with_first_news = word_header + first_news_line
            test_content = current_batch + word_with_first_news

            if (
                len(test_content.encode("utf-8")) + len(base_footer.encode("utf-8"))
                >= max_bytes
            ):
                if current_batch_has_content:
                    batches.append(current_batch + base_footer)
                current_batch = base_header + stats_header + word_with_first_news
                current_batch_has_content = True
                start_index = 1
            else:
                current_batch = test_content
                current_batch_has_content = True
                start_index = 1

            # Remaining News Items
            for j in range(start_index, len(stat["titles"])):
                title_data = stat["titles"][j]
                formatted_title = format_title(
                    format_type, title_data, show_src=True
                )
                news_line = f"  {j + 1}. {formatted_title}\n"
                if j < len(stat["titles"]) - 1:
                    news_line += "\n"

                test_content = current_batch + news_line
                if (
                    len(test_content.encode("utf-8")) + len(base_footer.encode("utf-8"))
                    >= max_bytes
                ):
                    if current_batch_has_content:
                        batches.append(current_batch + base_footer)
                    current_batch = base_header + stats_header + word_header + news_line
                    current_batch_has_content = True
                else:
                    current_batch = test_content
                    current_batch_has_content = True

            # Separator
            if i < len(report_data["stats"]) - 1:
                separator = "\n\n"
                test_content = current_batch + separator
                if (
                    len(test_content.encode("utf-8")) + len(base_footer.encode("utf-8"))
                    < max_bytes
                ):
                    current_batch = test_content

    # Process New Titles
    if report_data["new_titles"]:
        new_header = ""
        if format_type == "telegram":
            new_header = (
                f"\n\n🆕 Tin tức nóng mới (tổng {report_data['total_new_count']} tin)\n\n"
            )
        else:
            new_header = f"\n\n🆕 Tin tức nóng mới (tổng {report_data['total_new_count']} tin)\n\n"

        test_content = current_batch + new_header
        if (
            len(test_content.encode("utf-8")) + len(base_footer.encode("utf-8"))
            >= max_bytes
        ):
            if current_batch_has_content:
                batches.append(current_batch + base_footer)
            current_batch = base_header + new_header
            current_batch_has_content = True
        else:
            current_batch = test_content
            current_batch_has_content = True

        for source_data in report_data["new_titles"]:
            source_header = ""
            if format_type == "telegram":
                source_header = f"{source_data['source_name']} ({len(source_data['titles'])} tin):\n\n"
            else:
                source_header = f"{source_data['source_name']} ({len(source_data['titles'])} tin):\n\n"

            first_news_line = ""
            if source_data["titles"]:
                first_title_data = source_data["titles"][0]
                title_data_copy = first_title_data.copy()
                title_data_copy["is_new"] = False
                formatted_title = format_title(
                    format_type, title_data_copy, show_src=False
                )
                first_news_line = f"  1. {formatted_title}\n"

            source_with_first_news = source_header + first_news_line
            test_content = current_batch + source_with_first_news

            if (
                len(test_content.encode("utf-8")) + len(base_footer.encode("utf-8"))
                >= max_bytes
            ):
                if current_batch_has_content:
                    batches.append(current_batch + base_footer)
                current_batch = base_header + new_header + source_with_first_news
                current_batch_has_content = True
                start_index = 1
            else:
                current_batch = test_content
                current_batch_has_content = True
                start_index = 1

            for j in range(start_index, len(source_data["titles"])):
                title_data = source_data["titles"][j]
                title_data_copy = title_data.copy()
                title_data_copy["is_new"] = False
                formatted_title = format_title(
                    format_type, title_data_copy, show_src=False
                )
                news_line = f"  {j + 1}. {formatted_title}\n"

                test_content = current_batch + news_line
                if (
                    len(test_content.encode("utf-8")) + len(base_footer.encode("utf-8"))
                    >= max_bytes
                ):
                    if current_batch_has_content:
                        batches.append(current_batch + base_footer)
                    current_batch = base_header + new_header + source_header + news_line
                    current_batch_has_content = True
                else:
                    current_batch = test_content
                    current_batch_has_content = True

            current_batch += "\n"

    # Process Failed IDs
    if report_data["failed_ids"]:
        failed_header = ""
        if format_type == "telegram":
            failed_header = f"\n\n⚠️ Nền tảng lấy dữ liệu thất bại：\n\n"
        else:
            failed_header = f"\n\n⚠️ Nền tảng lấy dữ liệu thất bại：\n\n"

        test_content = current_batch + failed_header
        if (
            len(test_content.encode("utf-8")) + len(base_footer.encode("utf-8"))
            >= max_bytes
        ):
            if current_batch_has_content:
                batches.append(current_batch + base_footer)
            current_batch = base_header + failed_header
            current_batch_has_content = True
        else:
            current_batch = test_content
            current_batch_has_content = True

        for i, id_value in enumerate(report_data["failed_ids"], 1):
            failed_line = f"  • {id_value}\n"
            test_content = current_batch + failed_line
            if (
                len(test_content.encode("utf-8")) + len(base_footer.encode("utf-8"))
                >= max_bytes
            ):
                if current_batch_has_content:
                    batches.append(current_batch + base_footer)
                current_batch = base_header + failed_header + failed_line
                current_batch_has_content = True
            else:
                current_batch = test_content
                current_batch_has_content = True

    if current_batch_has_content:
        batches.append(current_batch + base_footer)

    return batches
