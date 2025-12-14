from typing import Dict, List, Optional
from src.config import CONFIG
from src.utils import get_beijing_time
from src.core import PushRecordManager
from src.notifiers.telegram import send_to_telegram
from src.notifiers.email import send_to_email
from src.processors.report_processor import prepare_report_data


def send_to_notifications(
    stats: List[Dict],
    failed_ids: Optional[List] = None,
    report_type: str = "当ngàytổng hợp",
    new_titles: Optional[Dict] = None,
    id_to_name: Optional[Dict] = None,
    update_info: Optional[Dict] = None,
    proxy_url: Optional[str] = None,
    mode: str = "daily",
    html_file_path: Optional[str] = None,
) -> Dict[str, bool]:
    """gửi数据đến多个thông báo平台"""
    results = {}

    if CONFIG["PUSH_WINDOW"]["ENABLED"]:
        push_manager = PushRecordManager()
        time_range_start = CONFIG["PUSH_WINDOW"]["TIME_RANGE"]["START"]
        time_range_end = CONFIG["PUSH_WINDOW"]["TIME_RANGE"]["END"]

        if not push_manager.is_in_time_range(time_range_start, time_range_end):
            now = get_beijing_time()
            print(
                f"Kiểm soát cửa sổ đẩy：当前giờ间 {now.strftime('%H:%M')} khôngở推送giờ间窗口 {time_range_start}-{time_range_end} trong，bỏ qua đẩy"
            )
            return results

        if CONFIG["PUSH_WINDOW"]["ONCE_PER_DAY"]:
            if push_manager.has_pushed_today():
                print(f"Kiểm soát cửa sổ đẩy：Hôm nay đã đẩy rồi，bỏ qua lần đẩy này")
                return results
            else:
                print(f"Kiểm soát cửa sổ đẩy：Lần đẩy đầu tiên hôm nay")

    report_data = prepare_report_data(stats, failed_ids, new_titles, id_to_name, mode)
    telegram_token = CONFIG["TELEGRAM_BOT_TOKEN"]
    telegram_chat_id = CONFIG["TELEGRAM_CHAT_ID"]
    email_from = CONFIG["EMAIL_FROM"]
    email_password = CONFIG["EMAIL_PASSWORD"]
    email_to = CONFIG["EMAIL_TO"]
    email_smtp_server = CONFIG.get("EMAIL_SMTP_SERVER", "")
    email_smtp_port = CONFIG.get("EMAIL_SMTP_PORT", "")

    update_info_to_send = update_info if CONFIG["SHOW_VERSION_UPDATE"] else None

    # Gửi đến Telegram
    if telegram_token and telegram_chat_id:
        results["telegram"] = send_to_telegram(
            telegram_token,
            telegram_chat_id,
            report_data,
            report_type,
            update_info_to_send,
            proxy_url,
            mode,
        )

    # Gửi email
    if email_from and email_password and email_to:
        results["email"] = send_to_email(
            email_from,
            email_password,
            email_to,
            report_type,
            html_file_path,
            email_smtp_server,
            email_smtp_port,
        )

    if not results:
        print("Chưa cấu hình kênh thông báo nào，bỏ qua gửi thông báo")

    # Nếu gửi thành công bất kỳ thông báo nào，và bật chỉ đẩy một lần mỗi ngày，thì ghi lại đẩy
    if (
        CONFIG["PUSH_WINDOW"]["ENABLED"]
        and CONFIG["PUSH_WINDOW"]["ONCE_PER_DAY"]
        and any(results.values())
    ):
        push_manager = PushRecordManager()
        push_manager.record_push(report_type)

    return results
