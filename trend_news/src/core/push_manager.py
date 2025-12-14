"""
Push Record Manager for TrendRadar.

Manages push notification records and time window controls.
"""

import json
from datetime import datetime
from pathlib import Path

import pytz

from src.config.settings import CONFIG
from src.utils.time_utils import get_beijing_time


class PushRecordManager:
    """Push notification record manager."""

    def __init__(self):
        """Initialize push record manager."""
        self.record_dir = Path("output") / ".push_records"
        self.ensure_record_dir()
        self.cleanup_old_records()

    def ensure_record_dir(self) -> None:
        """Ensure record directory exists."""
        self.record_dir.mkdir(parents=True, exist_ok=True)

    def get_today_record_file(self) -> Path:
        """
        Get today's record file path.
        
        Returns:
            Path: Path to today's record file
        """
        today = get_beijing_time().strftime("%Y%m%d")
        return self.record_dir / f"push_record_{today}.json"

    def cleanup_old_records(self) -> None:
        """Clean up expired push records."""
        retention_days = CONFIG["PUSH_WINDOW"]["RECORD_RETENTION_DAYS"]
        current_time = get_beijing_time()

        for record_file in self.record_dir.glob("push_record_*.json"):
            try:
                date_str = record_file.stem.replace("push_record_", "")
                file_date = datetime.strptime(date_str, "%Y%m%d")
                file_date = pytz.timezone("Asia/Shanghai").localize(file_date)

                if (current_time - file_date).days > retention_days:
                    record_file.unlink()
                    print(f"Dọn dẹp bản ghi đẩy hết hạn: {record_file.name}")
            except Exception as e:
                print(f"Dọn dẹp file bản ghi thất bại {record_file}: {e}")

    def has_pushed_today(self) -> bool:
        """
        Check if push has been sent today.
        
        Returns:
            bool: True if already pushed today, False otherwise
        """
        record_file = self.get_today_record_file()

        if not record_file.exists():
            return False

        try:
            with open(record_file, "r", encoding="utf-8") as f:
                record = json.load(f)
            return record.get("pushed", False)
        except Exception as e:
            print(f"Đọc bản ghi đẩy thất bại: {e}")
            return False

    def record_push(self, report_type: str) -> None:
        """
        Record a push notification.
        
        Args:
            report_type: Type of report that was pushed
        """
        record_file = self.get_today_record_file()
        now = get_beijing_time()

        record = {
            "pushed": True,
            "push_time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "report_type": report_type,
        }

        try:
            with open(record_file, "w", encoding="utf-8") as f:
                json.dump(record, f, ensure_ascii=False, indent=2)
            print(f"Đã lưu bản ghi đẩy: {report_type} at {now.strftime('%H:%M:%S')}")
        except Exception as e:
            print(f"Lưu bản ghi đẩy thất bại: {e}")

    def is_in_time_range(self, start_time: str, end_time: str) -> bool:
        """
        Check if current time is within specified time range.
        
        Args:
            start_time: Start time in HH:MM format
            end_time: End time in HH:MM format
            
        Returns:
            bool: True if current time is in range, False otherwise
        """
        now = get_beijing_time()
        current_time = now.strftime("%H:%M")

        def normalize_time(time_str: str) -> str:
            """Normalize time string to HH:MM format."""
            try:
                parts = time_str.strip().split(":")
                if len(parts) != 2:
                    raise ValueError(f"giờ间định dạnglỗi: {time_str}")

                hour = int(parts[0])
                minute = int(parts[1])

                if not (0 <= hour <= 23 and 0 <= minute <= 59):
                    raise ValueError(f"giờ间范围lỗi: {time_str}")

                return f"{hour:02d}:{minute:02d}"
            except Exception as e:
                print(f"Lỗi định dạng thời gian '{time_str}': {e}")
                return time_str

        normalized_start = normalize_time(start_time)
        normalized_end = normalize_time(end_time)
        normalized_current = normalize_time(current_time)

        result = normalized_start <= normalized_current <= normalized_end

        if not result:
            print(
                f"Xác định cửa sổ thời gian：hiện tại {normalized_current}，cửa sổ {normalized_start}-{normalized_end}"
            )

        return result
