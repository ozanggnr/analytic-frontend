# Quick fix: Add missing endpoint routes that frontend expects

# Chart endpoint (frontend calls /api/chart/{symbol}/{period})
@app.get("/api/chart/{symbol}/{period}")
def get_chart_data_new(symbol: str, period: str):
    """Chart data with proper formatting for Plotly"""
    try:
        # Map period to yfinance params
        period_map = {
            "1d": {"period": "1d", "interval": "1h"},
            "1mo": {"period": "1mo", "interval": "1d"},
            "1y": {"period": "1y", "interval": "1wk"},
            "5y": {"period": "5y", "interval": "1wk"}
        }
        
        if period not in period_map:
            period = "1y"  # Default
        
        params = period_map[period]
        
        # Handle Turkish stocks
        if not symbol.endswith('.IS') and symbol not in GLOBAL_SYMBOLS:
            symbol += '.IS'
        
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=params["period"], interval=params["interval"])
        
        if hist.empty:
            raise HTTPException(status_code=404, detail="No chart data")
        
        # Format for frontend
        reset_hist = hist.reset_index()
        data = []
        for _, row in reset_hist.iterrows():
            date_val = row.get('Datetime') or row.get('Date')
            time_fmt = "%Y-%m-%d %H:%M" if period == "1d" else "%Y-%m-%d"
            
            data.append({
                "time": date_val.strftime(time_fmt),
                "open": float(row['Open']),
                "high": float(row['High']),
                "low": float(row['Low']),
                "close": float(row['Close'])
            })
        
        return {"symbol": symbol, "history": data}
    except Exception as e:
        print(f"Chart error for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Route aliases for frontend compatibility
@app.get("/insight")
def get_insight_alias():
    """Alias for /api/insight"""
    return get_insight()

@app.get("/opportunities")
def get_opportunities_alias():
    """Alias for /api/opportunities"""
    return get_opportunities()
