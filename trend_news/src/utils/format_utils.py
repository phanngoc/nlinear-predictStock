"""
Format utilities for TrendRadar.

Handles formatting for ranks, titles, and content batching.
"""

from typing import Dict, List
from src.utils.text_utils import clean_title, html_escape


def format_rank_display(ranks: List[int], rank_threshold: int, format_type: str) -> str:
    """
    Format rank display for different platforms.
    
    Args:
        ranks: List of rank numbers
        rank_threshold: Threshold for highlighting
        format_type: Platform type (html, telegram)
        
    Returns:
        str: Formatted rank string
    """
    if not ranks:
        return ""

    unique_ranks = sorted(set(ranks))
    min_rank = unique_ranks[0]
    max_rank = unique_ranks[-1]

    if format_type == "html":
        highlight_start = "<font color='red'><strong>"
        highlight_end = "</strong></font>"
    elif format_type == "telegram":
        highlight_start = "<b>"
        highlight_end = "</b>"
    else:
        highlight_start = "**"
        highlight_end = "**"

    if min_rank <= rank_threshold:
        if min_rank == max_rank:
            return f"{highlight_start}[{min_rank}]{highlight_end}"
        else:
            return f"{highlight_start}[{min_rank} - {max_rank}]{highlight_end}"
    else:
        if min_rank == max_rank:
            return f"[{min_rank}]"
        else:
            return f"[{min_rank} - {max_rank}]"


def format_title_for_platform(
    platform: str, title_data: Dict, show_source: bool = True
) -> str:
    """
    Format title for specific platform.
    
    Args:
        platform: Platform name (telegram, html)
        title_data: Title data dictionary
        show_source: Whether to show source name
        
    Returns:
        str: Formatted title string
    """
    rank_display = format_rank_display(
        title_data["ranks"], title_data["rank_threshold"], platform
    )

    link_url = title_data["mobile_url"] or title_data["url"]
    cleaned_title = clean_title(title_data["title"])

    if platform == "telegram":
        # Deprecated: Use TelegramRenderer.format_title instead
        pass
    elif platform == "html":
        # Deprecated: Use HTMLRenderer.format_title instead
        pass

    return cleaned_title
