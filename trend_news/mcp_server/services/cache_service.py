"""
Dịch vụ cache

Triển khai cơ chế cache TTL, nâng cao hiệu suất truy cập dữ liệu.
"""

import time
from typing import Any, Optional
from threading import Lock


class CacheService:
    """Lớp dịch vụ cache"""

    def __init__(self):
        """Khởi tạo dịch vụ cache"""
        self._cache = {}
        self._timestamps = {}
        self._lock = Lock()

    def get(self, key: str, ttl: int = 900) -> Optional[Any]:
        """
        Lấy dữ liệu từ cache

        Args:
            key: Khóa cache
            ttl: Thời gian sống (giây), mặc định 15 phút

        Returns:
            Giá trị cache, trả về None nếu không tồn tại hoặc đã hết hạn
        """
        with self._lock:
            if key in self._cache:
                # Kiểm tra xem có hết hạn chưa
                if time.time() - self._timestamps[key] < ttl:
                    return self._cache[key]
                else:
                    # Đã hết hạn, xóa cache
                    del self._cache[key]
                    del self._timestamps[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """
        Đặt dữ liệu vào cache

        Args:
            key: Khóa cache
            value: Giá trị cache
        """
        with self._lock:
            self._cache[key] = value
            self._timestamps[key] = time.time()

    def delete(self, key: str) -> bool:
        """
        Xóa cache

        Args:
            key: Khóa cache

        Returns:
            Có xóa thành công hay không
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                del self._timestamps[key]
                return True
        return False

    def clear(self) -> None:
        """Xóa tất cả cache"""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()

    def cleanup_expired(self, ttl: int = 900) -> int:
        """
        Dọn dẹp cache hết hạn

        Args:
            ttl: Thời gian sống (giây)

        Returns:
            Số lượng mục đã dọn dẹp
        """
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, timestamp in self._timestamps.items()
                if current_time - timestamp >= ttl
            ]

            for key in expired_keys:
                del self._cache[key]
                del self._timestamps[key]

            return len(expired_keys)

    def get_stats(self) -> dict:
        """
        Lấy thông tin thống kê cache

        Returns:
            Dictionary thông tin thống kê
        """
        with self._lock:
            return {
                "total_entries": len(self._cache),
                "oldest_entry_age": (
                    time.time() - min(self._timestamps.values())
                    if self._timestamps else 0
                ),
                "newest_entry_age": (
                    time.time() - max(self._timestamps.values())
                    if self._timestamps else 0
                )
            }


# Instance cache toàn cục
_global_cache = None


def get_cache() -> CacheService:
    """
    Lấy instance cache toàn cục

    Returns:
        Instance dịch vụ cache toàn cục
    """
    global _global_cache
    if _global_cache is None:
        _global_cache = CacheService()
    return _global_cache
