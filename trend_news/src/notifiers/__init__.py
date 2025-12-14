"""
Notifiers module for TrendRadar.

Handles sending notifications to various platforms.
"""

from src.notifiers.manager import send_to_notifications
from src.notifiers.telegram import send_to_telegram
from src.notifiers.email import send_to_email

__all__ = [
    "send_to_notifications",
    "send_to_telegram",
    "send_to_email",
]
