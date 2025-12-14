"""
Data processors module for TrendRadar.

Handles data processing, statistics calculation, and frequency word matching.
"""

from src.processors.data_processor import (
    save_titles_to_file,
    parse_file_titles,
    read_all_today_titles,
    process_source_data,
    detect_latest_new_titles,
)
from src.processors.statistics import (
    matches_word_groups,
    count_word_frequency,
)
from src.processors.frequency_words import load_frequency_words
from src.processors.report_processor import prepare_report_data

__all__ = [
    "save_titles_to_file",
    "parse_file_titles",
    "read_all_today_titles",
    "process_source_data",
    "detect_latest_new_titles",
    "load_frequency_words",
    "matches_word_groups",
    "count_word_frequency",
    "prepare_report_data",
]
