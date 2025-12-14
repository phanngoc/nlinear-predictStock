"""
Dantri.com.vn news scraper.

Scrapes business news from dantri.com.vn - a popular Vietnamese news website.
"""

from typing import Dict, List
from bs4 import BeautifulSoup

from .base_scraper import BaseScraper


class DanTriKinhDoanhScraper(BaseScraper):
    """Scraper for Dân Trí business news section."""
    
    BASE_URL = "https://dantri.com.vn"
    
    def __init__(self):
        super().__init__(
            source_id="dantri-kinhdoanh",
            source_name="Dân Trí Kinh Doanh"
        )
    
    def get_url(self) -> str:
        return f"{self.BASE_URL}/kinh-doanh.htm"
    
    def parse_articles(self, soup: BeautifulSoup) -> List[Dict]:
        """Parse articles from Dân Trí business section."""
        articles = []
        seen_urls = set()
        
        # Dân Trí sử dụng class article-title và nhiều variant khác
        selectors = [
            # Tiêu đề bài viết chính
            "h3.article-title a",
            "h2.article-title a",
            # Tiêu đề trong list
            ".article-item h3 a",
            ".article-item h2 a",
            # Sidebar articles
            ".article-list h3 a",
            # Featured
            ".article-featured h3 a",
            ".article-featured h2 a",
            # Other variants
            "article h3 a",
            "article h2 a",
        ]
        
        for selector in selectors:
            try:
                elements = soup.select(selector)
                for elem in elements:
                    title = self._clean_title(elem.get_text())
                    url = elem.get('href', '')
                    
                    if not title or len(title) < 10:
                        continue
                    
                    url = self._normalize_url(url, self.BASE_URL)
                    
                    if not url or url in seen_urls:
                        continue
                    
                    # Chỉ lấy bài viết .htm
                    if '.htm' not in url:
                        continue
                    
                    # Bỏ qua video, photo
                    if any(skip in url for skip in ['/video/', '/photo/', '/anh/']):
                        continue
                    
                    seen_urls.add(url)
                    articles.append({
                        "title": title,
                        "url": url,
                        "mobileUrl": ""
                    })
            except Exception:
                continue
        
        return articles[:50]


class DanTriChungKhoanScraper(BaseScraper):
    """Scraper for Dân Trí stock market news."""
    
    BASE_URL = "https://dantri.com.vn"
    
    def __init__(self):
        super().__init__(
            source_id="dantri-chungkhoan",
            source_name="Dân Trí Chứng Khoán"
        )
    
    def get_url(self) -> str:
        return f"{self.BASE_URL}/kinh-doanh/chung-khoan.htm"
    
    def parse_articles(self, soup: BeautifulSoup) -> List[Dict]:
        """Parse articles from Dân Trí stock market section."""
        articles = []
        seen_urls = set()
        
        for link in soup.select("h3.article-title a, h2.article-title a, .article-item h3 a"):
            title = self._clean_title(link.get_text())
            url = link.get('href', '')
            
            if not title or len(title) < 10:
                continue
            
            url = self._normalize_url(url, self.BASE_URL)
            
            if not url or url in seen_urls:
                continue
            
            if '.htm' not in url:
                continue
            
            seen_urls.add(url)
            articles.append({
                "title": title,
                "url": url,
                "mobileUrl": ""
            })
        
        return articles[:50]
