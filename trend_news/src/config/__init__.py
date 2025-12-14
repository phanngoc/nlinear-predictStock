"""
Configuration module for TrendRadar.

Handles application configuration, constants, and settings.
"""

from src.config.constants import VERSION, SMTP_CONFIGS
from src.config.settings import load_config, CONFIG

__all__ = ["VERSION", "SMTP_CONFIGS", "load_config", "CONFIG"]
