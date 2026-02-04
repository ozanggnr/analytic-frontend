"""
Multi-API Stock Data Fetcher
Supports: Finnhub, Alpha Vantage, Polygon, Alpaca
Falls back gracefully when APIs fail or hit rate limits
"""

import os
import requests
from typing import Optional, Dict
import time

class StockAPIRouter:
    def __init__(self):
        # API Keys from environment
        self.finnhub_key = os.getenv('FINNHUB_API_KEY')
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        self.polygon_key = os.getenv('POLYGON_API_KEY')
        self.alpaca_key = os.getenv('ALPACA_API_KEY')
        self.alpaca_secret = os.getenv('ALPACA_SECRET_KEY')
        
        # Rate limiting (simple counter)
        self.last_call = {}
        self.min_interval = 1.0  # 1 second between calls
        
    def _rate_limit(self, api_name: str):
        """Simple rate limiting"""
        now = time.time()
        if api_name in self.last_call:
            elapsed = now - self.last_call[api_name]
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)
        self.last_call[api_name] = time.time()
    
    def fetch_from_finnhub(self, symbol: str) -> Optional[Dict]:
        """
        Fetch stock data from Finnhub (60 calls/min free tier)
        Best for: Real-time quotes for US and global stocks
        """
        if not self.finnhub_key:
            return None
            
        try:
            self._rate_limit('finnhub')
            
            # Remove .IS suffix for Turkish stocks - Finnhub uses different format
            clean_symbol = symbol.replace('.IS', '.IST')  # Istanbul exchange
            
            # Get quote
            url = f"https://finnhub.io/api/v1/quote"
            params = {'symbol': clean_symbol, 'token': self.finnhub_key}
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            if data.get('c') == 0:  # No data
                return None
                
            # Calculate change percentage
            current_price = data.get('c', 0)
            prev_close = data.get('pc', current_price)
            change_pct = ((current_price - prev_close) / prev_close * 100) if prev_close else 0
            
            return {
                'symbol': symbol,
                'price': round(current_price, 2),
                'change_pct': round(change_pct, 2),
                'high': data.get('h', current_price),
                'low': data.get('l', current_price),
                'open': data.get('o', current_price),
                'prev_close': prev_close,
                'timestamp': data.get('t', int(time.time()))
            }
            
        except Exception as e:
            print(f"Finnhub error for {symbol}: {e}")
            return None
    
    def fetch_from_alpha_vantage(self, symbol: str) -> Optional[Dict]:
        """
        Fetch from Alpha Vantage (25 requests/day free - USE SPARINGLY)
        Best for: Daily data when Finnhub fails
        """
        if not self.alpha_vantage_key:
            return None
            
        try:
            self._rate_limit('alpha_vantage')
            
            # Alpha Vantage doesn't support Turkish stocks well
            if symbol.endswith('.IS'):
                return None
            
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': self.alpha_vantage_key
            }
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            quote = data.get('Global Quote', {})
            if not quote:
                return None
            
            price = float(quote.get('05. price', 0))
            change_pct = float(quote.get('10. change percent', '0').replace('%', ''))
            
            return {
                'symbol': symbol,
                'price': round(price, 2),
                'change_pct': round(change_pct, 2),
                'high': float(quote.get('03. high', price)),
                'low': float(quote.get('04. low', price)),
                'open': float(quote.get('02. open', price)),
                'prev_close': float(quote.get('08. previous close', price)),
                'volume': int(quote.get('06. volume', 0))
            }
            
        except Exception as e:
            print(f"Alpha Vantage error for {symbol}: {e}")
            return None
    
    def fetch_from_polygon(self, symbol: str) -> Optional[Dict]:
        """
        Fetch from Polygon.io (5 calls/min free)
        Best for: US stocks previous day data
        """
        if not self.polygon_key:
            return None
            
        try:
            self._rate_limit('polygon')
            
            # Polygon doesn't support Turkish stocks
            if symbol.endswith('.IS'):
                return None
            
            # Get previous day's data
            url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/prev"
            params = {'apiKey': self.polygon_key}
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            results = data.get('results', [])
            if not results:
                return None
            
            quote = results[0]
            close_price = quote.get('c', 0)
            open_price = quote.get('o', close_price)
            change_pct = ((close_price - open_price) / open_price * 100) if open_price else 0
            
            return {
                'symbol': symbol,
                'price': round(close_price, 2),
                'change_pct': round(change_pct, 2),
                'high': quote.get('h', close_price),
                'low': quote.get('l', close_price),
                'open': open_price,
                'volume': quote.get('v', 0)
            }
            
        except Exception as e:
            print(f"Polygon error for {symbol}: {e}")
            return None
    
    def fetch_stock(self, symbol: str) -> Optional[Dict]:
        """
        Fetch stock data with intelligent fallback
        Priority: Finnhub -> Alpha Vantage -> Polygon
        """
        # Try Finnhub first (best free tier)
        data = self.fetch_from_finnhub(symbol)
        if data:
            return data
        
        # Try Alpha Vantage (limited calls)
        data = self.fetch_from_alpha_vantage(symbol)
        if data:
            return data
        
        # Try Polygon (US stocks only)
        data = self.fetch_from_polygon(symbol)
        if data:
            return data
        
        return None


# Global router instance
_router = None

def get_router() -> StockAPIRouter:
    """Get singleton router instance"""
    global _router
    if _router is None:
        _router = StockAPIRouter()
    return _router
