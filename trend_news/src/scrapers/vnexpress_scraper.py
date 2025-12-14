"""
VnExpress.net news scraper.

Scrapes business and stock market news from vnexpress.net - 
Vietnam's most popular online newspaper.
"""

from typing import Dict, List
from bs4 import BeautifulSoup

from .base_scraper import BaseScraper


class VnExpressKinhDoanhScraper(BaseScraper):
    """Scraper for VnExpress business news section."""
    
    BASE_URL = "https://vnexpress.net"
    
    def __init__(self):
        super().__init__(
            source_id="vnexpress-kinhdoanh",
            source_name="VnExpress Kinh Doanh"
        )
    
    def get_url(self) -> str:
        return f"{self.BASE_URL}/kinh-doanh"
    
    def parse_articles(self, soup: BeautifulSoup) -> List[Dict]:
        """Parse articles from VnExpress business section."""
        articles = []
        seen_urls = set()
        
        # VnExpress sử dụng nhiều class khác nhau cho tiêu đề
        selectors = [
            # Tiêu đề chính
            "h3.title-news a",
            "h2.title-news a",
            "p.title-news a",
            # Tiêu đề trong sidebar
            ".sidebar-1 h4 a",
            ".sidebar-1 h3 a",
            # Tin trong list
            ".list-news h3 a",
            ".item-news h3 a",
            # Featured articles
            ".article-topstory h3 a",
            ".article-topstory h2 a",
        ]
        
        for selector in selectors:
            try:
                elements = soup.select(selector)
                for elem in elements:
                    title = self._clean_title(elem.get_text())
                    url = elem.get('href', '')
                    
                    if not title or len(title) < 10:
                        continue
                    
                    # VnExpress URLs thường đã đầy đủ
                    if not url.startswith('http'):
                        url = self._normalize_url(url, self.BASE_URL)
                    
                    if not url or url in seen_urls:
                        continue
                    
                    # Bỏ qua video, photo, infographic
                    if any(skip in url for skip in ['/video/', '/photo/', '/infographic/', '/podcast/']):
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


class VnExpressChungKhoanScraper(BaseScraper):
    """Scraper for VnExpress stock market news section."""
    
    BASE_URL = "https://vnexpress.net"
    
    def __init__(self):
        super().__init__(
            source_id="vnexpress-chungkhoan",
            source_name="VnExpress Chứng Khoán"
        )
    
    def get_url(self) -> str:
        return f"{self.BASE_URL}/kinh-doanh/chung-khoan"
    
    def parse_articles(self, soup: BeautifulSoup) -> List[Dict]:
        """Parse articles from VnExpress stock market section."""
        articles = []
        seen_urls = set()
        
        selectors = [
            "h3.title-news a",
            "h2.title-news a",
            "p.title-news a",
            ".list-news h3 a",
            ".item-news h3 a",
        ]
        
        for selector in selectors:
            try:
                elements = soup.select(selector)
                for elem in elements:
                    title = self._clean_title(elem.get_text())
                    url = elem.get('href', '')
                    
                    if not title or len(title) < 10:
                        continue
                    
                    if not url.startswith('http'):
                        url = self._normalize_url(url, self.BASE_URL)
                    
                    if not url or url in seen_urls:
                        continue
                    
                    if any(skip in url for skip in ['/video/', '/photo/', '/infographic/']):
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


class VnExpressTaiChinhScraper(BaseScraper):
    """Scraper for VnExpress finance news section."""
    
    BASE_URL = "https://vnexpress.net"
    
    def __init__(self):
        super().__init__(
            source_id="vnexpress-taichinh",
            source_name="VnExpress Tài Chính"
        )
    
    def get_url(self) -> str:
        return f"{self.BASE_URL}/kinh-doanh/tai-chinh"
    
    def parse_articles(self, soup: BeautifulSoup) -> List[Dict]:
        """Parse articles from VnExpress finance section."""
        articles = []
        seen_urls = set()
        
        for link in soup.select("h3.title-news a, h2.title-news a, p.title-news a"):
            title = self._clean_title(link.get_text())
            url = link.get('href', '')
            
            if not title or len(title) < 10:
                continue
            
            if not url.startswith('http'):
                url = self._normalize_url(url, self.BASE_URL)
            
            if not url or url in seen_urls:
                continue
            
            seen_urls.add(url)
            articles.append({
                "title": title,
                "url": url,
                "mobileUrl": ""
            })
        
        return articles[:50]
