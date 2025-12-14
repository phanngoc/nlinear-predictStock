"""
Renderers module for TrendRadar.

Handles content rendering for different platforms (HTML, Feishu, DingTalk, etc.).
NOTE: Full implementations will be done in Phase 6.
"""

from src.renderers.base import BaseRenderer
from src.renderers.html_renderer import HTMLRenderer
from src.renderers.telegram_renderer import TelegramRenderer

__all__ = [
    "BaseRenderer",
    "HTMLRenderer",
    "TelegramRenderer",
]

