"""
CafeF.vn news scraper.

Scrapes financial news from cafef.vn - one of Vietnam's leading
financial news websites.
"""

from typing import Dict, List
from bs4 import BeautifulSoup

from .base_scraper import BaseScraper


class CafeFScraper(BaseScraper):
    """Scraper for CafeF.vn homepage financial news."""
    
    BASE_URL = "https://cafef.vn"
    
    def __init__(self):
        super().__init__(
            source_id="cafef",
            source_name="CafeF"
        )
    
    def get_url(self) -> str:
        return self.BASE_URL
    
    def parse_articles(self, soup: BeautifulSoup) -> List[Dict]:
        """Parse articles from CafeF homepage."""
        articles = []
        seen_urls = set()
        
        # CafeF có nhiều section khác nhau với các class khác nhau
        selectors = [
            # Tin nổi bật - box đầu tiên
            ".box-category-sapo h2 a",
            ".box-category-sapo h3 a",
            # Tin trong các category box
            ".box-category-item h3 a",
            ".box-category-item h2 a",
            # Tin sidebar và list
            ".list-news li h3 a",
            ".list-news-sub li a",
            # Timeline list (danh sách tin theo thời gian)
            ".tlitem h3 a",
            ".tlitem h2 a",
            # Các box tin khác
            ".box-content h3 a",
            ".box-content h2 a",
            # Tin nổi bật sticky
            ".knswli h3 a",
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
                    
                    # Bỏ qua các link không phải bài viết
                    if any(skip in url for skip in ['/du-lieu/', '/su-kien/', '/video/', '/photo/']):
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


class CafeFChungKhoanScraper(BaseScraper):
    """Scraper for CafeF stock market news section."""
    
    BASE_URL = "https://cafef.vn"
    
    def __init__(self):
        super().__init__(
            source_id="cafef-chungkhoan",
            source_name="CafeF Chứng Khoán"
        )
    
    def get_url(self) -> str:
        return f"{self.BASE_URL}/thi-truong-chung-khoan.chn"
    
    def parse_articles(self, soup: BeautifulSoup) -> List[Dict]:
        """Parse articles from CafeF stock market section."""
        articles = []
        seen_urls = set()
        
        selectors = [
            "h2 a",
            "h3 a",
            ".tlitem a",
            ".list-news li a",
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
                    
                    # Chỉ lấy link bài viết .chn hoặc có ID số
                    if '.chn' not in url and not any(c.isdigit() for c in url.split('/')[-1]):
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


class CafeFDoanhNghiepScraper(BaseScraper):
    """Scraper for CafeF business/enterprise news section."""
    
    BASE_URL = "https://cafef.vn"
    
    def __init__(self):
        super().__init__(
            source_id="cafef-doanhnghiep",
            source_name="CafeF Doanh Nghiệp"
        )
    
    def get_url(self) -> str:
        return f"{self.BASE_URL}/doanh-nghiep.chn"
    
    def parse_articles(self, soup: BeautifulSoup) -> List[Dict]:
        """Parse articles from CafeF business section."""
        articles = []
        seen_urls = set()
        
        for link in soup.select("h2 a, h3 a"):
            title = self._clean_title(link.get_text())
            url = link.get('href', '')
            
            if not title or len(title) < 10:
                continue
            
            url = self._normalize_url(url, self.BASE_URL)
            
            if not url or url in seen_urls:
                continue
            
            if '.chn' not in url:
                continue
            
            seen_urls.add(url)
            articles.append({
                "title": title,
                "url": url,
                "mobileUrl": ""
            })
        
        return articles[:50]
