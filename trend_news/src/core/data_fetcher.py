"""
Data Fetcher for TrendRadar.

Handles fetching news data from external APIs with retry logic.
"""

import json
import random
import time
from typing import Dict, List, Optional, Tuple, Union

import requests

from src.config.settings import CONFIG


class DataFetcher:
    """Data fetcher with retry support."""

    def __init__(self, proxy_url: Optional[str] = None):
        """
        Initialize data fetcher.
        
        Args:
            proxy_url: Optional proxy URL to use for requests
        """
        self.proxy_url = proxy_url

    def fetch_data(
        self,
        id_info: Union[str, Tuple[str, str]],
        max_retries: int = 2,
        min_retry_wait: int = 3,
        max_retry_wait: int = 5,
    ) -> Tuple[Optional[str], str, str]:
        """
        Fetch data for specified ID with retry support.
        
        Args:
            id_info: Platform ID or tuple of (ID, alias)
            max_retries: Maximum number of retries
            min_retry_wait: Minimum wait time between retries (seconds)
            max_retry_wait: Maximum wait time between retries (seconds)
            
        Returns:
            Tuple of (response_text, id_value, alias)
        """
        if isinstance(id_info, tuple):
            id_value, alias = id_info
        else:
            id_value = id_info
            alias = id_value

        url = f"https://newsnow.busiyi.world/api/s?id={id_value}&latest"

        proxies = None
        if self.proxy_url:
            proxies = {"http": self.proxy_url, "https": self.proxy_url}

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Connection": "keep-alive",
            "Cache-Control": "no-cache",
        }

        retries = 0
        while retries <= max_retries:
            try:
                response = requests.get(
                    url, proxies=proxies, headers=headers, timeout=10
                )
                response.raise_for_status()

                data_text = response.text
                data_json = json.loads(data_text)

                status = data_json.get("status", "未知")
                if status not in ["success", "cache"]:
                    raise ValueError(f"响应状态ngoại lệ: {status}")

                status_info = "nhất新数据" if status == "success" else "缓存数据"
                print(f"Lấy {id_value} thành công（{status_info}）")
                return data_text, id_value, alias

            except Exception as e:
                retries += 1
                if retries <= max_retries:
                    base_wait = random.uniform(min_retry_wait, max_retry_wait)
                    additional_wait = (retries - 1) * random.uniform(1, 2)
                    wait_time = base_wait + additional_wait
                    print(
                        f"Yêu cầu {id_value} thất bại: {e}. {wait_time:.2f}giây sau thử lại..."
                    )
                    time.sleep(wait_time)
                else:
                    print(f"Yêu cầu {id_value} thất bại: {e}")
                    return None, id_value, alias
        return None, id_value, alias

    def crawl_websites(
        self,
        ids_list: List[Union[str, Tuple[str, str]]],
        request_interval: int = None,
    ) -> Tuple[Dict, Dict, List]:
        """
        Crawl multiple websites.
        
        Args:
            ids_list: List of platform IDs or (ID, name) tuples
            request_interval: Interval between requests in milliseconds
            
        Returns:
            Tuple of (results, id_to_name, failed_ids)
        """
        if request_interval is None:
            request_interval = CONFIG["REQUEST_INTERVAL"]
            
        results = {}
        id_to_name = {}
        failed_ids = []

        for i, id_info in enumerate(ids_list):
            if isinstance(id_info, tuple):
                id_value, name = id_info
            else:
                id_value = id_info
                name = id_value

            id_to_name[id_value] = name
            response, _, _ = self.fetch_data(id_info)

            if response:
                try:
                    data = json.loads(response)
                    results[id_value] = {}
                    for index, item in enumerate(data.get("items", []), 1):
                        title = item.get("title")
                        if (
                            title is None
                            or isinstance(title, float)
                            or not str(title).strip()
                        ):
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
                    print(f"Phân tích {id_value} 响应thất bại")
                    failed_ids.append(id_value)
                except Exception as e:
                    print(f"Xử lý {id_value} dữ liệu lỗi: {e}")
                    failed_ids.append(id_value)
            else:
                failed_ids.append(id_value)

            if i < len(ids_list) - 1:
                actual_interval = request_interval + random.randint(-10, 20)
                actual_interval = max(50, actual_interval)
                time.sleep(actual_interval / 1000)

        print(f"thành công: {list(results.keys())}, thất bại: {failed_ids}")
        return results, id_to_name, failed_ids
