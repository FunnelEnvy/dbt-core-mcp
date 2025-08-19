import hashlib
import time
from typing import Any, Dict, Optional, Tuple
from collections import OrderedDict
import threading
import json


class LRUCache:
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: OrderedDict[str, Tuple[Any, float]] = OrderedDict()
        self.lock = threading.RLock()
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_requests": 0
        }

    def _generate_hash(self, content: str) -> str:
        return hashlib.sha256(content.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            self.stats["total_requests"] += 1
            
            if key not in self.cache:
                self.stats["misses"] += 1
                return None
            
            value, expiry = self.cache[key]
            
            if time.time() > expiry:
                del self.cache[key]
                self.stats["misses"] += 1
                return None
            
            self.cache.move_to_end(key)
            self.stats["hits"] += 1
            return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        with self.lock:
            if ttl is None:
                ttl = self.default_ttl
            
            expiry = time.time() + ttl
            
            if key in self.cache:
                self.cache.move_to_end(key)
            elif len(self.cache) >= self.max_size:
                self.cache.popitem(last=False)
                self.stats["evictions"] += 1
            
            self.cache[key] = (value, expiry)

    def clear(self) -> None:
        with self.lock:
            self.cache.clear()
            self.stats = {
                "hits": 0,
                "misses": 0,
                "evictions": 0,
                "total_requests": 0
            }

    def get_stats(self) -> Dict[str, Any]:
        with self.lock:
            hit_rate = 0
            if self.stats["total_requests"] > 0:
                hit_rate = self.stats["hits"] / self.stats["total_requests"]
            
            return {
                **self.stats,
                "hit_rate": hit_rate,
                "cache_size": len(self.cache),
                "max_size": self.max_size
            }

    def invalidate_pattern(self, pattern: str) -> int:
        with self.lock:
            keys_to_remove = []
            for key in self.cache:
                if pattern in key:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.cache[key]
            
            return len(keys_to_remove)

    def cleanup_expired(self) -> int:
        with self.lock:
            current_time = time.time()
            keys_to_remove = []
            
            for key, (_, expiry) in self.cache.items():
                if current_time > expiry:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.cache[key]
            
            return len(keys_to_remove)


class CacheManager:
    def __init__(self, cache_size: int = 1000, cache_ttl_minutes: int = 60):
        self.cache = LRUCache(
            max_size=cache_size,
            default_ttl=cache_ttl_minutes * 60
        )
        self.cleanup_interval = 300
        self.last_cleanup = time.time()

    def get_cached_result(self, content_hash: str) -> Optional[Any]:
        self._periodic_cleanup()
        return self.cache.get(content_hash)

    def set_cached_result(self, content_hash: str, result: Any, ttl: Optional[int] = None) -> None:
        self._periodic_cleanup()
        self.cache.set(content_hash, result, ttl)

    def clear_cache(self) -> None:
        self.cache.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        return self.cache.get_stats()

    def invalidate_pattern(self, pattern: str) -> int:
        return self.cache.invalidate_pattern(pattern)

    def generate_cache_key(self, content: str, prefix: str = "") -> str:
        content_hash = self.cache._generate_hash(content)
        if prefix:
            return f"{prefix}:{content_hash}"
        return content_hash

    def cache_yaml_content(self, yaml_content: str, parsed_result: Any, content_type: str = "unknown") -> str:
        cache_key = self.generate_cache_key(yaml_content, prefix=content_type)
        self.set_cached_result(cache_key, parsed_result)
        return cache_key

    def get_cached_yaml(self, yaml_content: str, content_type: str = "unknown") -> Optional[Any]:
        cache_key = self.generate_cache_key(yaml_content, prefix=content_type)
        return self.get_cached_result(cache_key)

    def _periodic_cleanup(self) -> None:
        current_time = time.time()
        if current_time - self.last_cleanup > self.cleanup_interval:
            self.cache.cleanup_expired()
            self.last_cleanup = current_time

    def warm_cache(self, items: Dict[str, Any], prefix: str = "") -> int:
        count = 0
        for key, value in items.items():
            cache_key = f"{prefix}:{key}" if prefix else key
            self.set_cached_result(cache_key, value)
            count += 1
        return count

    def get_memory_usage_estimate(self) -> Dict[str, Any]:
        import sys
        
        total_size = 0
        for key, (value, _) in self.cache.cache.items():
            total_size += sys.getsizeof(key)
            total_size += sys.getsizeof(value)
        
        return {
            "estimated_bytes": total_size,
            "estimated_mb": total_size / (1024 * 1024),
            "items_cached": len(self.cache.cache),
            "average_item_size": total_size / len(self.cache.cache) if self.cache.cache else 0
        }


_global_cache_manager: Optional[CacheManager] = None


def get_cache_manager(cache_size: int = 1000, cache_ttl_minutes: int = 60) -> CacheManager:
    global _global_cache_manager
    if _global_cache_manager is None:
        _global_cache_manager = CacheManager(cache_size, cache_ttl_minutes)
    return _global_cache_manager


def reset_global_cache() -> None:
    global _global_cache_manager
    if _global_cache_manager:
        _global_cache_manager.clear_cache()
        _global_cache_manager = None