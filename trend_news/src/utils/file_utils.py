"""
File utilities for TrendRadar.

Handles file and directory operations.
"""

from pathlib import Path


def ensure_directory_exists(directory: str) -> None:
    """
    Ensure directory exists, create if it doesn't.
    
    Args:
        directory: Directory path to create
    """
    Path(directory).mkdir(parents=True, exist_ok=True)


def get_output_path(subfolder: str, filename: str) -> str:
    """
    Get output file path with date folder structure.
    
    Args:
        subfolder: Subfolder name (e.g., "txt", "html")
        filename: Output filename
        
    Returns:
        str: Full output path
    """
    from src.utils.time_utils import format_date_folder
    
    date_folder = format_date_folder()
    output_dir = Path("output") / date_folder / subfolder
    ensure_directory_exists(str(output_dir))
    return str(output_dir / filename)


def is_first_crawl_today() -> bool:
    """
    Check if this is the first crawl today.
    
    Returns:
        bool: True if first crawl, False otherwise
    """
    from src.utils.time_utils import format_date_folder
    
    date_folder = format_date_folder()
    txt_dir = Path("output") / date_folder / "txt"

    if not txt_dir.exists():
        return True

    files = sorted([f for f in txt_dir.iterdir() if f.suffix == ".txt"])
    return len(files) <= 1
