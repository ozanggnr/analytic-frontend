# Wolfee Market - Stock Analysis Platform

A full-stack stock market analysis platform focused on Turkish stocks (BIST - Borsa Istanbul) with advanced technical analysis, AI insights, and portfolio management features.

## Features

- 📊 **Real-time Stock Data**: Fetch and analyze Turkish stock market data using Yahoo Finance
- 📈 **Technical Analysis**: Advanced indicators including RSI, MACD, Bollinger Bands, and more
- 🤖 **AI Insights**: Intelligent market analysis and trading opportunities
- 💼 **Portfolio Management**: Track and export your stock portfolio
- 📉 **Interactive Charts**: Visualize stock performance with multiple timeframes (1M, 1Y, 5Y)
- 📥 **Export Functionality**: Export portfolio data to Excel

## Tech Stack

### Backend
- **Python 3.10** with FastAPI
- **yfinance** for stock data
- **pandas** and **numpy** for data analysis
- **uvicorn** as ASGI server

### Frontend
- **Vanilla JavaScript** (ES6+)
- **HTML5** and **CSS3**
- **Chart.js** or similar for visualizations
- Deployed on **Cloudflare Pages**

## Project Structure

```
wolfee/
├── backend/               # FastAPI backend
│   ├── main.py           # Main FastAPI application
│   ├── analysis.py       # Stock analysis logic
│   ├── api_router.py     # API route handlers
│   ├── requirements.txt  # Python dependencies
│   ├── Procfile          # Render deployment config
│   └── runtime.txt       # Python version
│
└── frontend/             # Static frontend
    ├── index.html        # Main application page
    ├── app.js            # Main JavaScript logic
    ├── style.css         # Styling
    ├── js/               # JavaScript modules
    │   ├── config.js     # API configuration
    │   ├── main.js       # Main app logic
    │   ├── api.js        # API calls
    │   ├── chart.js      # Chart rendering
    │   └── ui.js         # UI components
    └── wrangler.toml     # Cloudflare Pages config
```

## Local Development

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the development server:
```bash
uvicorn main:app --reload --port 8000
```

The backend will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Update `js/config.js` to use local backend:
```javascript
const API_URL = "http://127.0.0.1:8000";
```

3. Serve the frontend using any static server:
```bash
# Using Python
python -m http.server 3000

# Or using Node.js http-server
npx http-server -p 3000
```

The frontend will be available at `http://localhost:3000`

## Deployment

### Backend Deployment (Render)

1. **Push code to GitHub**

2. **Create a new Web Service on Render**:
   - Connect your GitHub repository
   - Set **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: Uses `Procfile` (auto-detected)
   - **Environment**: Python 3

3. **Configure Environment Variables** (if needed):
   - Add any API keys or secrets in Render dashboard

4. **Deploy**: Render will automatically deploy your backend

Your backend URL will be: `https://your-service-name.onrender.com`

### Frontend Deployment (Cloudflare Pages)

1. **Update API URL**: In `frontend/js/config.js`, update to your Render backend URL:
```javascript
const API_URL = "https://your-service-name.onrender.com";
```

2. **Commit and push changes**

3. **Create a new Cloudflare Pages project**:
   - Connect your GitHub repository
   - Set **Root Directory**: `frontend`
   - **Build Command**: (leave empty for static files)
   - **Build Output Directory**: `.`

4. **Deploy**: Cloudflare will automatically deploy your frontend

Your app will be available at: `https://your-project.pages.dev`

## API Endpoints

- `GET /docs` - FastAPI interactive documentation
- `GET /api/market-data/quick` - Quick market overview
- `GET /api/market-data/full` - Full market data
- `GET /analyze/{symbol}` - Analyze specific stock
- `GET /opportunities` - Get trading opportunities
- `GET /insight` - Get AI market insights
- `GET /api/chart/{symbol}/{range}` - Get chart data
- `GET /api/export/{period}` - Export portfolio data

## Environment Variables

The backend may require the following environment variables:

- `PORT` - Server port (set automatically by Render)
- Add any API keys for external services if needed

## Contributing

This is a personal project for stock market analysis. Feel free to fork and modify for your own use.

## License

Private project - All rights reserved

## Contact

For questions or issues, please contact the project owner.
