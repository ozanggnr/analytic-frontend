import yfinance as yf
import json

def debug_stock(symbol):
    print(f"--- Debugging {symbol} ---")
    ticker = yf.Ticker(symbol)
    
    # Fetch info
    try:
        info = ticker.info
        # Print relevant keys
        keys = ['bid', 'ask', 'dayLow', 'dayHigh', 'regularMarketPreviousClose', 'volume', 'currency', 'quoteType']
        data = {k: info.get(k) for k in keys}
        print(json.dumps(data, indent=2))
        
        # Check history for today
        hist = ticker.history(period="1d")
        print("\nHistory (Last Row):")
        print(hist.tail(1))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_stock("SKBNK.IS")
    debug_stock("THYAO.IS")
