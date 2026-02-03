"""
Multi-API Router with Intelligent Rate Limiting
Maximizes data fetching speed by rotating across multiple APIs
"""

import time
from dataclasses import dataclass
from typing import Optional, Dict, List, Callable
from collections import deque
import threading


@dataclass
class APIConfig:
    """Configuration for each API"""
    name: str
    rpm: int  # requests per minute
    supports_turkish: bool
    supports_global: bool
    fetch_function: Optional[Callable] = None
    enabled: bool = True
    

class RateLimiter:
    """Per-API rate limiter with sliding window"""
    
    def __init__(self, requests_per_minute: int):
        self.rpm = requests_per_minute
        self.request_times = deque()
        self.lock = threading.Lock()
        
    def wait_if_needed(self):
        """Block if rate limit would be exceeded"""
        with self.lock:
            now = time.time()
            
            # Remove requests older than 1 minute
            while self.request_times and self.request_times[0] < now - 60:
                self.request_times.popleft()
            
            # If at limit, wait until oldest request expires
            if len(self.request_times) >= self.rpm:
                sleep_time = 60 - (now - self.request_times[0]) + 0.1
                if sleep_time > 0:
                    print(f"⏳ Rate limit reached, waiting {sleep_time:.1f}s...")
                    time.sleep(sleep_time)
                    # Clean up again after waiting
                    now = time.time()
                    while self.request_times and self.request_times[0] < now - 60:
                        self.request_times.popleft()
            
            # Record this request
            self.request_times.append(now)
    
    def get_available_slots(self) -> int:
        """Get number of available request slots in current window"""
        with self.lock:
            now = time.time()
            # Remove old requests
            while self.request_times and self.request_times[0] < now - 60:
                self.request_times.popleft()
            return max(0, self.rpm - len(self.request_times))


class MultiAPIRouter:
    """
    Intelligent API router that distributes requests across multiple APIs
    to maximize throughput while respecting rate limits
    """
    
    def __init__(self):
        self.apis: List[APIConfig] = []
        self.rate_limiters: Dict[str, RateLimiter] = {}
        self._setup_apis()
        
    def _setup_apis(self):
        """Initialize all available APIs"""
        from backup_data import (
            fetch_from_yahoo,
            fetch_from_polygon, 
            fetch_from_alpaca,
            fetch_from_finnhub,
            fetch_from_alpha_vantage
        )
        
        # Define API configurations in priority order
        api_configs = [
            APIConfig("yahoo", 33, True, True, fetch_from_yahoo),
            APIConfig("alpaca", 200, False, True, fetch_from_alpaca),
            APIConfig("finnhub", 60, True, True, fetch_from_finnhub),
            APIConfig("polygon", 5, False, True, fetch_from_polygon),
            APIConfig("alpha_vantage", 5, False, True, fetch_from_alpha_vantage),
        ]
        
        for config in api_configs:
            self.apis.append(config)
            self.rate_limiters[config.name] = RateLimiter(config.rpm)
            
        print(f"✓ Initialized {len(self.apis)} APIs")
    
    def _get_available_apis(self, is_turkish: bool) -> List[APIConfig]:
        """Get list of APIs that support the stock type"""
        if is_turkish:
            # Only Yahoo and Finnhub support Turkish stocks
            return [api for api in self.apis 
                   if api.enabled and api.supports_turkish]
        else:
            # All APIs support global stocks
            return [api for api in self.apis 
                   if api.enabled and api.supports_global]
    
    def fetch_stock(self, symbol: str, is_turkish: bool = False) -> Optional[Dict]:
        """
        Fetch stock data using best available API
        
        Args:
            symbol: Stock symbol (e.g., "AAPL" or "AKBNK.IS")
            is_turkish: Whether this is a Turkish stock
            
        Returns:
            Stock data dict or None if all APIs fail
        """
        available_apis = self._get_available_apis(is_turkish)
        
        if not available_apis:
            print(f"⚠️ No available APIs for {'Turkish' if is_turkish else 'Global'} stock: {symbol}")
            return None
        
        # Try each API in order
        for api in available_apis:
            try:
                # Wait if rate limited
                self.rate_limiters[api.name].wait_if_needed()
                
                # Fetch data
                data = api.fetch_function(symbol)
                
                if data:
                    # Mark source
                    data['api_source'] = api.name
                    return data
                    
            except Exception as e:
                print(f"⚠️ {api.name} failed for {symbol}: {str(e)[:100]}")
                continue
        
        print(f"✗ All APIs failed for {symbol}")
        return None
    
    def fetch_batch(self, symbols: List[str], is_turkish: bool = False) -> List[Dict]:
        """
        Optimized batch fetching across multiple APIs
        
        Distributes symbols across available APIs based on their rate limits
        for maximum parallel throughput.
        
        Args:
            symbols: List of stock symbols
            is_turkish: Whether these are Turkish stocks
            
        Returns:
            List of stock data dicts
        """
        available_apis = self._get_available_apis(is_turkish)
        
        if not available_apis:
            print(f"⚠️ No APIs available for batch")
            return []
        
        results = []
        symbol_queue = symbols.copy()
        
        print(f"\n📊 Fetching {len(symbols)} {'Turkish' if is_turkish else 'Global'} stocks")
        print(f"Available APIs: {[api.name for api in available_apis]}")
        
        # Process symbols using API rotation
        api_index = 0
        
        while symbol_queue:
            # Rotate to next API
            api = available_apis[api_index % len(available_apis)]
            
            # Check available slots
            available_slots = self.rate_limiters[api.name].get_available_slots()
            
            if available_slots > 0:
                # Fetch up to available slots
                batch_size = min(available_slots, len(symbol_queue))
                
                for _ in range(batch_size):
                    if not symbol_queue:
                        break
                        
                    symbol = symbol_queue.pop(0)
                    
                    try:
                        self.rate_limiters[api.name].wait_if_needed()
                        data = api.fetch_function(symbol)
                        
                        if data:
                            data['api_source'] = api.name
                            results.append(data)
                            print(f"✓ {api.name}: {symbol} ({len(results)}/{len(symbols)})")
                        else:
                            # Try with next API on next iteration
                            print(f"⚠️ {api.name} returned no data for {symbol}, will retry with another API")
                            symbol_queue.append(symbol)
                            
                    except Exception as e:
                        print(f"⚠️ {api.name} error for {symbol}: {str(e)[:100]}")
                        # Re-add to queue to try with another API
                        symbol_queue.append(symbol)
            
            # Move to next API
            api_index += 1
            
            # Safety: if we've cycled through all APIs and still have failures, break
            if api_index > len(available_apis) * 2 and len(symbol_queue) > len(symbols) * 0.5:
                print(f"⚠️ Too many failures, stopping batch processing")
                break
        
        print(f"✅ Batch complete: {len(results)}/{len(symbols)} stocks fetched\n")
        return results
    
    def get_api_stats(self) -> Dict:
        """Get current API usage statistics"""
        stats = {}
        for api in self.apis:
            limiter = self.rate_limiters[api.name]
            stats[api.name] = {
                "rpm_limit": api.rpm,
                "available_slots": limiter.get_available_slots(),
                "enabled": api.enabled,
                "supports_turkish": api.supports_turkish,
                "supports_global": api.supports_global
            }
        return stats


# Global singleton instance
_router_instance = None

def get_router() -> MultiAPIRouter:
    """Get or create the global router instance"""
    global _router_instance
    if _router_instance is None:
        _router_instance = MultiAPIRouter()
    return _router_instance
