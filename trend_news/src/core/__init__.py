"""
Core components module for TrendRadar.

Contains main classes for data fetching, push management, and analysis.
"""

from src.core.data_fetcher import DataFetcher
from src.core.push_manager import PushRecordManager
from src.core.analyzer import NewsAnalyzer

__all__ = ["DataFetcher", "PushRecordManager", "NewsAnalyzer"]


