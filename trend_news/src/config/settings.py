"""
Settings module for TrendRadar.

Handles configuration loading from YAML files and environment variables.
"""

import os
from pathlib import Path
from typing import Dict

import yaml


def load_config() -> Dict:
    """
    Load configuration from YAML file and environment variables.
    
    Environment variables take precedence over config file values.
    
    Returns:
        Dict: Configuration dictionary with all settings
        
    Raises:
        FileNotFoundError: If config file doesn't exist
    """
    config_path = os.environ.get("CONFIG_PATH", "config/config.yaml")

    if not Path(config_path).exists():
        raise FileNotFoundError(f"File cấu hình {config_path} không tồn tại")

    with open(config_path, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    print(f"Tải file cấu hình thành công: {config_path}")

    config = {
        "VERSION_CHECK_URL": config_data["app"]["version_check_url"],
        "SHOW_VERSION_UPDATE": config_data["app"]["show_version_update"],
        "REQUEST_INTERVAL": config_data["crawler"]["request_interval"],
        "REPORT_MODE": os.environ.get("REPORT_MODE", "").strip()
        or config_data["report"]["mode"],
        "RANK_THRESHOLD": config_data["report"]["rank_threshold"],
        "USE_PROXY": config_data["crawler"]["use_proxy"],
        "DEFAULT_PROXY": config_data["crawler"]["default_proxy"],
        "ENABLE_CRAWLER": os.environ.get("ENABLE_CRAWLER", "").strip().lower()
        in ("true", "1")
        if os.environ.get("ENABLE_CRAWLER", "").strip()
        else config_data["crawler"]["enable_crawler"],
        "ENABLE_NOTIFICATION": os.environ.get("ENABLE_NOTIFICATION", "").strip().lower()
        in ("true", "1")
        if os.environ.get("ENABLE_NOTIFICATION", "").strip()
        else config_data["notification"]["enable_notification"],
        "MESSAGE_BATCH_SIZE": config_data["notification"]["message_batch_size"],
        "BATCH_SEND_INTERVAL": config_data["notification"]["batch_send_interval"],
        "PUSH_WINDOW": {
            "ENABLED": os.environ.get("PUSH_WINDOW_ENABLED", "").strip().lower()
            in ("true", "1")
            if os.environ.get("PUSH_WINDOW_ENABLED", "").strip()
            else config_data["notification"]
            .get("push_window", {})
            .get("enabled", False),
            "TIME_RANGE": {
                "START": os.environ.get("PUSH_WINDOW_START", "").strip()
                or config_data["notification"]
                .get("push_window", {})
                .get("time_range", {})
                .get("start", "08:00"),
                "END": os.environ.get("PUSH_WINDOW_END", "").strip()
                or config_data["notification"]
                .get("push_window", {})
                .get("time_range", {})
                .get("end", "22:00"),
            },
            "ONCE_PER_DAY": os.environ.get("PUSH_WINDOW_ONCE_PER_DAY", "").strip().lower()
            in ("true", "1")
            if os.environ.get("PUSH_WINDOW_ONCE_PER_DAY", "").strip()
            else config_data["notification"]
            .get("push_window", {})
            .get("once_per_day", True),
            "RECORD_RETENTION_DAYS": int(
                os.environ.get("PUSH_WINDOW_RETENTION_DAYS", "").strip() or "0"
            )
            or config_data["notification"]
            .get("push_window", {})
            .get("push_record_retention_days", 7),
        },
        "WEIGHT_CONFIG": {
            "RANK_WEIGHT": config_data["weight"]["rank_weight"],
            "FREQUENCY_WEIGHT": config_data["weight"]["frequency_weight"],
            "HOTNESS_WEIGHT": config_data["weight"]["hotness_weight"],
        },
        "PLATFORMS": config_data["platforms"],
    }

    notification = config_data.get("notification", {})
    webhooks = notification.get("webhooks", {})

    config["TELEGRAM_BOT_TOKEN"] = os.environ.get(
        "TELEGRAM_BOT_TOKEN", ""
    ).strip() or webhooks.get("telegram_bot_token", "")
    config["TELEGRAM_CHAT_ID"] = os.environ.get(
        "TELEGRAM_CHAT_ID", ""
    ).strip() or webhooks.get("telegram_chat_id", "")

    config["EMAIL_FROM"] = os.environ.get("EMAIL_FROM", "").strip() or webhooks.get(
        "email_from", ""
    )
    config["EMAIL_PASSWORD"] = os.environ.get(
        "EMAIL_PASSWORD", ""
    ).strip() or webhooks.get("email_password", "")
    config["EMAIL_TO"] = os.environ.get("EMAIL_TO", "").strip() or webhooks.get(
        "email_to", ""
    )
    config["EMAIL_SMTP_SERVER"] = os.environ.get(
        "EMAIL_SMTP_SERVER", ""
    ).strip() or webhooks.get("email_smtp_server", "")
    config["EMAIL_SMTP_PORT"] = os.environ.get(
        "EMAIL_SMTP_PORT", ""
    ).strip() or webhooks.get("email_smtp_port", "")


    notification_sources = []
    if config["TELEGRAM_BOT_TOKEN"] and config["TELEGRAM_CHAT_ID"]:
        token_source = (
            "Biến môi trường" if os.environ.get("TELEGRAM_BOT_TOKEN") else "File cấu hình"
        )
        chat_source = "Biến môi trường" if os.environ.get("TELEGRAM_CHAT_ID") else "File cấu hình"
        notification_sources.append(f"Telegram({token_source}/{chat_source})")
    if config["EMAIL_FROM"] and config["EMAIL_PASSWORD"] and config["EMAIL_TO"]:
        from_source = "Biến môi trường" if os.environ.get("EMAIL_FROM") else "File cấu hình"
        notification_sources.append(f"邮件({from_source})")


    if notification_sources:
        print(f"Nguồn cấu hình kênh thông báo: {', '.join(notification_sources)}")
    else:
        print("Chưa cấu hình kênh thông báo nào")

    return config


print("Đang tải cấu hình...")
CONFIG = load_config()

from src.config.constants import VERSION
print(f"TrendRadar v{VERSION} Hoàn tất tải cấu hình")
print(f"Số lượng nền tảng giám sát: {len(CONFIG['PLATFORMS'])}")

# Count by type
api_count = len([p for p in CONFIG['PLATFORMS'] if p.get('type', 'api') == 'api'])
scraper_count = len([p for p in CONFIG['PLATFORMS'] if p.get('type') == 'scraper'])
if scraper_count > 0:
    print(f"  - API sources: {api_count}, Scraper sources: {scraper_count}")
