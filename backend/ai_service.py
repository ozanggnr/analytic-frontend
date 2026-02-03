import random

def get_market_insight(opportunities):
    """
    Generates a 'Daily Insight' focusing on 1-MONTH GROWTH POTENTIAL.
    Filters for stocks likely to appreciate over the next 30 days.
    """
    
    if not opportunities:
        return "Market is quiet today. No strong buy signals detected yet. Keep cash ready for dips."

    # Random "AI-like" templates
    templates = [
        "🐺 **Wolfee AI Protocol**: I've detected medium-term opportunities. Patience pays.",
        "🚀 **Market Scan Complete**: Building positions for 30-day gains.",
        "🤖 **Algorithmic Insight**: Smart accumulation phase detected."
    ]

    selected_intro = random.choice(templates)
    
    # Filter for 1-MONTH GROWTH opportunities
    # Criteria:
    # - Golden Cross (sustained uptrend momentum)
    # - RSI 30-45 (accumulation zone, not overbought)
    # - Strong trend following signals (not immediate buys)
    medium_term_growth = [
        opp for opp in opportunities 
        if (
            'Golden Cross' in opp.get('buy_signal', '') or  # Sustained momentum
            (30 <= opp.get('rsi', 100) <= 45) or  # Sweet spot: recovering but not overbought
            'Trend Follow' in opp.get('buy_signal', '') or  # Established uptrend
            'Oversold Rebound' in opp.get('buy_signal', '')  # Value recovery play
        )
    ]
    
    # Pick random from medium-term opportunities (quality + variety)
    if medium_term_growth:
        top_pick = random.choice(medium_term_growth)
    else:
        # Fallback: Any opportunity with RSI < 60 (not overbought)
        decent_picks = [opp for opp in opportunities if opp.get('rsi', 100) < 60]
        top_pick = random.choice(decent_picks) if decent_picks else random.choice(opportunities)
    
    symbol = top_pick['symbol'].replace('.IS', '')
    advice = f"Consider looking at **{symbol}**. It's showing a **{top_pick['prediction']}** signal. "
    
    if len(opportunities) > 3:
        advice += f"There are {len(opportunities)} other signals to check in the sidebar."
    
    return f"{selected_intro}\n\n{advice}"
