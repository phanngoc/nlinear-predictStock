"""
Text utilities for TrendRadar.

Handles text cleaning and HTML escaping.
"""

import re


def clean_title(title: str) -> str:
    """
    Clean title by removing special characters and normalizing whitespace.
    
    Args:
        title: Title string to clean
        
    Returns:
        str: Cleaned title
    """
    if not isinstance(title, str):
        title = str(title)
    cleaned_title = title.replace("\n", " ").replace("\r", " ")
    cleaned_title = re.sub(r"\s+", " ", cleaned_title)
    cleaned_title = cleaned_title.strip()
    return cleaned_title


def html_escape(text: str) -> str:
    """
    Escape HTML special characters.
    
    Args:
        text: Text to escape
        
    Returns:
        str: HTML-escaped text
    """
    if not isinstance(text, str):
        text = str(text)

    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


def strip_markdown(text: str) -> str:
    """
    Remove Markdown formatting from text.
    Useful for platforms that don't support Markdown or need plain text.
    """
    # Remove bold **text** or __text__
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)

    # Remove italic *text* or _text_
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)

    # Remove strikethrough ~~text~~
    text = re.sub(r'~~(.+?)~~', r'\1', text)

    # Convert links [text](url) -> text url
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1 \2', text)

    # Remove images ![alt](url) -> alt
    text = re.sub(r'!\[(.+?)\]\(.+?\)', r'\1', text)

    # Remove inline code `code`
    text = re.sub(r'`(.+?)`', r'\1', text)

    # Remove blockquotes >
    text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)

    # Remove headers # ## ###
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)

    # Remove horizontal rules --- or ***
    text = re.sub(r'^[\-\*]{3,}\s*$', '', text, flags=re.MULTILINE)

    # Remove HTML tags
    text = re.sub(r'<font[^>]*>(.+?)</font>', r'\1', text)
    text = re.sub(r'<[^>]+>', '', text)

    # Clean up extra newlines
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()
