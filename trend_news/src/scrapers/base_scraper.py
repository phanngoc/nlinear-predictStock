"""
Base scraper class for Vietnamese news sources.

This module provides an abstract base class that all Vietnamese news scrapers
should inherit from to ensure consistent interface and behavior.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup


class BaseScraper(ABC):
    """
    Abstract base class for all Vietnamese news scrapers.
    
    Subclasses must implement:
        - get_url(): Return the URL to scrape
        - parse_articles(): Parse articles from BeautifulSoup object
    """
    
    def __init__(self, source_id: str, source_name: str):
        """
        Initialize the scraper.
        
        Args:
            source_id: Unique identifier for this source (e.g., 'cafef')
            source_name: Human-readable name (e.g., 'CafeF')
        """
        self.source_id = source_id
        self.source_name = source_name
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
    
    @abstractmethod
    def get_url(self) -> str:
        """
        Return the URL to scrape.
        
        Returns:
            str: The target URL for this scraper
        """
        pass
    
    @abstractmethod
    def parse_articles(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Parse articles from BeautifulSoup object.
        
        Args:
            soup: BeautifulSoup object of the page HTML
            
        Returns:
            List of article dicts with keys: title, url, mobileUrl
        """
        pass
    
    def fetch(self, timeout: int = 15) -> Optional[Dict]:
        """
        Fetch and parse news from source.
        
        Args:
            timeout: Request timeout in seconds
            
        Returns:
            Dict with format matching the API response:
            {
                "status": "success",
                "id": "source_id",
                "items": [
                    {"title": "...", "url": "...", "mobileUrl": ""},
                    ...
                ]
            }
            Returns None if fetch fails.
        """
        try:
            url = self.get_url()
            response = requests.get(
                url,
                headers=self.headers,
                timeout=timeout,
                allow_redirects=True
            )
            response.raise_for_status()
            
            # Handle encoding for Vietnamese text
            response.encoding = response.apparent_encoding or 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            articles = self.parse_articles(soup)
            
            if not articles:
                print(f"  ⚠ {self.source_name}: Không tìm thấy bài viết nào")
                return None
            
            return {
                "status": "success",
                "id": self.source_id,
                "items": articles
            }
            
        except requests.exceptions.Timeout:
            print(f"  ✗ {self.source_name}: Timeout sau {timeout}s")
            return None
        except requests.exceptions.ConnectionError as e:
            print(f"  ✗ {self.source_name}: Lỗi kết nối - {e}")
            return None
        except requests.exceptions.HTTPError as e:
            print(f"  ✗ {self.source_name}: HTTP Error - {e}")
            return None
        except Exception as e:
            print(f"  ✗ {self.source_name}: Lỗi - {e}")
            return None
    
    def _normalize_url(self, url: str, base_url: str) -> str:
        """
        Normalize relative URLs to absolute URLs.
        
        Args:
            url: The URL to normalize (may be relative)
            base_url: The base URL to prepend if relative
            
        Returns:
            Absolute URL
        """
        if not url:
            return ""
        if url.startswith('http://') or url.startswith('https://'):
            return url
        if url.startswith('//'):
            return 'https:' + url
        if url.startswith('/'):
            return base_url.rstrip('/') + url
        return base_url.rstrip('/') + '/' + url
    
    def _clean_title(self, title: str) -> str:
        """
        Clean and normalize article title.
        
        Args:
            title: Raw title text
            
        Returns:
            Cleaned title
        """
        if not title:
            return ""
        # Remove extra whitespace
        title = ' '.join(title.split())
        # Remove common prefixes/suffixes
        title = title.strip()
        return title
