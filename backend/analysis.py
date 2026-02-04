import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Top ~50 Most Liquid BIST Stocks (reduced for reliability)
BIST_SYMBOLS = [
    # Major Banks (9 stocks)
    "AKBNK.IS", "GARAN.IS", "HALKB.IS", "ISCTR.IS", "YKBNK.IS", "VAKBN.IS", "TSKB.IS", "SKBNK.IS", "ALBRK.IS",
    
    # Major Holdings & Investment (10 stocks)  
    "KCHOL.IS", "SAHOL.IS", "DOHOL.IS", "EKGYO.IS", "GSDHO.IS", "BIMAS.IS", "SISE.IS", "EREGL.IS", "ARCLK.IS", "ENKAI.IS",
    
    # Energy & Utilities (8 stocks)
    "EUPWR.IS", "SMRTG.IS", "ODAS.IS", "ASTOR.IS", "AYDEM.IS", "ZOREN.IS", "KONTR.IS", "GWIND.IS",
    
    # Industry & Auto (8 stocks)
    "FROTO.IS", "TOASO.IS", "TTRAK.IS", "TMSN.IS", "KARSN.IS", "PETKM.IS", "TUPRS.IS", "VESTL.IS",
    
    # Aviation & Transport (4 stocks)
    "THYAO.IS", "PGSUS.IS", "TAVHL.IS", "CLEBI.IS",
    
    # Retail & Food (6 stocks)
    "MGROS.IS", "SOKM.IS", "AEFES.IS", "CCOLA.IS", "ULKER.IS", "MAVI.IS",
    
    # Tech & Telecom (5 stocks)  
    "ASELS.IS", "TCELL.IS", "TTKOM.IS", "SDTTR.IS", "VBTYZ.IS",
]

GLOBAL_SYMBOLS = [
    # US Tech Giants & FAANG+
    "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "NVDA", "TSLA", "META", "NFLX", "AMD", "INTC",
    "AVGO", "QCOM", "CSCO", "ORCL", "ADBE", "CRM", "NOW", "SNOW", "PANW", "CRWD", "ZS",
    "DDOG", "NET", "MDB", "PLTR", "U", "TTD", "TWLO", "SQ", "PYPL",
    
    # Finance & Banks
    "JPM", "V", "MA", "BAC", "WFC", "C", "GS", "MS", "BLK", "AXP", "SCHW", "USB", "PNC",
    "TFC", "COF", "BK", "STT", "SPGI", "MCO", "ICE", "CME", "MSCI",
    
    # Consumer & Retail
    "WMT", "COST", "HD", "LOW", "TGT", "TJX",  "NKE", "LULU", "SBUX", "MCD", "YUM", "CMG",
    "DPZ", "ROST", "ULTA", "DG", "DLTR",
    
    # Consumer Products & Brands
    "PG", "KO", "PEP", "PM", "MO", "CL", "KMB", "EL", "CLX", "CHD",
    
   # Healthcare & Pharma
    "JNJ", "UNH", "LLY", "ABBV", "MRK", "PFE", "TMO", "ABT", "DHR", "BMY", "AMGN", "GILD",
    "VRTX", "REGN", "CI", "CVS", "HUM", "ELV", "HCA", "MOH",
    
    # Media & Entertainment
    "DIS", "CMCSA", "NFLX", "PARA", "WBD", "FOXA", "SPOT", "RBLX", "EA", "TTWO", "ATVI",
    
    # Industrial & Manufacturing  
    "BA", "CAT", "GE", "HON", "UNP", "UPS", "FDX", "LMT", "RTX", "NOC", "GD", "MMM", "EMR",
    "ITW", "ETN", "PH", "ROK", "DOV",
    
    # Energy & Oil
    "XOM", "CVX", "COP", "SLB", "EOG", "PXD", "MPC", "PSX", "VLO", "OXY", "HAL", "BKR",
    "DVN", "FANG", "HES",
    
    # Automotive
    "TSLA", "F", "GM", "TM", "HMC", "STLA", "RIVN", "LCID",
    
    # Semiconductors & Hardware
    "NVDA", "AMD", "INTC", "AVGO", "QCOM", "TXN", "ADI", "MCHP", "KLAC", "LRCX", "AMAT",
    "MU", "NXPI", "ON", "MRVL", "SWKS",
    
    # E-commerce & Payments
    "AMZN", "SHOP", "MELI", "EBAY", "ETSY", "SE", "BABA", "JD", "PDD",
    "V", "MA", "PYPL", "SQ", "COIN", "SOFI",
    
    # Telecom & Communication
    "T", "VZ", "TMUS", "CHTR",
    
    # Real Estate & REITs
    "PLD", "AMT", "CCI", "EQIX", "SPG", "PSA", "O", "WELL", "DLR", "VICI",
    
    # Utilities
    "NEE", "DUK", "SO", "D", "AEP", "EXC", "SRE", "XEL",
    
    # Other Major Players
    "BRK-B", "BRK.B", "TSM", "ASML", "NVO", "UL", "SAP", "TTE", "SHEL", "BP"
]

COMMODITIES_SYMBOLS = {
    "GC=F": "Gold",
    "SI=F": "Silver",
    "HG=F": "Copper",
    "CL=F": "Crude Oil"
}

def get_stock_data(symbol: str, period="2y"): # Need longer for 6mo calculations
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period)
        if df.empty:
            return None
        return df
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None

def calculate_rsi(series, period=14):
    delta = series.diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_indicators(df: pd.DataFrame):
    if df is None or df.empty:
        return None
    
    # Simple Moving Averages
    df['MA_5'] = df['Close'].rolling(window=5).mean()
    df['MA_10'] = df['Close'].rolling(window=10).mean()
    df['MA_20'] = df['Close'].rolling(window=20).mean()
    df['MA_50'] = df['Close'].rolling(window=50).mean()
    
    # Volatility (Annualized)
    df['Returns'] = df['Close'].pct_change()
    df['Volatility'] = df['Returns'].rolling(window=20).std() * np.sqrt(252) * 100
    
    # RSI
    df['RSI'] = calculate_rsi(df['Close'])
    
    # 6 Month High (approx 126 trading days)
    df['High_6Mo'] = df['Close'].rolling(window=126).max()
    
    df.dropna(inplace=True) # Drop initial NaNs
    return df

def predict_best_buy(buy_type, volatility, rsi):
    """Simple heuristic to predict best buy time."""
    today = datetime.now()
    
    if buy_type == "Golden Cross":
        # Trend is just starting, buy ASAP
        return "Best Entry: NOW or < 2 Days"
    
    if buy_type == "Oversold Rebound":
        # RSI is low, might dip slightly more but good value
        if rsi < 25:
            return "Extreme Value! Buy TODAY."
        else:
            return "Accumulate over next 3-5 days."
            
    if buy_type == "Trend Follow":
        # Already in trend, wait for minor dip?
        if rsi > 60:
            return "Wait for dip (Projected: 3-7 days)"
        else:
            return "Good entry point now."
            
    return "Neutral"

def analyze_stock(symbol: str, is_commodity=False, detailed=False):
    """
    Fetch stock data using multi-API router (Finnhub, Alpha Vantage, Polygon)
    Replaces Yahoo Finance with reliable alternatives
    """
    from api_router import get_router
    
    try:
        # Get API router
        router = get_router()
        
        # Fetch from alternative APIs
        api_data = router.fetch_price(symbol)
        
        if not api_data:
            print(f"No data available for {symbol}")
            return None
        
        # Build response using API data
        current_price = api_data.get('price', 0)
        change_pct = api_data.get('change_pct', 0)
        
        # Determine currency
        currency = "TRY" if symbol.endswith('.IS') else "USD"
        
        # Generate prediction based on change
        if change_pct > 5:
            prediction = f"Strong momentum with +{round(change_pct, 1)}% gain"
        elif change_pct > 2:
            prediction = f"Positive trend with +{round(change_pct, 1)}% gain"
        elif change_pct > 0:
            prediction = "Slight upward movement"
        elif change_pct < -5:
            prediction = f"Strong decline with {round(change_pct, 1)}% loss"
        elif change_pct < -2:
            prediction = f"Downward trend with {round(change_pct, 1)}% loss"
        else:
            prediction = "Stable price action"
        
        # Estimate RSI from price change (simplified)
        rsi = 50 + (change_pct * 2)  # Rough estimate
        rsi = max(0, min(100, rsi))  # Clamp between 0-100
        
        # Estimate MA_20 (simplified - slightly above/below current price)
        ma_20 = current_price * (1 - change_pct / 200)  # Approximate
        
        result = {
            "symbol": symbol,
            "name": symbol.replace('.IS', ''),
            "price": current_price,
            "change_pct": change_pct,
            "currency": currency,
            "market_cap": 0,  # Not available from quote APIs
            "volume": api_data.get('volume', 0),
            "rsi": round(rsi, 2),
            "ma_20": round(ma_20, 2),
            "prediction": prediction,
            "reason": prediction,
            "buy_signals": [],
            "is_favorable": change_pct > 0,
            "volatility": "HIGH" if abs(change_pct) > 5 else "MEDIUM" if abs(change_pct) > 2 else "LOW"
        }
        
        return result
        
    except Exception as e:
        print(f"Error analyzing {symbol}: {e}")
        return None
        
        # If we got valid dataframe from Yahoo, continue with normal analysis
        if df is None or df.empty:
            return None
        
        df = calculate_indicators(df)
        if df is None or df.empty:
            return None
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # --- Strategy Logic (Unchanged) ---
        buy_signal = False
        reasons = []
        buy_type = "Trend Follow"
        
        # Strategy 1: Golden Cross
        if prev['MA_5'] < prev['MA_10'] and latest['MA_5'] > latest['MA_10']:
            buy_signal = True
            reasons.append("Golden Cross (MA5 > MA10)")
            buy_type = "Golden Cross"
            
        elif latest['Close'] > latest['MA_20'] and latest['MA_5'] > latest['MA_10']:
           if not is_commodity:
               if latest['RSI'] < 70:
                   buy_signal = True
                   reasons.append("Strong Uptrend")
                   buy_type = "Trend Follow"
        
        # Strategy 2: Oversold
        if latest['Close'] < (latest['High_6Mo'] * 0.70):
            if latest['RSI'] < 40:
                buy_signal = True
                reasons.append("Oversold (Value Play)")
                buy_type = "Oversold Rebound"
    
        # Prediction
        prediction_text = "N/A"
        if buy_signal:
            main_reason = "Trend Follow"
            if "Golden Cross" in reasons: main_reason = "Golden Cross"
            if "Oversold" in reasons[0]: main_reason = "Oversold Rebound"
            prediction_text = predict_best_buy(main_reason, latest['Volatility'], latest['RSI'])
    
        name = COMMODITIES_SYMBOLS.get(symbol, symbol)
        
        # --- Detailed Info Fetching ---
        # Fallback Logic using 'latest' candle data if info is missing
        day_low = info.get('dayLow')
        if day_low is None: day_low = round(latest['Low'], 2)
        
        day_high = info.get('dayHigh')
        if day_high is None: day_high = round(latest['High'], 2)

        vol_lot = info.get('volume')
        if vol_lot is None: vol_lot = int(latest['Volume'])
        
        # Estimate Vol TL if currency is TRY (approx close price * volume)
        vol_tl = 0
        if "currency" in info and info['currency'] == "TRY":
             # This is a rough estimate but better than "-"
             vol_tl = int(vol_lot * latest['Close'])
        
        # VWAP Estimate (Typical Price) if missing
        vwap = info.get('regularMarketPreviousClose') # This isn't really VWAP, it was a placeholder
        # Let's calculate typical price as makeshift VWAP
        vwap_est = (latest['High'] + latest['Low'] + latest['Close']) / 3
        
        extra_info = {
                    "bid": info.get('bid', 0),
                    "ask": info.get('ask', 0),
                    "day_low": day_low,
                    "day_high": day_high,
                    "volume_lot": vol_lot,
                    "volume_tl": vol_tl,
                    "vwap": round(vwap_est, 2)
                }
    
    
        return {
            "symbol": symbol,
            "name": name,
            "price": round(latest['Close'], 2),
            "change_pct": round(latest['Returns'] * 100, 2),
            "volume": int(latest['Volume']),
            "ma_5": round(latest['MA_5'], 2),
            "ma_10": round(latest['MA_10'], 2),
            "ma_20": round(latest['MA_20'], 2),
            "volatility": round(latest['Volatility'], 2),
            "rsi": round(latest['RSI'], 2) if not pd.isna(latest['RSI']) else 0,
            "is_buyable": buy_signal,
            "reason": ", ".join(reasons) if buy_signal else "No signal",
            "prediction": prediction_text,
            **extra_info # Merge details
        }
    except Exception as e:
        print(f"Analyze stock error {symbol}: {e}")
        return None


def get_market_opportunities():
    """Scans all symbols for buy signals."""
    opportunities = []
    
    # Scan Stocks
    for symbol in BIST_SYMBOLS:
        data = analyze_stock(symbol, is_commodity=False)
        # Use is_favorable (positive change) as buy signal for simplified data
        if data and data.get('is_favorable', False) and data.get('change_pct', 0) > 0.5:
            opportunities.append(data)

    # Scan Global Stocks
    for symbol in GLOBAL_SYMBOLS:
        data = analyze_stock(symbol, is_commodity=False)
        if data and data.get('is_favorable', False) and data.get('change_pct', 0) > 0.5:
            opportunities.append(data)
            
    # Scan Commodities
    for symbol in COMMODITIES_SYMBOLS.keys():
        data = analyze_stock(symbol, is_commodity=True)
        if data and data.get('is_favorable', False) and data.get('change_pct', 0) > 0.3:
            opportunities.append(data)
    
    # Sort by change percentage (best performers first)
    opportunities.sort(key=lambda x: x.get('change_pct', 0), reverse=True)
    
    # Return top 10
    return opportunities[:10]

def get_bulk_analysis(period: str):
    """
    Analyzes all stocks and commodities for a specific period.
    Period: 'daily', 'weekly', 'monthly'
    Returns list of dicts suitable for CSV export with enhanced details.
    """
    
    # Map friendly period names to yfinance periods
    # We need enough data to calculate indicators (RSI needs 14, MA needs 50 etc)
    # irrespective of the 'period' requested for change calc.
    # However, to be fast, we'll try to fetch just enough.
    # But to get MA50, we need 50 days. To get RSI, we need ~15 days.
    # Safest is to fetch '3mo' or '6mo' to ensure we have data for indicators + period lookback.
    
    fetch_period = "6mo" 
    
    # Define lookback days for "Change" calculation
    days_back = 1
    if period == "daily":
        days_back = 1
    elif period == "weekly":
        days_back = 5 
    elif period == "monthly":
        days_back = 22 
    else:
        return []
        
    results = []
    
    all_symbols = list(BIST_SYMBOLS) + list(GLOBAL_SYMBOLS) + list(COMMODITIES_SYMBOLS.keys())
    
    for symbol in all_symbols:
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=fetch_period)
            
            if hist.empty or len(hist) < 50: # Need enough for indicators
                continue
                
            # --- 1. Calculate Indicators using existing function logic ---
            # We can reuse code or just re-impl brief ver here for speed
            # Let's perform robust calculation on the dataframe
            
            df = hist.copy()
            
            # Simple Moving Averages
            df['MA_5'] = df['Close'].rolling(window=5).mean()
            df['MA_20'] = df['Close'].rolling(window=20).mean()
            df['MA_50'] = df['Close'].rolling(window=50).mean()
            
            # RSI
            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            # Volatility
            df['Returns'] = df['Close'].pct_change()
            df['Volatility'] = df['Returns'].rolling(window=20).std() * np.sqrt(252) * 100
            
            # --- 2. Period Specific Calculations ---
            
            # Get latest
            current_idx = -1
            current_row = df.iloc[current_idx]
            current_close = current_row['Close']
            current_date = df.index[current_idx].strftime("%Y-%m-%d")
            
            # Get past (start of period)
            lookback_idx = -1 - days_back
            if abs(lookback_idx) > len(df):
                lookback_idx = 0
            
            past_row = df.iloc[lookback_idx]
            past_close = past_row['Close']
            past_date = df.index[lookback_idx].strftime("%Y-%m-%d")
            
            # Period Slice (for High/Low in range)
            # We want the max/min strictly within the period window
            period_slice = df.iloc[lookback_idx:] 
            
            period_high = period_slice['High'].max()
            period_low = period_slice['Low'].min()
            
            # Find dates for high/low (returns Index, which is date)
            period_high_date = period_slice['High'].idxmax().strftime("%Y-%m-%d")
            period_low_date = period_slice['Low'].idxmin().strftime("%Y-%m-%d")
            
            # Calculations
            change_amt = current_close - past_close
            change_pct = (change_amt / past_close) * 100
            
            # --- 3. Interpretation & Visuals ---
            
            trend_icon = "➖"
            if change_pct > 0: trend_icon = "📈 UP"
            elif change_pct < 0: trend_icon = "📉 DOWN"
            
            # Simple RSI Status
            rsi_val = current_row['RSI']
            rsi_status = "Neutral"
            if rsi_val > 70: rsi_status = "Overbought (High Risk)"
            if rsi_val < 30: rsi_status = "Oversold (Value)"
            
            name = COMMODITIES_SYMBOLS.get(symbol, symbol)
            
            results.append({
                "Symbol": symbol,
                "Name": name,
                "Report Period": period.capitalize(),
                "Analysis Date": current_date,
                "Trend": trend_icon,
                
                # Prices
                "Current Price": round(current_close, 2),
                "Start Price": round(past_close, 2),
                "Change %": round(change_pct, 2),
                "Change Amt": round(change_amt, 2),
                
                # Range Detail
                "Period High": round(period_high, 2),
                "High Date": period_high_date,
                "Period Low": round(period_low, 2),
                "Low Date": period_low_date,
                
                # Tech Indicators
                "RSI (14)": round(rsi_val, 2) if not np.isnan(rsi_val) else 0,
                "RSI Status": rsi_status,
                "Volatility %": round(current_row['Volatility'], 2) if not np.isnan(current_row['Volatility']) else 0,
                "MA(20)": round(current_row['MA_20'], 2) if not np.isnan(current_row['MA_20']) else 0,
                "Volume (Period)": int(period_slice['Volume'].sum())
            })
            
        except Exception as e:
            # print(f"Error bulk analyzing {symbol}: {e}")
            continue
            
    return results

