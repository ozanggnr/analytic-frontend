// Client-side Yahoo Finance fetching (works in browser, bypasses server blocks)

// Sample Turkish stocks (reduced list for faster loading)
const TURKISH_STOCKS = [
    "AKBNK.IS", "GARAN.IS", "HALKB.IS", "ISCTR.IS", "YKBNK.IS",
    "THYAO.IS", "TUPRS.IS", "EREGL.IS", "SAHOL.IS", "KCHOL.IS"
];

// Sample US stocks
const US_STOCKS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "JPM", "V", "WMT"
];

// Fetch stock data directly from browser (Yahoo allows this)
async function fetchStockFromBrowser(symbol) {
    try {
        // Use yfinance-like endpoint that works from browser
        const url = `https://query1.finance.yahoo.com/v8/finance/chart/${symbol}?range=1mo&interval=1d`;

        const response = await fetch(url);
        const data = await response.json();

        if (!data.chart || !data.chart.result || data.chart.result.length === 0) {
            return null;
        }

        const result = data.chart.result[0];
        const meta = result.meta;
        const quotes = result.indicators.quote[0];

        if (!quotes || !quotes.close || quotes.close.length === 0) {
            return null;
        }

        // Get latest price
        const prices = quotes.close.filter(p => p !== null);
        if (prices.length === 0) return null;

        const currentPrice = prices[prices.length - 1];
        const previousPrice = prices.length > 1 ? prices[prices.length - 2] : currentPrice;
        const changePct = ((currentPrice - previousPrice) / previousPrice) * 100;

        return {
            symbol: symbol,
            name: meta.symbol,
            price: parseFloat(currentPrice.toFixed(2)),
            change_pct: parseFloat(changePct.toFixed(2)),
            currency: meta.currency || (symbol.endsWith('.IS') ? 'TRY' : 'USD'),
            volume: quotes.volume ? quotes.volume[quotes.volume.length - 1] : 0,
            is_favorable: changePct > 0
        };
    } catch (error) {
        console.log(`Failed to fetch ${symbol}:`, error.message);
        return null;
    }
}

// Fetch all stocks with browser-based method
async function fetchAllStocksFromBrowser() {
    console.log('📊 Fetching stocks from browser...');

    const allSymbols = [...TURKISH_STOCKS, ...US_STOCKS];
    const results = [];

    // Fetch in batches to avoid overwhelming the browser
    for (let i = 0; i < allSymbols.length; i += 3) {
        const batch = allSymbols.slice(i, i + 3);
        const batchPromises = batch.map(symbol => fetchStockFromBrowser(symbol));
        const batchResults = await Promise.all(batchPromises);

        // Add successful results
        batchResults.forEach(result => {
            if (result) results.push(result);
        });

        // Small delay to avoid rate limiting
        if (i + 3 < allSymbols.length) {
            await new Promise(resolve => setTimeout(resolve, 500));
        }
    }

    console.log(`✅ Loaded ${results.length}/${allSymbols.length} stocks from browser`);
    return results;
}
