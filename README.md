# 📈 StockBot India — AI Financial Research Agent

> **An intelligent, conversational AI agent for NSE/BSE and global stock market research — powered by Groq LLaMA-3.3-70B, LangChain, Yahoo Finance, and NewsAPI.**

---

## 🌟 Features

| Feature | Description |
|---|---|
| 🤖 **AI Agent Chat** | Natural language queries powered by Groq LLaMA-3.3-70B via LangChain tool-calling |
| 💰 **Live Stock Prices** | Real-time NSE/BSE/NYSE data via Yahoo Finance (yfinance) |
| 📊 **Technical Analysis** | RSI-14, Bollinger Bands, Moving Averages (MA20/50/200), Golden/Death Cross signals |
| 📰 **News Sentiment** | TextBlob NLP sentiment analysis on live or demo news headlines |
| 💼 **Portfolio Tracker** | SQLite-backed P&L tracker with live price updates |
| 📋 **Watchlist** | Persistent stock watchlist with one-click analysis |
| 🔄 **Sector Comparison** | Peer-to-peer sector comparison across IT, Banking, Energy, Auto, Pharma |
| 📄 **PDF Export** | SEBI-compliant research report generation using FPDF2 |
| 📈 **Interactive Charts** | Plotly candlestick charts with RSI, volume, and moving average overlays |

---

## 🗂️ Project Structure

```
AIProject/
├── app.py               # Main Streamlit application (all UI + AI agent logic)
├── db_manager.py        # SQLite database layer (watchlist & portfolio)
├── pdf_generator.py     # FPDF2-based PDF research report generator
├── requirements.txt     # Python package dependencies
├── .env                 # API keys (never commit to Git!)
├── .gitignore           # Git ignore rules
├── financial_agent.db   # SQLite database (auto-created on first run)
├── test_agent.py        # Agent integration test
├── test_groq.py         # Groq API connectivity test
├── test_portfolio.py    # Portfolio manager unit test
├── test_yfinance.py     # yfinance data fetch test
└── verify_syntax.py     # Syntax verification utility
```

---

## ⚙️ Prerequisites

- **Python** 3.10 or higher
- **pip** package manager
- A **Groq Cloud** account (free tier available)
- *(Optional)* A **NewsAPI** account for live news sentiment

---

## 🚀 Quick Setup

### 1. Clone the Repository

```bash
git clone https://github.com/SatyaVenkataRamaChanduGadikoyila/Financial-Research-AI-Agent-.git
cd Financial-Research-AI-Agent-
```

### 2. Create a Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

> 💡 **Note:** After installing TextBlob, download its corpus:
> ```bash
> python -m textblob.download_corpora
> ```

### 4. Configure API Keys

Create (or edit) the `.env` file in the project root:

```env
# Required — get your free key at https://console.groq.com/
GROQ_API_KEY=gsk_your_actual_groq_api_key_here

# Optional — enables live news sentiment (demo mode used if absent)
# Get a free key at https://newsapi.org/
NEWS_API_KEY=your_newsapi_key_here
```

> ⚠️ **Security Warning:** Never commit your `.env` file to Git. It is already listed in `.gitignore`.

### 5. Run the Application

```bash
streamlit run app.py
```

The application will open automatically in your browser at **http://localhost:8501**

---

## 🔑 API Key Configuration Guide

### Groq API Key (Required)

The AI agent brain — powers natural language query understanding and market insights.

1. Visit [https://console.groq.com/](https://console.groq.com/) and sign up for a free account
2. Navigate to **API Keys** in the left sidebar
3. Click **Create API Key**, give it a name (e.g., `stockbot-india`)
4. Copy the generated key (starts with `gsk_...`)
5. Paste it into your `.env` file as `GROQ_API_KEY=gsk_...`

**Model Used:** `llama-3.3-70b-versatile` (Groq's fastest and most capable free-tier model)

**Free Tier Limits:** ~14,400 requests/day, 30 req/min

### NewsAPI Key (Optional)

Enables live financial news headlines for sentiment analysis.

1. Register at [https://newsapi.org/register](https://newsapi.org/register)
2. Copy your API key from the dashboard
3. Add to `.env`: `NEWS_API_KEY=your_key_here`

**Without this key:** The app runs in **Demo Mode** using synthetic AI-generated headlines — all other features work normally.

### Yahoo Finance (No Key Required)

Stock price data, historical OHLCV, and fundamental data are fetched for free via `yfinance`. No API key or registration is needed.

---

## 🗄️ Database Setup

The SQLite database (`financial_agent.db`) is **auto-created on first run** with a default watchlist:
- `RELIANCE.NS`, `TCS.NS`, `INFY.NS`, `HDFCBANK.NS`, `SBIN.NS`

No manual database setup is required.

---

## 💬 Example AI Queries

```
What is the current price of RELIANCE.NS?
Technical analysis for TCS
Compare TCS INFY WIPRO HCLTECH
News sentiment analysis for SBIN.NS
Fundamental metrics for HDFCBANK
History of TATAMOTORS.NS 6mo
What is the RSI for Infosys?
Show me Bollinger Bands for Wipro
Compare AAPL MSFT GOOGL
```

---

## 🌍 Supported Markets & Tickers

| Market | Suffix | Example |
|---|---|---|
| NSE India | `.NS` | `RELIANCE.NS` |
| BSE India | `.BO` | `RELIANCE.BO` |
| Nifty 50 Index | `^NSEI` | `^NSEI` |
| Sensex Index | `^BSESN` | `^BSESN` |
| NYSE/NASDAQ | (none) | `AAPL`, `TSLA` |

**Smart aliases supported:** Type `reliance`, `tcs`, `hdfc`, `sbi`, `nifty`, `apple`, `tesla`, etc. — the agent auto-resolves to the correct ticker.

---

## 📦 Dependencies

```
streamlit>=1.35.0       # Web UI framework
plotly>=5.22.0          # Interactive financial charts
yfinance>=0.2.40        # Yahoo Finance market data
pandas>=2.2.2           # Data manipulation
numpy>=1.26.4           # Numerical computing
langchain>=0.2.0        # LLM agent orchestration
langchain-core>=0.2.0   # LangChain core primitives
langchain-groq>=0.1.6   # Groq LLM integration
textblob>=0.18.0        # NLP sentiment analysis
vaderSentiment>=3.3.2   # Lexicon-based sentiment
requests>=2.32.3        # HTTP client for NewsAPI
python-dotenv>=1.0.1    # .env file loader
fpdf2>=2.7.9            # PDF report generation
pytz>=2024.1            # Timezone handling (IST)
cachetools>=5.5.0       # Caching utilities
```

---

## ⚖️ Regulatory Disclaimer

> StockBot India is an **educational and research tool only**. It does not constitute financial, investment, legal, or tax advice. Always consult a **SEBI-registered investment advisor** before making investment decisions. Past performance does not guarantee future results.

---

## 📄 License

This project is developed for academic purposes. All financial data is sourced from public APIs under their respective terms of service.
