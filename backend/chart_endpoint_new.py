# Add this as a NEW endpoint in main.py after the existing /api/history endpoint

@app.get("/api/chart/{symbol}/{period}")
def get_chart_data(symbol: str, period: str):
    """
    Returns historical chart data with proper intervals.
    Period: 1d (hourly), 1mo (daily), 1y (weekly)
    """
    try:
        # Map period to yfinance params
        period_map = {
            "1d": {"period": "1d", "interval": "1h"},      # 1 day, hourly candles
            "1mo": {"period": "1mo", "interval": "1d"},    # 1 month, daily candles  
            "1y": {"period": "1y", "interval": "1wk"}      # 1 year, weekly candles
        }
        
        if period not in period_map:
            raise HTTPException(status_code=400, detail="Invalid period")
        
        params = period_map[period]
        
        # Don't auto-append .IS for global stocks
        is_global = symbol in GLOBAL_SYMBOLS or symbol.upper() in GLOBAL_SYMBOLS
        if not is_global and not symbol.endswith(".IS") and "=" not in symbol:
            symbol += ".IS"
        
        # Fetch data
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=params["period"], interval=params["interval"])
        
        if hist.empty:
            raise HTTPException(status_code=404, detail="No data available")
        
        # Get full name
        info = ticker.info
        full_name = info.get('longName') or info.get('shortName') or symbol
        
        # Format data
        reset_hist = hist.reset_index()
        data = []
        for _, row in reset_hist.iterrows():
            date_val = row.get('Datetime') or row.get('Date')
            
            # Format timestamp based on interval
            if period == "1d":  # Hourly data - show time
                time_fmt = "%Y-%m-%d %H:%M"
            else:  # Daily/Weekly - show date only
                time_fmt = "%Y-%m-%d"
            
            data.append({
                "time": date_val.strftime(time_fmt),
                "open": round(row['Open'], 2),
                "high": round(row['High'], 2),
                "low": round(row['Low'], 2),
                "close": round(row['Close'], 2)
            })
            
        return {
            "symbol": symbol,
            "name": full_name,
            "history": data
        }
    except Exception as e:
        print(f"Chart error for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
