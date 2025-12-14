"""
Vietnam News Data Fetcher for TrendRadar.

This module aggregates data from multiple Vietnamese financial news sources
using custom web scrapers. It provides the same interface as DataFetcher
for seamless integration with the existing system.
"""

import json
import random
import time
from typing import Dict, List, Optional, Tuple, Union

# Import scrapers - using lazy loading to avoid import errors
# when beautifulsoup4 is not installed


class VietnamDataFetcher:
    """
    Data fetcher for Vietnamese news sources using web scraping.
    
    This class provides the same interface as DataFetcher for compatibility
    with the existing TrendRadar system.
    """

    def __init__(self):
        """Initialize the Vietnam data fetcher with all available scrapers."""
        self.scrapers = {}
        self._load_scrapers()

    def _load_scrapers(self):
        """Lazy load scrapers to avoid import errors."""
        try:
            from src.scrapers import VIETNAM_SCRAPERS
            self.scrapers = {
                source_id: scraper_class() 
                for source_id, scraper_class in VIETNAM_SCRAPERS.items()
            }
        except ImportError as e:
            print(f"⚠ Không thể tải scrapers VN: {e}")
            print("  Chạy: pip install beautifulsoup4 lxml")
            self.scrapers = {}

    def is_vietnam_source(self, source_id: str) -> bool:
        """
        Check if a source ID is a Vietnamese source.
        
        Args:
            source_id: The source ID to check
            
        Returns:
            True if this is a Vietnamese source, False otherwise
        """
        return source_id in self.scrapers

    def fetch_data(
        self,
        id_info: Union[str, Tuple[str, str]],
        max_retries: int = 2,
        min_retry_wait: int = 3,
        max_retry_wait: int = 5,
    ) -> Tuple[Optional[str], str, str]:
        """
        Fetch data for specified Vietnamese source ID.
        
        This method is compatible with DataFetcher.fetch_data() interface.
        
        Args:
            id_info: Platform ID or tuple of (ID, alias)
            max_retries: Maximum number of retries
            min_retry_wait: Minimum wait time between retries (seconds)
            max_retry_wait: Maximum wait time between retries (seconds)
            
        Returns:
            Tuple of (response_json_string, id_value, alias)
        """
        if isinstance(id_info, tuple):
            id_value, alias = id_info
        else:
            id_value = id_info
            alias = id_value

        if id_value not in self.scrapers:
            print(f"  ✗ Nguồn VN '{id_value}' không được hỗ trợ")
            return None, id_value, alias

        scraper = self.scrapers[id_value]
        
        retries = 0
        while retries <= max_retries:
            try:
                result = scraper.fetch()
                
                if result and result.get("status") == "success":
                    items_count = len(result.get("items", []))
                    print(f"Lấy {id_value} thành công ({items_count} bài viết)")
                    return json.dumps(result, ensure_ascii=False), id_value, alias
                else:
                    raise ValueError("Không thể lấy dữ liệu hoặc không có bài viết")
                    
            except Exception as e:
                retries += 1
                if retries <= max_retries:
                    wait_time = random.uniform(min_retry_wait, max_retry_wait)
                    print(f"Yêu cầu {id_value} thất bại: {e}. {wait_time:.2f}s sau thử lại...")
                    time.sleep(wait_time)
                else:
                    print(f"Yêu cầu {id_value} thất bại sau {max_retries} lần thử: {e}")
                    return None, id_value, alias
                    
        return None, id_value, alias

    def crawl_websites(
        self,
        ids_list: List[Union[str, Tuple[str, str]]],
        request_interval: int = 2000,  # Longer interval for scraping
    ) -> Tuple[Dict, Dict, List]:
        """
        Crawl multiple Vietnamese websites.
        
        This method is compatible with DataFetcher.crawl_websites() interface.
        
        Args:
            ids_list: List of platform IDs or (ID, name) tuples
            request_interval: Interval between requests in milliseconds
                              (default 2000ms to be respectful to servers)
            
        Returns:
            Tuple of (results, id_to_name, failed_ids)
        """
        results = {}
        id_to_name = {}
        failed_ids = []

        if not self.scrapers:
            print("⚠ Không có scraper VN nào được tải")
            return results, id_to_name, failed_ids

        print(f"\n📰 Bắt đầu thu thập tin tức Việt Nam ({len(ids_list)} nguồn)...")

        for i, id_info in enumerate(ids_list):
            if isinstance(id_info, tuple):
                id_value, name = id_info
            else:
                id_value = id_info
                if id_value in self.scrapers:
                    name = self.scrapers[id_value].source_name
                else:
                    name = id_value

            id_to_name[id_value] = name
            response, _, _ = self.fetch_data(id_info)

            if response:
                try:
                    data = json.loads(response)
                    results[id_value] = {}
                    
                    for index, item in enumerate(data.get("items", []), 1):
                        title = item.get("title")
                        if not title or not str(title).strip():
                            continue
                            
                        title = str(title).strip()
                        url = item.get("url", "")
                        mobile_url = item.get("mobileUrl", "")

                        if title in results[id_value]:
                            results[id_value][title]["ranks"].append(index)
                        else:
                            results[id_value][title] = {
                                "ranks": [index],
                                "url": url,
                                "mobileUrl": mobile_url,
                            }
                except json.JSONDecodeError:
                    print(f"  ✗ Phân tích JSON {id_value} thất bại")
                    failed_ids.append(id_value)
                except Exception as e:
                    print(f"  ✗ Xử lý {id_value} lỗi: {e}")
                    failed_ids.append(id_value)
            else:
                failed_ids.append(id_value)

            # Wait between requests to be respectful to servers
            if i < len(ids_list) - 1:
                actual_interval = request_interval + random.randint(-200, 500)
                actual_interval = max(1000, actual_interval)  # Min 1 second
                time.sleep(actual_interval / 1000)

        # Summary
        success_count = len(results)
        fail_count = len(failed_ids)
        print(f"\n📊 VN Sources - Thành công: {success_count}, Thất bại: {fail_count}")
        if failed_ids:
            print(f"   Thất bại: {failed_ids}")
        
        return results, id_to_name, failed_ids
    
    @staticmethod
    def get_available_sources() -> List[Tuple[str, str]]:
        """
        Get list of available Vietnamese news sources.
        
        Returns:
            List of tuples (source_id, source_name)
        """
        return [
            ("cafef", "CafeF"),
            ("cafef-chungkhoan", "CafeF Chứng Khoán"),
            ("vnexpress-kinhdoanh", "VnExpress Kinh Doanh"),
            ("vnexpress-chungkhoan", "VnExpress Chứng Khoán"),
            ("dantri-kinhdoanh", "Dân Trí Kinh Doanh"),
            ("24hmoney", "24H Money"),
        ]

    @staticmethod
    def get_config_example() -> str:
        """
        Get example configuration for config.yaml.
        
        Returns:
            YAML string example for vietnam_platforms section
        """
        return """
# === TIN TỨC TÀI CHÍNH VIỆT NAM ===
vietnam_platforms:
  - id: "cafef"
    name: "CafeF"
  - id: "cafef-chungkhoan"
    name: "CafeF Chứng Khoán"
  - id: "vnexpress-kinhdoanh"
    name: "VnExpress Kinh Doanh"
  - id: "vnexpress-chungkhoan"
    name: "VnExpress Chứng Khoán"
  - id: "dantri-kinhdoanh"
    name: "Dân Trí Kinh Doanh"
  - id: "24hmoney"
    name: "24H Money"
"""
