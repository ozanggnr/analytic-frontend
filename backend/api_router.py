"""
Multi-API Stock Data Fetcher
Supports: Finnhub, Alpha Vantage, Polygon, Alpaca
Falls back gracefully when APIs fail or hit rate limits
"""

import os
import requests
from typing import Optional, Dict
import time
from datetime import datetime
from bs4 import BeautifulSoup


class StockAPIRouter:
    def __init__(self):
        # API Keys from environment
        self.finnhub_key = os.getenv('FINNHUB_API_KEY')
        self.alphavantage_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        self.polygon_key = os.getenv('POLYGON_API_KEY')
        
        # Rate limiting dictionary
        self.last_call = {}
        # Finnhub limit is 60/min. 1.2s interval = 50/min (Safe). 
        # Polygon free is 5/min. If we hit fallback, we MUST wait.
        self.min_interval = 1.3  
        
    def _rate_limit(self, api_name: str):
        """Strict rate limiting with sleep"""
        now = time.time()
        if api_name in self.last_call:
            elapsed = now - self.last_call[api_name]
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)
        self.last_call[api_name] = time.time()

    def _handle_api_error(self, e, api_name: str):
        """Handle 429 and other errors"""
        if isinstance(e, requests.exceptions.HTTPError):
            if e.response.status_code == 429:
                print(f"⚠️ {api_name} Rate Limit Hit (429). Cooling down for 60s...")
                time.sleep(60) # Wait for limit reset
                return True
        return False

    def fetch_from_finnhub(self, symbol: str) -> Optional[Dict]:
        """
        Fetch stock data from Finnhub (60 calls/min free tier)
        With Strict 429 Error Handling
        """
        if not self.finnhub_key:
            return None
            
        try:
            self._rate_limit('finnhub')
            
            # Remove .IS suffix for Turkish stocks - Finnhub uses different format
            clean_symbol = symbol.replace('.IS', '.IST') 
            
            url = f"https://finnhub.io/api/v1/quote"
            params = {'symbol': clean_symbol, 'token': self.finnhub_key}
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('c') == 0:
                return None
                
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
            
        except requests.exceptions.HTTPError as e:
            if self._handle_api_error(e, 'finnhub'): # Calls sleep(60) if 429
                return None
            print(f"Finnhub HTTP error for {symbol}: {e}")
            return None
        except Exception as e:
            print(f"Finnhub error for {symbol}: {e}")
            return None
    
    def fetch_from_alpha_vantage(self, symbol: str) -> Optional[Dict]:
        """
        Fetch from Alpha Vantage (25 requests/day free - USE SPARINGLY)
        Best for: Daily data when Finnhub fails
        """
        if not self.alphavantage_key:
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
                'apikey': self.alphavantage_key
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
        With Strict 429 Error Handling
        """
        if not self.polygon_key:
            return None
            
        try:
            self._rate_limit('polygon')
            if symbol.endswith('.IS'): return None
            
            url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/prev"
            params = {'apiKey': self.polygon_key}
            
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            results = data.get('results', [])
            if not results: return None
            
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
        except requests.exceptions.HTTPError as e:
            if self._handle_api_error(e, 'polygon'): # Calls sleep(60) if 429
                return None
            print(f"Polygon HTTP error for {symbol}: {e}")
            return None
        except Exception as e:
            print(f"Polygon error for {symbol}: {e}")
            return None
    
    def fetch_scraped_data(self, symbol: str) -> Optional[Dict]:
        """
        Primary Data Source:
        1. yfinance library (Handles cookies/crumbs automatically)
        2. Google Finance Scraper (Backup)
        """
        # 1. Try yfinance library
        try:
            import yfinance as yf
            # yfinance handles symbols like 'AAPL', 'AKBNK.IS'
            ticker = yf.Ticker(symbol)
            # fast_info is faster than history()
            info = ticker.fast_info
            
            # Check valid price
            price = info.last_price
            prev_close = info.previous_close
            
            if price is not None and price > 0:
                change_pct = ((price - prev_close) / prev_close) * 100 if prev_close else 0
                
                return {
                    "symbol": symbol,
                    "price": round(price, 2),
                    "change_pct": round(change_pct, 2),
                    "volume": 0 # Optimization
                }
        except Exception:
            pass # Try backup

        # 2. Backup: Google Finance (Global + Turkish)
        gf_symbol = symbol
        if symbol.endswith('.IS'):
            gf_symbol = f"BIST:{symbol.replace('.IS', '')}"
        elif symbol in ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'BRK.B']:
            gf_symbol = f"NASDAQ:{symbol}"
        
        try:
            url = f"https://www.google.com/finance/quote/{gf_symbol}"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                price_div = soup.find('div', class_='YMlKec fxKbKc')
                if not price_div: price_div = soup.find('div', class_='YMlKec')
                
                if price_div:
                    p_text = price_div.get_text().replace('₺', '').replace('$', '').replace(',', '').strip()
                    price = float(p_text)
                    
                    # Sanity check for BIST index confusion (avoid 49k if not index)
                    # If it's TR stock and price > 15000, probably index. (Except occasional outliers?)
                    if not (symbol.endswith('.IS') and price > 15000):
                        return {
                            "symbol": symbol,
                            "price": price,
                            "change_pct": 0.0,
                            "volume": 0
                        }
        except Exception:
            pass
            
        return None

    def fetch_price(self, symbol: str) -> Optional[Dict]:
        """
        Fetch current price data.
        Priority: Scraper (yfinance/Google) -> Finnhub -> Polygon -> Alpha Vantage
        """
        # 1. Scraping (Unlimited, Primary)
        data = self.fetch_scraped_data(symbol)
        if data: return data

        # 2. Finnhub (API, 60/min)
        data = self.fetch_from_finnhub(symbol)
        if data: return data
        
        # 3. Polygon (API, 5/min)
        data = self.fetch_from_polygon(symbol)
        if data: return data
        
        # 4. Alpha Vantage (Backup)
        data = self.fetch_from_alpha_vantage(symbol)
        if data: return data
        
        return None

    def fetch_history(self, symbol: str, period: str = "1mo") -> Optional[Dict]:
        """
        Fetch historical candle data for charts.
        Priority: Finnhub -> Polygon -> Alpha Vantage
        """
        # Convert period to timestamps (start/end)
        end_ts = int(time.time())
        start_ts = end_ts - (30 * 24 * 3600) # Default 1mo
        resolution = "D"
        
        if period == "1d":
            start_ts = end_ts - (24 * 3600)
            resolution = "15" # 15 min
        elif period == "1wk":
            start_ts = end_ts - (7 * 24 * 3600)
            resolution = "60"
        elif period == "1mo":
            start_ts = end_ts - (30 * 24 * 3600)
            resolution = "D" 
        elif period == "1y":
            start_ts = end_ts - (365 * 24 * 3600)
            resolution = "D" # Daily is best for 1y to avoid limits
        elif period == "5y":
            start_ts = end_ts - (5 * 365 * 24 * 3600)
            resolution = "W" # Weekly
            
        # Try Finnhub (Best for candles)
        if self.finnhub_key:
            try:
                self._rate_limit('finnhub')
                clean_symbol = symbol.replace('.IS', '.IST')
                
                # Finnhub resolution mapping
                # Supported: 1, 5, 15, 30, 60, D, W, M
                fh_res = resolution
                if resolution == "15": fh_res = "15"
                if resolution == "60": fh_res = "60"
                if resolution == "W": fh_res = "W"
                
                url = "https://finnhub.io/api/v1/stock/candle"
                params = {
                    'symbol': clean_symbol,
                    'resolution': fh_res,
                    'from': start_ts,
                    'to': end_ts,
                    'token': self.finnhub_key
                }
                
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 429:
                     print(f"Finnhub History 429 for {symbol}")
                     # Fallthrough
                else:
                    data = response.json()
                    
                    if data.get('s') == 'ok':
                        # Convert to our format
                        history = []
                        times = data.get('t', [])
                        opens = data.get('o', [])
                        highs = data.get('h', [])
                        lows = data.get('l', [])
                        closes = data.get('c', [])
                        
                        for i in range(len(times)):
                            ts = datetime.fromtimestamp(times[i])
                            time_str = ts.strftime("%Y-%m-%d %H:%M") if "m" in period or period=="1d" else ts.strftime("%Y-%m-%d")
                            history.append({
                                "time": time_str,
                                "open": opens[i],
                                "high": highs[i],
                                "low": lows[i],
                                "close": closes[i]
                            })
                        return {"symbol": symbol, "history": history}
                    
            except Exception as e:
                print(f"Finnhub history error: {e}")

        # Try Polygon (US only)
        if self.polygon_key and not symbol.endswith(".IS"):
            try:
                self._rate_limit('polygon')
                multiplier = 1
                timespan = "day"
                
                if period == "1d": 
                    timespan = "minute"
                    multiplier = 15
                elif period == "1y":
                    timespan = "day"
                elif period == "5y":
                    timespan = "week"
                    
                start_date = datetime.fromtimestamp(start_ts).strftime("%Y-%m-%d")
                end_date = datetime.fromtimestamp(end_ts).strftime("%Y-%m-%d")
                
                url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/range/{multiplier}/{timespan}/{start_date}/{end_date}"
                params = {'apiKey': self.polygon_key, 'limit': 500}
                
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 429:
                    print(f"Polygon History 429 for {symbol}")
                    # Fallthrough
                else:
                    data = response.json()
                    
                    if data.get('results'):
                        history = []
                        for bar in data['results']:
                            ts = datetime.fromtimestamp(bar['t'] / 1000)
                            time_str = ts.strftime("%Y-%m-%d %H:%M") if period=="1d" else ts.strftime("%Y-%m-%d")
                            history.append({
                                "time": time_str,
                                "open": bar.get('o'),
                                "high": bar.get('h'),
                                "low": bar.get('l'),
                                "close": bar.get('c')
                            })
                        return {"symbol": symbol, "history": history}
                    
            except Exception as e:
                print(f"Polygon history error: {e}")

        return None


# Global router instance
_router = None

def get_router() -> StockAPIRouter:
    """Get singleton router instance"""
    global _router
    if _router is None:
        _router = StockAPIRouter()
    return _router
