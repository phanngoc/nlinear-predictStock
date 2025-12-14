from typing import Dict, Optional
import requests
import time
from src.config import CONFIG
from src.utils.message_utils import split_content_into_batches


def send_to_telegram(
    bot_token: str,
    chat_id: str,
    report_data: Dict,
    report_type: str,
    update_info: Optional[Dict] = None,
    proxy_url: Optional[str] = None,
    mode: str = "daily",
) -> bool:
    """gửiđếnTelegram（支持phút批gửi）"""
    headers = {"Content-Type": "application/json"}
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    proxies = None
    if proxy_url:
        proxies = {"http": proxy_url, "https": proxy_url}

    # Lấy nội dung phân lô
    batches = split_content_into_batches(
        report_data, "telegram", update_info, mode=mode
    )

    print(f"TelegramTin nhắn chia thành {len(batches)} lô gửi [{report_type}]")

    # Gửi từng lô
    for i, batch_content in enumerate(batches, 1):
        batch_size = len(batch_content.encode("utf-8"))
        print(
            f"gửiTelegram第 {i}/{len(batches)} lô，kích thước：{batch_size} byte [{report_type}]"
        )

        # Thêm nhận dạng lô
        if len(batches) > 1:
            batch_header = f"<b>[第 {i}/{len(batches)} lô]</b>\n\n"
            batch_content = batch_header + batch_content

        payload = {
            "chat_id": chat_id,
            "text": batch_content,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }

        try:
            response = requests.post(
                url, headers=headers, json=payload, proxies=proxies, timeout=30
            )
            if response.status_code == 200:
                result = response.json()
                if result.get("ok"):
                    print(f"Telegram第 {i}/{len(batches)} lô gửithành công [{report_type}]")
                    # Khoảng cách giữa các lô
                    if i < len(batches):
                        time.sleep(CONFIG["BATCH_SEND_INTERVAL"])
                else:
                    print(
                        f"Telegram第 {i}/{len(batches)} lôgửi失败 [{report_type}]，lỗi：{result.get('description')}"
                    )
                    return False
            else:
                print(
                    f"Telegram第 {i}/{len(batches)} lôgửi失败 [{report_type}]，mã trạng thái：{response.status_code}"
                )
                return False
        except Exception as e:
            print(f"Telegram第 {i}/{len(batches)} lô gửi出错 [{report_type}]：{e}")
            return False

    print(f"Telegram所có {len(batches)} lô gửihoàn thành [{report_type}]")
    return True
