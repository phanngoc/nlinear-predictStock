"""
Vietnamese news scrapers package.

This package contains scrapers for Vietnamese financial news sources.
"""

from .base_scraper import BaseScraper
from .cafef_scraper import CafeFScraper, CafeFChungKhoanScraper
from .vnexpress_scraper import VnExpressKinhDoanhScraper, VnExpressChungKhoanScraper
from .dantri_scraper import DanTriKinhDoanhScraper
from .money24h_scraper import Money24HScraper

# Registry of all available Vietnam scrapers
VIETNAM_SCRAPERS = {
    "cafef": CafeFScraper,
    "cafef-chungkhoan": CafeFChungKhoanScraper,
    "vnexpress-kinhdoanh": VnExpressKinhDoanhScraper,
    "vnexpress-chungkhoan": VnExpressChungKhoanScraper,
    "dantri-kinhdoanh": DanTriKinhDoanhScraper,
    "24hmoney": Money24HScraper,
}

__all__ = [
    "BaseScraper",
    "CafeFScraper",
    "CafeFChungKhoanScraper",
    "VnExpressKinhDoanhScraper",
    "VnExpressChungKhoanScraper",
    "DanTriKinhDoanhScraper",
    "Money24HScraper",
    "VIETNAM_SCRAPERS",
]
