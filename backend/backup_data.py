"""
Multi-API fallback chain for stock data.
Yahoo Finance → Alpaca → Finnhub → Polygon → Alpha Vantage
"""

import requests
import os
import yfinance as yf


def fetch_from_yahoo(symbol):
    """
    Yahoo Finance via yfinance library.
    Primary data source - no API key needed.
    Rate limit: ~33 requests/minute
    """
    try:
        ticker = yf.Ticker(symbol)
        
        # Get latest data (faster than full history)
        hist = ticker.history(period="5d")
        
        if hist.empty:
            return None
        
        latest = hist.iloc[-1]
        prev = hist.iloc[-2] if len(hist) > 1 else latest
        
        current_price = latest['Close']
        prev_close = prev['Close']
        change_pct = ((current_price - prev_close) / prev_close * 100) if prev_close else 0
        
        return {
            "price": round(current_price, 2),
            "change_pct": round(change_pct, 2),
            "high": round(latest['High'], 2),
            "low": round(latest['Low'], 2),
            "open": round(latest['Open'], 2),
            "prev_close": round(prev_close, 2),
            "volume": int(latest['Volume']),
            "source": "Yahoo Finance"
        }
        
    except Exception as e:
        print(f"Yahoo error for {symbol}: {e}")
        return None


def fetch_from_finnhub(symbol):
    """
    Finnhub API: 60 requests/minute free tier.
    Better rate limits than Yahoo Finance.
    """
    try:
        FINNHUB_KEY = os.getenv("FINNHUB_API_KEY", "")
        if not FINNHUB_KEY:
            return None
        
        # Turkish stocks: .IS -> .IST for Finnhub
        clean_symbol = symbol.replace('.IS', '.IST') if symbol.endswith('.IS') else symbol
        
        url = "https://finnhub.io/api/v1/quote"
        params = {"symbol": clean_symbol, "token": FINNHUB_KEY}
        
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        
        if not data or data.get('c') == 0:
            return None
        
        current_price = data.get('c', 0)
        prev_close = data.get('pc', current_price)
        change_pct = ((current_price - prev_close) / prev_close * 100) if prev_close else 0
        
        return {
            "price": current_price,
            "change_pct": change_pct,
            "high": data.get('h', current_price),
            "low": data.get('l', current_price),
            "open": data.get('o', current_price),
            "prev_close": prev_close,
            "volume": 0,
            "source": "Finnhub"
        }
        
    except Exception as e:
        print(f"Finnhub error for {symbol}: {e}")
        return None


def fetch_from_alpha_vantage(symbol):
    """
    Alpha Vantage API: 25 requests/day free tier.
    Use as last resort fallback.
    """
    try:
        AV_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")
        if not AV_KEY:
            return None
        
        # Alpha Vantage doesn't support .IS Turkish stocks well
        if symbol.endswith('.IS'):
            return None
        
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": AV_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if "Global Quote" not in data or not data["Global Quote"]:
            return None
        
        quote = data["Global Quote"]
        
        price = float(quote.get("05. price", 0))
        change_pct = float(quote.get("10. change percent", "0").replace('%', ''))
        
        return {
            "price": price,
            "change_pct": change_pct,
            "high": float(quote.get("03. high", price)),
            "low": float(quote.get("04. low", price)),
            "open": float(quote.get("02. open", price)),
            "prev_close": float(quote.get("08. previous close", price)),
            "volume": int(quote.get("06. volume", 0)),
            "source": "Alpha Vantage"
        }
        
    except Exception as e:
        print(f"Alpha Vantage error for {symbol}: {e}")
        return None


def fetch_from_polygon(symbol):
    """
    Polygon.io API: 5 requests/minute free tier.
    Good for US stocks.
    """
    try:
        POLYGON_KEY = os.getenv("POLYGON_API_KEY", "")
        if not POLYGON_KEY:
            return None
        
        # Polygon doesn't support Turkish stocks
        if symbol.endswith('.IS'):
            return None
        
        # Get previous close first
        url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/prev"
        params = {"apiKey": POLYGON_KEY}
        
        response = requests.get(url, params=params, timeout=5)
        data = response.json()
        
        if data.get("status") != "OK" or not data.get("results"):
            return None
        
        result = data["results"][0]
        
        # Get current price from snapshot
        snapshot_url = f"https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers/{symbol}"
        snap_response = requests.get(snapshot_url, params=params, timeout=5)
        snap_data = snap_response.json()
        
        current_price = result['c']  # Close from previous day as fallback
        
        if snap_data.get("status") == "OK" and snap_data.get("ticker"):
            ticker_data = snap_data["ticker"]
            if "day" in ticker_data and ticker_data["day"].get("c"):
                current_price = ticker_data["day"]["c"]
        
        prev_close = result['c']
        change_pct = ((current_price - prev_close) / prev_close * 100) if prev_close else 0
        
        return {
            "price": round(current_price, 2),
            "change_pct": round(change_pct, 2),
            "high": round(result.get('h', current_price), 2),
            "low": round(result.get('l', current_price), 2),
            "open": round(result.get('o', current_price), 2),
            "prev_close": round(prev_close, 2),
            "volume": int(result.get('v', 0)),
            "source": "Polygon.io"
        }
        
    except Exception as e:
        print(f"Polygon error for {symbol}: {e}")
        return None


def fetch_from_alpaca(symbol):
    """
    Alpaca Market Data API: 200 requests/minute free tier.
    Best rate limits for US stocks.
    """
    try:
        ALPACA_KEY = os.getenv("ALPACA_API_KEY", "")
        ALPACA_SECRET = os.getenv("ALPACA_SECRET_KEY", "")
        
        if not ALPACA_KEY or not ALPACA_SECRET:
            return None
        
        # Alpaca doesn't support Turkish stocks
        if symbol.endswith('.IS'):
            return None
        
        # Use Alpaca's latest quote endpoint
        url = f"https://data.alpaca.markets/v2/stocks/{symbol}/quotes/latest"
        headers = {
            "APCA-API-KEY-ID": ALPACA_KEY,
            "APCA-API-SECRET-KEY": ALPACA_SECRET
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        data = response.json()
        
        if "quote" not in data:
            return None
        
        quote = data["quote"]
        
        # Get latest trade for current price
        trade_url = f"https://data.alpaca.markets/v2/stocks/{symbol}/trades/latest"
        trade_response = requests.get(trade_url, headers=headers, timeout=5)
        trade_data = trade_response.json()
        
        current_price = quote.get('ap', 0)  # Ask price as fallback
        if "trade" in trade_data:
            current_price = trade_data["trade"].get("p", current_price)
        
        # Get previous close from bars
        bars_url = f"https://data.alpaca.markets/v2/stocks/{symbol}/bars/latest"
        bars_response = requests.get(bars_url, headers=headers, timeout=5)
        bars_data = bars_response.json()
        
        prev_close = current_price
        high = current_price
        low = current_price
        open_price = current_price
        volume = 0
        
        if "bar" in bars_data:
            bar = bars_data["bar"]
            prev_close = bar.get('c', current_price)
            high = bar.get('h', current_price)
            low = bar.get('l', current_price)
            open_price = bar.get('o', current_price)
            volume = bar.get('v', 0)
        
        change_pct = ((current_price - prev_close) / prev_close * 100) if prev_close else 0
        
        return {
            "price": round(current_price, 2),
            "change_pct": round(change_pct, 2),
            "high": round(high, 2),
            "low": round(low, 2),
            "open": round(open_price, 2),
            "prev_close": round(prev_close, 2),
            "volume": int(volume),
            "source": "Alpaca"
        }
        
    except Exception as e:
        print(f"Alpaca error for {symbol}: {e}")
        return None


def fetch_with_fallback(symbol):
    """
    Try all APIs in optimized order based on rate limits and coverage.
    For Turkish stocks on cloud (Render), prioritize Finnhub to avoid Yahoo 429 errors.
    Returns data or None if all fail.
    """
    
    # For Turkish stocks: Try Finnhub FIRST (avoids Render IP blocks on Yahoo)
    if symbol.endswith('.IS'):
        # Try Finnhub first (works better on cloud platforms like Render)
        data = fetch_from_finnhub(symbol)
        if data:
            print(f"✓ Finnhub (.IST): {symbol}")
            return data
        
        # Fallback to Yahoo if Finnhub fails
        data = fetch_from_yahoo(symbol)
        if data:
            print(f"✓ Yahoo (fallback): {symbol}")
            return data
            
        print(f"✗ All APIs failed for Turkish stock: {symbol}")
        return None
    
    # For global stocks, try in order of reliability and rate limits
    # Yahoo first (free, no key needed)
    data = fetch_from_yahoo(symbol)
    if data:
        print(f"✓ Yahoo: {symbol}")
        return data
    
    # Alpaca (200 rpm - fastest for US stocks)
    data = fetch_from_alpaca(symbol)
    if data:
        print(f"✓ Alpaca: {symbol}")
        return data
    
    # Finnhub (60 rpm)
    data = fetch_from_finnhub(symbol)
    if data:
        print(f"✓ Finnhub: {symbol}")
        return data
    
    # Polygon (5 rpm)
    data = fetch_from_polygon(symbol)
    if data:
        print(f"✓ Polygon: {symbol}")
        return data
    
    # Alpha Vantage as last resort (5 rpm)
    data = fetch_from_alpha_vantage(symbol)
    if data:
        print(f"✓ Alpha Vantage: {symbol}")
        return data
    
    print(f"✗ All APIs failed for {symbol}")
    return None

