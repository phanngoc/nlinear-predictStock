"""
24hmoney.vn news scraper.

Scrapes financial and stock market news from 24hmoney.vn - 
a Vietnamese financial information portal.
"""

from typing import Dict, List
from bs4 import BeautifulSoup

from .base_scraper import BaseScraper


class Money24HScraper(BaseScraper):
    """Scraper for 24hmoney.vn financial news."""
    
    BASE_URL = "https://24hmoney.vn"
    
    def __init__(self):
        super().__init__(
            source_id="24hmoney",
            source_name="24H Money"
        )
    
    def get_url(self) -> str:
        return self.BASE_URL
    
    def parse_articles(self, soup: BeautifulSoup) -> List[Dict]:
        """Parse articles from 24hmoney homepage."""
        articles = []
        seen_urls = set()
        
        # 24hmoney sử dụng link có pattern /news/ hoặc /tin-tuc/
        selectors = [
            "a[href*='/news/']",
            "a[href*='/tin-tuc/']",
            "a[href*='/phan-tich/']",
            "a[href*='/co-phieu/']",
            ".news-item a",
            ".article-item a",
            "h3 a",
            "h2 a",
        ]
        
        for selector in selectors:
            try:
                elements = soup.select(selector)
                for elem in elements:
                    title = self._clean_title(elem.get_text())
                    url = elem.get('href', '')
                    
                    # Bỏ qua tiêu đề quá ngắn
                    if not title or len(title) < 15:
                        continue
                    
                    url = self._normalize_url(url, self.BASE_URL)
                    
                    if not url or url in seen_urls:
                        continue
                    
                    # Chỉ lấy các URL có nội dung tin tức
                    if not any(p in url for p in ['/news/', '/tin-tuc/', '/phan-tich/']):
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


class Money24HChungKhoanScraper(BaseScraper):
    """Scraper for 24hmoney stock market news."""
    
    BASE_URL = "https://24hmoney.vn"
    
    def __init__(self):
        super().__init__(
            source_id="24hmoney-chungkhoan",
            source_name="24H Money Chứng Khoán"
        )
    
    def get_url(self) -> str:
        return f"{self.BASE_URL}/chung-khoan"
    
    def parse_articles(self, soup: BeautifulSoup) -> List[Dict]:
        """Parse articles from 24hmoney stock section."""
        articles = []
        seen_urls = set()
        
        for link in soup.select("a[href*='/news/'], a[href*='/tin-tuc/'], h3 a, h2 a"):
            title = self._clean_title(link.get_text())
            url = link.get('href', '')
            
            if not title or len(title) < 15:
                continue
            
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
