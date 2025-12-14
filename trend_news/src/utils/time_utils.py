"""
Time utilities for TrendRadar.

Handles time formatting and Beijing time operations.
"""

from datetime import datetime
import pytz


def get_beijing_time() -> datetime:
    """
    Get current Beijing time.
    
    Returns:
        datetime: Current time in Asia/Shanghai timezone
    """
    return datetime.now(pytz.timezone("Asia/Shanghai"))


def format_date_folder() -> str:
    """
    Format date for folder names.
    
    Returns:
        str: Formatted date string (e.g., "2024năm01tháng15ngày")
    """
    return get_beijing_time().strftime("%Ynăm%mtháng%dngày")


def format_time_filename() -> str:
    """
    Format time for filenames.
    
    Returns:
        str: Formatted time string (e.g., "14giờ30phút")
    """
    return get_beijing_time().strftime("%Hgiờ%Mphút")


def format_time_display(first_time: str, last_time: str) -> str:
    """
    Format time display for reports.
    
    Args:
        first_time: First occurrence time
        last_time: Last occurrence time
        
    Returns:
        str: Formatted time range or single time
    """
    if not first_time:
        return ""
    if first_time == last_time or not last_time:
        return first_time
    else:
        return f"[{first_time} ~ {last_time}]"
