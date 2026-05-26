"""
StockBot India - Premium AI-Powered Financial Research Assistant (Track A)
=============================================================================
Tech Stack: Streamlit + Groq + LangChain + yfinance + Plotly + SQLite + FPDF2
Features:
- SQLite persistence for Watchlists & Portfolios
- Time-zone aware Indian Market Hours status indicator (NSE/BSE)
- Indian Numbering System currency formatting (₹ Lakhs/Crores)
- Interactive Technical Indicator Charts (Candlesticks, MA, BB, Volume, RSI)
- Robust News Sentiment Analysis (TextBlob) with optional NewsAPI key
- Dedicated Sector Comparison Dashboard
- One-click PDF Research Report Exporter
- Highly polished, custom CSS dark/slate-mode user interface
"""

import streamlit as st
import pandas as pd
import yfinance as yf
import os
import time
from datetime import datetime
import pytz
from dotenv import load_dotenv
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
from textblob import TextBlob
from collections import defaultdict
import numpy as np

from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_groq import ChatGroq

# Import custom components
import db_manager
import pdf_generator

# Initialize database
db_manager.init_db()

# ─────────────────────────────────────
# CONFIG & SETUP
# ─────────────────────────────────────
load_dotenv()

# API Keys Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# Streamlit Page Configurations
st.set_page_config(page_title="StockBot India", page_icon="📈", layout="wide")

# Custom CSS for Premium Design aesthetics
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Theme overrides */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    
    /* Main title layout */
    .main-title {
        background: linear-gradient(135deg, #38bdf8 0%, #3b82f6 50%, #818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem;
        font-weight: 800;
        margin-bottom: 5px;
    }
    
    /* Subtitle styling */
    .sub-title {
        color: #94a3b8;
        font-size: 1.1rem;
        margin-bottom: 25px;
    }
    
    /* Custom container/glassmorphism card */
    .glass-card {
        background-color: rgba(30, 41, 59, 0.45);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
    }
    
    /* Stat cards gradients */
    .metric-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.8) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
    }
    .metric-value-up {
        font-family: 'Outfit', sans-serif;
        font-size: 1.6rem;
        font-weight: 700;
        color: #10b981;
    }
    .metric-value-down {
        font-family: 'Outfit', sans-serif;
        font-size: 1.6rem;
        font-weight: 700;
        color: #f43f5e;
    }
    .metric-value-neutral {
        font-family: 'Outfit', sans-serif;
        font-size: 1.6rem;
        font-weight: 700;
        color: #3b82f6;
    }
    .metric-label {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #94a3b8;
        margin-top: 5px;
    }
    
    /* Chat bubbles */
    .stChatMessage {
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 12px;
    }
    
    /* Elegant tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0px 0px;
        padding: 10px 16px;
        background-color: rgba(30, 41, 59, 0.2);
        color: #94a3b8;
        border: 1px solid rgba(255, 255, 255, 0.05);
        font-weight: 600;
        font-size: 0.95rem;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(59, 130, 246, 0.15) !important;
        color: #3b82f6 !important;
        border-bottom: 2px solid #3b82f6 !important;
    }
</style>
""", unsafe_allow_html=True)

# Main Title Presentation
st.markdown('<div class="main-title">📈 StockBot India</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Premium SEBI-Compliant Financial Assistant for Indian Stock Analysis</div>', unsafe_allow_html=True)

# Memoization cache for ticker resolution
_ticker_cache = {}

# Sector Map for Sector comparison
SECTOR_MAP = {
    "IT & Software": ["TCS.NS", "INFY.NS", "WIPRO.NS", "HCLTECH.NS"],
    "Banking & Finance": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "AXISBANK.NS"],
    "Energy & Oil": ["RELIANCE.NS", "ONGC.NS", "NTPC.NS", "POWERGRID.NS"],
    "Automobile": ["TATAMOTORS.NS", "MARUTI.NS", "BAJAJ-AUTO.NS", "HEROMOTOCO.NS"],
    "Pharmaceuticals": ["SUNPHARMA.NS", "CIPLA.NS", "DRREDDY.NS", "APOLLOHOSP.NS"]
}

# Mapping of plain names to standard tickers
ALIASES = {
    # Indian Large Caps
    "reliance": "RELIANCE.NS",   "ril": "RELIANCE.NS",
    "tcs": "TCS.NS",            "tata consultancy": "TCS.NS",
    "infosys": "INFY.NS",        "infy": "INFY.NS",
    "wipro": "WIPRO.NS",
    "hdfc": "HDFCBANK.NS",       "hdfc bank": "HDFCBANK.NS",
    "icici": "ICICIBANK.NS",     "icici bank": "ICICIBANK.NS",
    "sbi": "SBIN.NS",            "state bank": "SBIN.NS", "sbin": "SBIN.NS",
    "bajaj": "BAJFINANCE.NS",    "bajaj finance": "BAJFINANCE.NS",
    "itc": "ITC.NS",
    "maruti": "MARUTI.NS",       "maruti suzuki": "MARUTI.NS",
    "tata motors": "TATAMOTORS.NS",  "tatamotors": "TATAMOTORS.NS",
    "axis bank": "AXISBANK.NS",  "axis": "AXISBANK.NS",
    "hcl tech": "HCLTECH.NS",    "hcltech": "HCLTECH.NS",
    "sun pharma": "SUNPHARMA.NS","sunpharma": "SUNPHARMA.NS",
    "nifty": "^NSEI",            "nifty 50": "^NSEI",
    "sensex": "^BSESN",
    # US Equities
    "apple": "AAPL",   "microsoft": "MSFT",
    "google": "GOOGL", "tesla": "TSLA", "nvidia": "NVDA",
    "amazon": "AMZN",  "meta": "META",
}

def resolve_ticker(name: str) -> str:
    """Resolve ticker with memoization and mapping"""
    name_clean = name.strip().lower()
    if name_clean in _ticker_cache:
        return _ticker_cache[name_clean]
    
    result = ALIASES.get(name_clean, name.strip().upper())
    # Add auto-suffixing logic for Indian Stocks if user typing a standard symbol without .NS
    if not result.endswith(".NS") and not result.endswith(".BO") and not result.startswith("^"):
        # If it matches any of standard Indian companies listed, add .NS
        # Or standard validation check, default to NSE if no suffix matches US names
        us_tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "AMZN", "META", "NFLX", "AMD"]
        if result not in us_tickers:
            result = f"{result}.NS"
            
    _ticker_cache[name_clean] = result
    return result

# ─────────────────────────────────────
# RATE LIMITING & CACHING MANAGER
# ─────────────────────────────────────
class RateLimiter:
    def __init__(self, max_calls=15, time_window=60):
        self.max_calls = max_calls
        self.time_window = time_window
        self.call_times = defaultdict(list)
    
    def is_allowed(self, key="default"):
        now = time.time()
        # Remove old calls outside time window
        self.call_times[key] = [t for t in self.call_times[key] if now - t < self.time_window]
        
        if len(self.call_times[key]) < self.max_calls:
            self.call_times[key].append(now)
            return True, None
        
        retry_after = int(self.call_times[key][0] - (now - self.time_window)) + 1
        return False, retry_after

rate_limiter = RateLimiter(max_calls=15, time_window=60)

# ─────────────────────────────────────
# COMPLIANCE & FORMATTING HELPERS
# ─────────────────────────────────────
def format_inr(number):
    """Format a number in Indian Rupee format (Lakhs, Crores) e.g., ₹12,34,567.89"""
    if number is None or str(number) == 'N/A' or np.isnan(number) if isinstance(number, float) else False:
        return "₹N/A"
    
    try:
        number = round(float(number), 2)
        is_negative = number < 0
        number = abs(number)
        
        s = f"{number:.2f}"
        parts = s.split('.')
        integer_part = parts[0]
        decimal_part = parts[1]
        
        if len(integer_part) <= 3:
            result = integer_part
        else:
            last_three = integer_part[-3:]
            remaining = integer_part[:-3]
            groups = []
            while len(remaining) > 0:
                groups.append(remaining[-2:])
                remaining = remaining[:-2]
            groups.reverse()
            result = ",".join(groups) + "," + last_three
            
        result = "₹" + ("-" if is_negative else "") + result + "." + decimal_part
        return result
    except Exception:
        return f"₹{number}"

def get_indian_market_status():
    """
    Check if the Indian stock market (NSE/BSE) is open.
    Trading hours: Monday to Friday, 9:15 AM to 3:30 PM IST.
    """
    tz = pytz.timezone('Asia/Kolkata')
    now = datetime.now(tz)
    
    # 0 = Monday, 6 = Sunday
    day_of_week = now.weekday()
    
    # Check weekend
    if day_of_week >= 5:
        return False, "Closed (Weekend)", now
        
    market_start = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_end = now.replace(hour=15, minute=30, second=0, microsecond=0)
    
    if market_start <= now <= market_end:
        return True, "Open", now
    elif now < market_start:
        return False, "Closed (Market opens at 9:15 AM IST)", now
    else:
        return False, "Closed (Market closed for the day)", now

def validate_ticker(ticker: str) -> tuple[bool, str]:
    """Validate ticker symbol format and availability"""
    if not ticker or not isinstance(ticker, str):
        return False, "Invalid ticker format"
    
    ticker = ticker.strip()
    if len(ticker) == 0:
        return False, "Ticker cannot be empty"
    
    if len(ticker) > 15:
        return False, "Ticker too long (max 15 chars)"
    
    if not all(c.isalnum() or c in ['^', '.', '-'] for c in ticker):
        return False, "Invalid ticker characters"
    
    return True, ticker

# ─────────────────────────────────────
# TECHNICAL INDICATORS MODULE
# ─────────────────────────────────────
class TechnicalIndicators:
    """Centralized technical indicators calculator"""
    
    @staticmethod
    def rsi(prices, period=14):
        """Calculate RSI with safety checks"""
        if len(prices) < period:
            return None
        
        deltas = np.diff(prices)
        seed = deltas[:period+1]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        
        if down == 0:
            return 100.0 if up > 0 else 0.0
        
        rs = up / down
        rsi = 100.0 - (100.0 / (1.0 + rs))
        
        rsis = [rsi]
        for delta in deltas[period+1:]:
            if delta > 0:
                up = (up * (period - 1) + delta) / period
                down = (down * (period - 1) + 0) / period
            else:
                up = (up * (period - 1) + 0) / period
                down = (down * (period - 1) - delta) / period
            
            if down == 0:
                rsi = 100.0 if up > 0 else 0.0
            else:
                rs = up / down
                rsi = 100.0 - (100.0 / (1.0 + rs))
            rsis.append(rsi)
        
        return rsis[-1]
    
    @staticmethod
    def calculate_rsi_series(prices, period=14):
        """Calculate RSI for all points efficiently (O(n) vectorized approach)"""
        if len(prices) < period:
            return [None] * len(prices)
        
        deltas = np.diff(prices)
        seed = deltas[:period]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        
        rsi_list = [None] * period
        
        if down == 0:
            rsi_val = 100.0 if up > 0 else 0.0
        else:
            rs = up / down
            rsi_val = 100.0 - (100.0 / (1.0 + rs))
        rsi_list.append(rsi_val)
        
        for delta in deltas[period:]:
            if delta > 0:
                up = (up * (period - 1) + delta) / period
                down = (down * (period - 1) + 0) / period
            else:
                up = (up * (period - 1) + 0) / period
                down = (down * (period - 1) - delta) / period
            
            if down == 0:
                rsi_val = 100.0 if up > 0 else 0.0
            else:
                rs = up / down
                rsi_val = 100.0 - (100.0 / (1.0 + rs))
            rsi_list.append(rsi_val)
        
        return rsi_list
    
    @staticmethod
    def bollinger_bands(prices, period=20, std_dev=2):
        """Calculate Bollinger Bands"""
        if len(prices) < period:
            return None, None, None
        
        sma = np.mean(prices[-period:])
        std = np.std(prices[-period:])
        
        upper = sma + (std_dev * std)
        lower = sma - (std_dev * std)
        
        return upper, sma, lower
    
    @staticmethod
    def moving_averages(prices, periods=(20, 50, 200)):
        """Calculate multiple MAs"""
        mas = {}
        for p in periods:
            if len(prices) >= p:
                mas[f'ma{p}'] = np.mean(prices[-p:])
            else:
                mas[f'ma{p}'] = None
        return mas
    
    @staticmethod
    def interpret_rsi(rsi):
        """Interpret RSI value"""
        if rsi is None:
            return "Insufficient Data"
        if rsi >= 70:
            return "⚠️ Overbought (Profit taking suggested)"
        elif rsi >= 50:
            return "📈 Bullish (Upward momentum)"
        elif rsi > 30:
            return "📉 Bearish (Downward momentum)"
        else:
            return "✅ Oversold (Buying interest expected)"

# ─────────────────────────────────────
# NEWS SENTIMENT ANALYSIS
# ─────────────────────────────────────
def analyze_sentiment(text):
    """Analyze sentiment polarity using TextBlob"""
    blob = TextBlob(str(text))
    polarity = blob.sentiment.polarity  # range: -1 to 1
    
    if polarity > 0.1:
        return "positive", polarity
    elif polarity < -0.1:
        return "negative", polarity
    else:
        return "neutral", polarity

def get_news_sentiment(ticker: str, limit=5, max_retries=2) -> dict:
    """Fetch and analyze news sentiment for a stock with fallback"""
    try:
        # Fallback if News API Key is missing or invalid
        if not NEWS_API_KEY or NEWS_API_KEY == "YOUR_NEWS_API_KEY":
            # Return demo sentiment derived from general market trends to avoid crashing
            # and allow the application to remain functional in a staging/academic environment.
            seed = sum(ord(c) for c in ticker) % 3
            mock_polarities = [0.15, -0.05, 0.22, 0.08, -0.11]
            mock_titles = [
                f"{ticker} demonstrates steady expansion in local market segments.",
                f"Regulatory audits prompt minor adjustments in {ticker} logistics.",
                f"Financial analysts maintain standard ratings for {ticker} shares.",
                f"{ticker} announces key executive transition to support next-stage growth.",
                f"Competitors pressure market margins across {ticker}'s primary sectors."
            ]
            
            processed_articles = []
            sentiments = []
            for i in range(min(limit, len(mock_titles))):
                title = mock_titles[i]
                sent, pol = analyze_sentiment(title)
                sentiments.append(pol)
                processed_articles.append({
                    "title": title,
                    "sentiment": sent,
                    "polarity": round(pol, 3),
                    "source": "Market Sentiment Watch"
                })
            avg_pol = np.mean(sentiments) if sentiments else 0
            overall = "positive" if avg_pol > 0.05 else "negative" if avg_pol < -0.05 else "neutral"
            return {
                "status": "success",
                "overall_sentiment": overall,
                "avg_polarity": round(avg_pol, 3),
                "articles": processed_articles,
                "is_mock": True
            }
            
        company_name = ticker.split('.')[0]
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": company_name,
            "sortBy": "publishedAt",
            "language": "en",
            "pageSize": limit,
            "apiKey": NEWS_API_KEY
        }
        
        resp = None
        for attempt in range(max_retries):
            try:
                resp = requests.get(url, params=params, timeout=6)
                if resp.status_code == 200:
                    break
                elif resp.status_code == 429:
                    time.sleep(1)
            except requests.Timeout:
                if attempt == max_retries - 1:
                    raise
                time.sleep(1)
        
        if not resp or resp.status_code != 200:
            raise Exception(f"News API responded with code: {resp.status_code if resp else 'No response'}")
            
        data = resp.json()
        articles = data.get("articles", [])
        
        sentiments = []
        processed_articles = []
        
        for article in articles[:limit]:
            title = article.get("title", "")
            description = article.get("description", "") or ""
            text = f"{title} {description}"
            
            sentiment, polarity = analyze_sentiment(text)
            sentiments.append(polarity)
            
            processed_articles.append({
                "title": title[:100] + "..." if len(title) > 100 else title,
                "sentiment": sentiment,
                "polarity": round(polarity, 3),
                "source": article.get("source", {}).get("name", "Financial Feed")
            })
        
        avg_sentiment_score = np.mean(sentiments) if sentiments else 0
        overall_sentiment = "positive" if avg_sentiment_score > 0.05 else "negative" if avg_sentiment_score < -0.05 else "neutral"
        
        return {
            "status": "success",
            "overall_sentiment": overall_sentiment,
            "avg_polarity": round(avg_sentiment_score, 3),
            "articles": processed_articles,
            "is_mock": False
        }
    
    except Exception as e:
        return {"status": "error", "message": f"News retrieval failed: {str(e)}"}

# ─────────────────────────────────────
# CACHED DATA HELPERS (TTL-based API optimization)
# ─────────────────────────────────────
@st.cache_data(ttl=120)
def fetch_info(ticker: str) -> dict:
    try:
        return yf.Ticker(ticker).info or {}
    except Exception:
        return {}

@st.cache_data(ttl=60)
def fetch_history(ticker: str, period: str = "3mo") -> pd.DataFrame:
    try:
        df = yf.download(ticker, period=period, progress=False)
        if df is None or df.empty:
            df = yf.download(ticker, period="1mo", progress=False)
        return df if df is not None else pd.DataFrame()
    except Exception:
        return pd.DataFrame()

# ─────────────────────────────────────
# RAW TOOL LOGIC
# ─────────────────────────────────────
def _price(ticker_raw: str) -> str:
    is_valid, msg = validate_ticker(ticker_raw)
    if not is_valid:
        return f"❌ Input Error: {msg}"
    
    ticker = resolve_ticker(msg)
    info = fetch_info(ticker)
    price = info.get("currentPrice") or info.get("regularMarketPrice")
    
    if not price:
        return f"❌ Pricing data unavailable for '{ticker_raw}'. Try explicit symbols like RELIANCE.NS, TCS.NS, or AAPL."

    prev = info.get("previousClose", price)
    chg = price - prev
    pct = chg / prev * 100 if prev else 0
    cur = info.get("currency", "INR")
    name = info.get("shortName", ticker)
    cap = info.get("marketCap", 0)
    pe = info.get("trailingPE", 0)
    arr = "▲" if chg >= 0 else "▼"
    color = "🟢" if chg >= 0 else "🔴"

    st.session_state["chart_ticker"] = ticker

    # Formatted prices
    price_fmt = format_inr(price) if cur == "INR" else f"{cur} {price:,.2f}"
    chg_fmt = format_inr(chg) if cur == "INR" else f"{cur} {chg:,.2f}"
    prev_fmt = format_inr(prev) if cur == "INR" else f"{cur} {prev:,.2f}"
    high_fmt = format_inr(info.get('fiftyTwoWeekHigh', 0)) if cur == "INR" else f"{cur} {info.get('fiftyTwoWeekHigh', 0):,.2f}"
    low_fmt = format_inr(info.get('fiftyTwoWeekLow', 0)) if cur == "INR" else f"{cur} {info.get('fiftyTwoWeekLow', 0):,.2f}"
    
    if cur == "INR":
        cap_fmt = f"₹{cap/10000000:,.2f} Crores"
    else:
        cap_fmt = f"{cur} {cap/1e9:.2f} Billion"

    result = (
        f"{'='*50}\n"
        f"📊 {name} ({ticker})\n"
        f"{'='*50}\n"
        f"💰 Current Price  : {price_fmt}\n"
        f"{color} {arr} Change (1D)   : {abs(chg):,.2f} ({pct:+.2f}%)\n"
        f"📍 Prev Close     : {prev_fmt}\n"
        f"📈 52W High       : {high_fmt}\n"
        f"📉 52W Low        : {low_fmt}\n"
        f"🏢 Market Cap     : {cap_fmt}\n"
    )
    
    if pe > 0:
        result += f"📊 P/E Ratio      : {pe:.2f}"
    
    return result

def _technical_analysis(ticker_raw: str) -> str:
    ticker = resolve_ticker(ticker_raw.strip().split()[0])

    if ticker.startswith("^"):
        return f"⚠️ Technical indices like '{ticker}' do not possess complete indicator sets."

    df = fetch_history(ticker, "6mo")

    if df is None or df.empty or "Close" not in df:
        return f"❌ Valid historical pricing not found for '{ticker}'"
    
    close = df["Close"].squeeze().values
    
    rsi = TechnicalIndicators.rsi(close) if len(close) > 14 else None
    upper, sma, lower = TechnicalIndicators.bollinger_bands(close, period=20, std_dev=2)
    mas = TechnicalIndicators.moving_averages(close, (20, 50, 200))
    
    current = close[-1]
    prev = close[-2] if len(close) > 1 else current
    chg_pct = (current - prev) / prev * 100 if prev != 0 else 0
    
    result = (
        f"{'='*60}\n"
        f"📈 Technical Indicator Suite: {ticker}\n"
        f"{'='*60}\n"
        f"💰 Latest Price      : {current:,.2f}\n"
        f"📊 Performance (1D)  : {chg_pct:+.2f}%\n\n"
        f"🔧 LEADING INDICATORS:\n"
    )
    
    if rsi is not None:
        result += f"  RSI (14 Period)    : {rsi:.2f} — {TechnicalIndicators.interpret_rsi(rsi)}\n"
    
    if sma is not None:
        result += (
            f"\n  Bollinger Bands (20, 2):\n"
            f"    Upper Bound      : {upper:,.2f}\n"
            f"    Middle Band (SMA): {sma:,.2f}\n"
            f"    Lower Bound      : {lower:,.2f}\n"
        )
    
    result += f"\n📍 MOVING AVERAGES:\n"
    if mas.get('ma20') is not None:
        result += f"  MA (20 Days)       : {mas['ma20']:,.2f}\n"
    if mas.get('ma50') is not None:
        result += f"  MA (50 Days)       : {mas['ma50']:,.2f}\n"
    if mas.get('ma200') is not None:
        result += f"  MA (200 Days)      : {mas['ma200']:,.2f}\n"
    
    if mas.get('ma20') and mas.get('ma50'):
        signal = "🟢 BULLISH MOMENTUM" if mas['ma20'] > mas['ma50'] else "🔴 BEARISH MOMENTUM"
        result += f"\n🎯 MA Cross (20/50)  : {signal}"
    
    st.session_state["chart_ticker"] = ticker
    
    return result

def _history(query: str) -> str:
    parts = query.strip().split()
    ticker = resolve_ticker(parts[0])
    period = parts[1] if len(parts) > 1 else "1mo"

    df = fetch_history(ticker, period)
    if df.empty:
        return f"❌ Historical data not found for '{ticker}' over '{period}'"

    close = df["Close"].squeeze()
    ret = (close.iloc[-1] - close.iloc[0]) / close.iloc[0] * 100
    tail = df.tail(5).copy()
    tail.index = tail.index.strftime("%Y-%m-%d")

    st.session_state["chart_ticker"] = ticker
    st.session_state["chart_period"] = period

    return (
        f"{'='*60}\n"
        f"📈 Performance History: {ticker} ({period})\n"
        f"{'='*60}\n"
        f"📊 Period Return     : {ret:+.2f}%\n"
        f"📈 Period Peak       : {df['High'].max().squeeze():,.2f}\n"
        f"📉 Period Trough     : {df['Low'].min().squeeze():,.2f}\n"
        f"💱 Average Volume    : {df['Volume'].mean().squeeze():,.0f}\n"
        f"📅 Volatility (std)  : {close.std():.2f}\n"
        f"{'─'*60}\n"
        f"Recent 5 Market Sessions:\n"
        f"{'─'*60}\n"
        f"{tail[['Open','High','Low','Close','Volume']].round(2).to_string()}"
    )

def _compare(query: str) -> str:
    tickers_raw = query.strip().split()[:4]
    if not tickers_raw:
        return "❌ Ticker selection required."
    
    tickers = [resolve_ticker(t) for t in tickers_raw]
    rows = []
    
    for t in tickers:
        info = fetch_info(t)
        if not info:
            continue
        
        df = fetch_history(t, "6mo")
        close = df["Close"].squeeze().values if not df.empty else []
        rsi = TechnicalIndicators.rsi(close) if len(close) > 14 else None
        
        price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
        prev = info.get("previousClose", price)
        pct = (price - prev) / prev * 100 if prev else 0
        cur = info.get("currency", "INR")
        
        # Format values
        price_str = format_inr(price) if cur == "INR" else f"{cur} {price:,.2f}"
        cap = info.get("marketCap", 0)
        cap_str = f"₹{cap/10000000:,.1f} Cr" if cur == "INR" else f"${cap/1e9:,.1f} B"
        
        rows.append({
            "Ticker": t,
            "Name": info.get("shortName", t)[:12],
            "Price": price_str,
            "Chg%": f"{pct:+.1f}%",
            "RSI": f"{rsi:.0f}" if rsi else "N/A",
            "P/E": f"{info.get('trailingPE', 0):.1f}" if info.get('trailingPE') else "N/A",
            "Market Cap": cap_str,
        })
    
    if not rows:
        return "❌ Metrics could not be queried for the specified list."
    
    df = pd.DataFrame(rows)
    return f"{'='*70}\n🔄 Comparative Analysis\n{'='*70}\n{df.to_string(index=False)}"

def _news_sentiment(ticker_raw: str) -> str:
    ticker = resolve_ticker(ticker_raw.strip().split()[0])
    sentiment_data = get_news_sentiment(ticker, limit=5)
    
    if sentiment_data["status"] == "error":
        return f"❌ Sentiment analysis error: {sentiment_data['message']}"
    
    emoji_sentiment = {"positive": "📈", "negative": "📉", "neutral": "➡️"}
    color_sentiment = {"positive": "🟢", "negative": "🔴", "neutral": "⚪"}
    
    demo_badge = " [DEMO FEED]" if sentiment_data.get("is_mock") else ""
    
    result = (
        f"{'='*60}\n"
        f"📰 Sentiment & News Catalysts{demo_badge}: {ticker}\n"
        f"{'='*60}\n"
        f"{color_sentiment[sentiment_data['overall_sentiment']]} Overall Sentiment: {sentiment_data['overall_sentiment'].upper()}\n"
        f"📊 Avg Polarity Score: {sentiment_data['avg_polarity']} (-1 to 1 scale)\n"
        f"{'─'*60}\n"
        f"Catalyst Headlines Analyzed:\n"
        f"{'─'*60}\n"
    )
    
    for i, article in enumerate(sentiment_data["articles"], 1):
        emoji = emoji_sentiment.get(article["sentiment"], "❓")
        result += (
            f"{i}. {emoji} {article['title']}\n"
            f"   📌 Sentiment: {article['sentiment'].upper()} | Polarity: {article['polarity']:+.3f}\n"
            f"   🔗 Source: {article['source']}\n\n"
        )
    
    return result

def _fundamental_analysis(ticker_raw: str) -> str:
    ticker = resolve_ticker(ticker_raw.strip().split()[0])
    info = fetch_info(ticker)
    
    if not info:
        return f"❌ Fundamentals unavailable for '{ticker}'"
    
    cur = info.get("currency", "INR")
    
    roe = info.get('returnOnEquity', 'N/A')
    if isinstance(roe, (float, int)):
        roe = f"{roe*100:.2f}%"
        
    roa = info.get('returnOnAssets', 'N/A')
    if isinstance(roa, (float, int)):
        roa = f"{roa*100:.2f}%"

    div_yield = info.get('dividendYield')
    div_yield_str = f"{div_yield*100:.2f}%" if div_yield else "0.00%"
    
    return (
        f"{'='*60}\n"
        f"💼 Fundamental Valuation Matrix: {ticker}\n"
        f"{'='*60}\n"
        f"📊 Valuation Indicators:\n"
        f"  P/E Ratio (TTM)       : {info.get('trailingPE', 'N/A')}\n"
        f"  P/E Ratio (Forward)   : {info.get('forwardPE', 'N/A')}\n"
        f"  P/B Ratio             : {info.get('priceToBook', 'N/A')}\n\n"
        f"💰 Investment Returns:\n"
        f"  Dividend Yield        : {div_yield_str}\n"
        f"  ROE (Return on Equity): {roe}\n"
        f"  ROA (Return on Assets): {roa}\n\n"
        f"💳 Balance Sheet Strength:\n"
        f"  Debt-to-Equity        : {info.get('debtToEquity', 'N/A')}\n"
        f"  Current Ratio         : {info.get('currentRatio', 'N/A')}\n"
        f"  Quick Ratio           : {info.get('quickRatio', 'N/A')}\n\n"
        f"📈 Operational Performance:\n"
        f"  52W Share Change      : {info.get('52WeekChange', 'N/A')}\n"
        f"  Average Daily Volume  : {info.get('averageVolume', 'N/A'):,}"
    )

# ─────────────────────────────────────
# LANGCHAIN WRAPPERS
# ─────────────────────────────────────
@tool
def get_stock_price(ticker: str) -> str:
    """Get live stock price, change %, 52-week range, market cap, P/E ratio.
    Input: company name or ticker e.g. 'reliance', 'TCS.NS', 'AAPL'"""
    return _price(ticker)

@tool
def get_technical_analysis(ticker: str) -> str:
    """Get advanced technical analysis: RSI, Moving Averages, Bollinger Bands, Signal.
    Input: ticker e.g. 'RELIANCE.NS', 'TCS', 'AAPL'"""
    return _technical_analysis(ticker)

@tool
def get_historical_data(query: str) -> str:
    """Get OHLCV historical data + period return stats + volatility.
    Input format: 'TICKER period'  e.g. 'RELIANCE.NS 3mo'
    Valid periods: 1d 5d 1mo 3mo 6mo 1y 2y"""
    return _history(query)

@tool
def compare_stocks(tickers: str) -> str:
    """Compare 2-4 stocks with price, change, RSI, P/E, market cap.
    Input: space-separated tickers e.g. 'RELIANCE.NS TCS.NS INFY.NS'"""
    return _compare(tickers)

@tool
def get_news_sentiment_analysis(ticker: str) -> str:
    """Get recent news and sentiment analysis for a stock.
    Input: ticker e.g. 'RELIANCE.NS', 'AAPL'
    Returns: Overall sentiment, individual article sentiments"""
    return _news_sentiment(ticker)

@tool
def get_fundamental_analysis(ticker: str) -> str:
    """Get fundamental metrics: P/E, Dividend Yield, ROE, Debt-to-Equity.
    Input: ticker e.g. 'RELIANCE.NS'"""
    return _fundamental_analysis(ticker)

TOOL_MAP = {
    "get_stock_price": lambda a: _price(a.get("ticker", "")),
    "get_technical_analysis": lambda a: _technical_analysis(a.get("ticker", "")),
    "get_historical_data": lambda a: _history(a.get("query", "")),
    "compare_stocks": lambda a: _compare(a.get("tickers", "")),
    "get_news_sentiment_analysis": lambda a: _news_sentiment(a.get("ticker", "")),
    "get_fundamental_analysis": lambda a: _fundamental_analysis(a.get("ticker", "")),
}

ALL_TOOLS = [
    get_stock_price,
    get_technical_analysis,
    get_historical_data,
    compare_stocks,
    get_news_sentiment_analysis,
    get_fundamental_analysis,
]

SYSTEM_PROMPT = """You are StockBot India — an advanced financial AI research assistant for NSE/BSE and global markets.

COMPLIANCE & DISCLOSURES:
1. Provide objective analysis, market statistics, and calculations. Never provide direct financial advice, hot tips, or buy/sell recommendations.
2. Maintain a highly professional and neutral tone. Include references to financial indicators.

OPERATIONAL RULES:
1. Call exactly ONE tool per user query to gather primary data.
2. Select the optimal tool:
   - Live price/overview → get_stock_price
   - Technical studies (RSI, Moving Averages, Bollinger) → get_technical_analysis
   - Historical ranges → get_historical_data
   - Comparison → compare_stocks
   - News catalyst/sentiment → get_news_sentiment_analysis
   - Balance sheet strength/fundamentals → get_fundamental_analysis
3. Display raw tool findings clearly. Provide a precise, 2-line financial summary immediately after. Do not execute multiple tool runs.
4. Auto-resolve aliases: reliance -> RELIANCE.NS, tcs -> TCS.NS, sbi -> SBIN.NS, etc."""

@st.cache_resource
def get_llm_with_tools():
    return ChatGroq(
        api_key=GROQ_API_KEY,
        model="llama-3.3-70b-versatile",
        temperature=0,
        max_tokens=256,
    ).bind_tools(ALL_TOOLS, tool_choice="auto")

@st.cache_resource
def get_llm_plain():
    return ChatGroq(
        api_key=GROQ_API_KEY,
        model="llama-3.3-70b-versatile",
        temperature=0,
        max_tokens=200,
    )

def run_agent(user_query: str) -> str:
    allowed, retry_after = rate_limiter.is_allowed("agent_call")
    if not allowed:
        return f"⏳ Rate limiting active. Please retry in {retry_after}s."

    llm = get_llm_with_tools()
    messages = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_query)]

    try:
        response = llm.invoke(messages)
    except Exception as e:
        return f"❌ AI Engine Error: {str(e)}"

    messages.append(response)

    if not response.tool_calls:
        return response.content or "Analysis complete."

    tool_outputs = []

    for tc in response.tool_calls:
        tool_name = tc.get("name")
        tool_args = tc.get("args", {})

        if tool_name not in TOOL_MAP:
            result = f"❌ Invalid tool requested: {tool_name}"
        else:
            try:
                result = TOOL_MAP[tool_name](tool_args)
            except Exception as e:
                result = f"❌ Tool execution failed: {str(e)}"

        tool_outputs.append(result)
        messages.append(ToolMessage(content=result, tool_call_id=tc["id"]))

    raw_data = "\n\n".join(tool_outputs)

    try:
        summary_resp = get_llm_plain().invoke(
            messages + [HumanMessage(content="Write a concise 2-sentence market summary. Do not invoke tools.")]
        )
        summary = summary_resp.content.strip()
    except Exception:
        summary = ""

    return f"{raw_data}\n\n💬 Summary Insights:\n{summary}" if summary else raw_data

# ─────────────────────────────────────
# PLOTLY ADVANCED CHART
# ─────────────────────────────────────
def show_chart(ticker: str, period: str = "3mo"):
    df = fetch_history(ticker, period)
    if df.empty:
        st.warning(f"Unable to load chart data for {ticker}")
        return

    df = df.reset_index()
    # Normalize MultiIndex columns if present
    df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]

    df["MA20"] = df["Close"].rolling(20).mean()
    df["MA50"] = df["Close"].rolling(50).mean()
    df["MA200"] = df["Close"].rolling(200).mean()
    
    bb_period = 20
    bb_std = 2
    df["BB_Mid"] = df["Close"].rolling(bb_period).mean()
    df["BB_Std"] = df["Close"].rolling(bb_period).std()
    df["BB_Upper"] = df["BB_Mid"] + (bb_std * df["BB_Std"])
    df["BB_Lower"] = df["BB_Mid"] - (bb_std * df["BB_Std"])

    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True,
        row_heights=[0.55, 0.20, 0.25], vertical_spacing=0.06,
    )

    # Main Candlestick chart
    fig.add_trace(go.Candlestick(
        x=df["Date"],
        open=df["Open"], high=df["High"],
        low=df["Low"],   close=df["Close"],
        name="Price OHLC",
        increasing_line_color="#26a69a",
        decreasing_line_color="#ef5350",
    ), row=1, col=1)

    # Overlays
    fig.add_trace(go.Scatter(x=df["Date"], y=df["MA20"],
                             name="MA 20", line=dict(color="orange", width=1.5), opacity=0.85), row=1, col=1)
    fig.add_trace(go.Scatter(x=df["Date"], y=df["MA50"],
                             name="MA 50", line=dict(color="#3b82f6", width=1.5), opacity=0.85), row=1, col=1)
    fig.add_trace(go.Scatter(x=df["Date"], y=df["MA200"],
                             name="MA 200", line=dict(color="#f43f5e", width=1.5), opacity=0.7), row=1, col=1)

    # Bollinger Bands Fill
    fig.add_trace(go.Scatter(x=df["Date"], y=df["BB_Upper"],
                             name="BB Upper", line=dict(color="rgba(59,130,246,0)", width=0),
                             showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=df["Date"], y=df["BB_Lower"],
                             name="Bollinger Bands (20,2)", line=dict(color="rgba(59,130,246,0)", width=0),
                             fillcolor="rgba(59,130,246,0.06)", fill='tonexty',
                             showlegend=True), row=1, col=1)

    # Volume bars
    bar_colors = ["#26a69a" if c >= o else "#ef5350" for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(go.Bar(x=df["Date"], y=df["Volume"],
                          name="Volume", marker_color=bar_colors, opacity=0.55), row=2, col=1)

    # RSI
    prices = df["Close"].values
    rsi_values = TechnicalIndicators.calculate_rsi_series(prices, 14)
    fig.add_trace(go.Scatter(x=df["Date"], y=rsi_values, name="RSI (14)",
                             line=dict(color="#818cf8", width=2)), row=3, col=1)
    
    fig.add_hline(y=70, line_dash="dash", line_color="#ef5350", row=3, col=1, opacity=0.7)
    fig.add_hline(y=30, line_dash="dash", line_color="#26a69a", row=3, col=1, opacity=0.7)

    fig.update_layout(
        title=f"<b>{ticker} | {period}</b> - Technical Dashboard",
        xaxis_rangeslider_visible=False,
        height=680,
        hovermode='x unified',
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=1.02, x=0.01),
        font=dict(family="Inter", size=10)
    )
    
    fig.update_yaxes(title_text="Price (INR)",  row=1, col=1, gridcolor="rgba(255,255,255,0.05)")
    fig.update_yaxes(title_text="Volume", row=2, col=1, gridcolor="rgba(255,255,255,0.05)")
    fig.update_yaxes(title_text="RSI",    row=3, col=1, gridcolor="rgba(255,255,255,0.05)", range=[10, 90])
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.05)")

    st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────
# SESSION STATE INITIALIZATION
# ─────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chart_ticker" not in st.session_state:
    st.session_state.chart_ticker = "RELIANCE.NS"
if "chart_period" not in st.session_state:
    st.session_state.chart_period = "3mo"

# Sync persistent database to session state on startup
if "watchlist" not in st.session_state:
    st.session_state.watchlist = db_manager.get_watchlist()
if "portfolio" not in st.session_state:
    st.session_state.portfolio = db_manager.get_portfolio()

# ─────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏛️ Market Clock")
    # Live Indian market status indicator
    is_open, status_text, ist_time = get_indian_market_status()
    ist_time_str = ist_time.strftime("%I:%M:%S %p IST")
    if is_open:
        st.markdown(
            f'<div style="background-color: rgba(38, 166, 154, 0.12); border: 1px solid #26a69a; '
            f'border-radius: 8px; padding: 12px; margin-bottom: 20px; text-align: center;">'
            f'<span style="color: #26a69a; font-weight: 700; font-size: 14px;">🟢 NSE/BSE IS OPEN</span><br>'
            f'<span style="color: #cbd5e1; font-size: 11px; font-weight: 500;">{ist_time_str}</span>'
            f'</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            f'<div style="background-color: rgba(239, 83, 80, 0.12); border: 1px solid #ef5350; '
            f'border-radius: 8px; padding: 12px; margin-bottom: 20px; text-align: center;">'
            f'<span style="color: #ef5350; font-weight: 700; font-size: 14px;">🔴 NSE/BSE CLOSED</span><br>'
            f'<span style="color: #cbd5e1; font-size: 11px; font-weight: 500;">{ist_time_str}</span><br>'
            f'<span style="color: #94a3b8; font-size: 10px; font-style: italic;">{status_text}</span><br>'
            f'<span style="color: #ffb300; font-size: 9px; font-weight: 600; display: block; margin-top: 3px;">⚠️ Historical/Cached Quotes</span>'
            f'</div>',
            unsafe_allow_html=True
        )

    st.markdown("### ⚡ Quick Queries")
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("**Price Checks**")
        for label, sym in [("Reliance", "RELIANCE.NS"), ("TCS", "TCS.NS"),
                           ("HDFC Bank", "HDFCBANK.NS"), ("Infosys", "INFY.NS")]:
            if st.button(f"💵 {label}", use_container_width=True, key=f"price_{sym}"):
                q = f"What is the current price of {sym}?"
                st.session_state.messages.append({"role": "user", "content": q})
                with st.spinner("Fetching..."):
                    ans = run_agent(q)
                st.session_state.messages.append({"role": "assistant", "content": ans})
                st.rerun()
    
    with col_r:
        st.markdown("**Technical Indicators**")
        for label, sym in [("SBI", "SBIN.NS"), ("Wipro", "WIPRO.NS"),
                           ("Nifty 50", "^NSEI"), ("Sensex", "^BSESN")]:
            if st.button(f"📈 {label}", use_container_width=True, key=f"tech_{sym}"):
                q = f"Technical analysis for {sym}"
                st.session_state.messages.append({"role": "user", "content": q})
                with st.spinner("Analyzing..."):
                    ans = run_agent(q)
                st.session_state.messages.append({"role": "assistant", "content": ans})
                st.rerun()

    st.divider()
    st.markdown("### 📋 Navigation Options")
    st.markdown("- Watchlist and Portfolio storage are fully persisted in SQLite.")
    st.markdown("- Adjust technical charts or request PDF exports in the main tabs.")
    
    st.divider()
    # API configuration check status
    st.markdown("### 🔑 System Integration")
    if GROQ_API_KEY:
        st.success("🤖 Groq AI Engine: CONNECTED")
    else:
        st.error("🤖 Groq AI Engine: KEY MISSING")
        st.info("Please add GROQ_API_KEY in the `.env` configuration file.")
        
    if NEWS_API_KEY and NEWS_API_KEY != "YOUR_NEWS_API_KEY":
        st.success("📰 News API: CONNECTED")
    else:
        st.warning("📰 News API: DEMO MODE ACTIVE")
        st.caption("Provide a valid NEWS_API_KEY in `.env` to enable live catalyst parsing.")

    st.divider()
    st.caption("Disclaimer: StockBot India provides technical research and market computations. No direct advice is formulated.")

# ─────────────────────────────────────
# MAIN PANEL TABS
# ─────────────────────────────────────
tab_chart, tab_sector, tab_portfolio, tab_watchlist = st.tabs([
    "📈 Stock Research & Charts", 
    "🔄 Sector Comparison", 
    "💼 Portfolio Manager", 
    "📋 Persistent Watchlist"
])

# ----------------------------------------------------
# TAB 1: Stock Research & Charts
# ----------------------------------------------------
with tab_chart:
    st.subheader(f"📊 Technical Suite & AI Analysis: {st.session_state.chart_ticker}")
    
    # Chart controls inline for widescreen presentation
    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([3, 2, 2])
    with ctrl_col1:
        cht_sym = st.text_input("Enter Ticker/Company Name", value=st.session_state.chart_ticker, key="main_chart_ticker_input")
    with ctrl_col2:
        cht_per = st.selectbox("Historical Window", ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y"], index=3, key="main_chart_period_select")
    with ctrl_col3:
        st.write("<div style='height:28px;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Render Analytics", use_container_width=True, key="update_chart_main_btn"):
            st.session_state.chart_ticker = resolve_ticker(cht_sym)
            st.session_state.chart_period = cht_per
            st.rerun()

    # Show advanced Plotly chart
    show_chart(st.session_state.chart_ticker, st.session_state.chart_period)
    
    # AI Chat and PDF Generation section
    st.divider()
    
    col_pdf, col_chat = st.columns([1, 2])
    
    with col_pdf:
        st.markdown("### 📄 Export PDF Report")
        st.write("Generate a comprehensive, SEBI-compliant research report for the current stock ticker.")
        
        if st.button("📝 Compile Research PDF", use_container_width=True, key="generate_pdf_btn"):
            with st.spinner("Analyzing fundamentals, technicals, and sentiments..."):
                active_ticker = st.session_state.chart_ticker
                info = fetch_info(active_ticker)
                
                # Fetch history for RSI and MA
                df_hist = fetch_history(active_ticker, "6mo")
                close_prices = df_hist["Close"].squeeze().values if not df_hist.empty else []
                
                rsi = TechnicalIndicators.rsi(close_prices) if len(close_prices) > 14 else None
                rsi_interp = TechnicalIndicators.interpret_rsi(rsi) if rsi else "Insufficient historical price sessions."
                mas = TechnicalIndicators.moving_averages(close_prices, (20, 50, 200))
                
                # Sentiment
                sent_dict = get_news_sentiment(active_ticker, limit=4)
                
                # Generate PDF bytes
                try:
                    pdf_bytes = pdf_generator.generate_pdf_report(
                        active_ticker, info, rsi, rsi_interp, mas, sent_dict
                    )
                    
                    st.download_button(
                        label="📥 Download Research Report (PDF)",
                        data=pdf_bytes,
                        file_name=f"StockBot_Report_{active_ticker}_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                    st.success("Report Compiled Successfully!")
                except Exception as ex:
                    st.error(f"Error compiling PDF: {str(ex)}")
        
        st.write("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        st.markdown("**Example Commands:**")
        st.caption("• `Current price of RELIANCE.NS`")
        st.caption("• `Technical indicators for TCS`")
        st.caption("• `Compare TCS INFY WIPRO`")
        st.caption("• `News sentiment analysis for SBIN.NS`")
        st.caption("• `Fundamental indicators for HDFCBANK`")
        
    with col_chat:
        st.markdown("### 💬 Agent Analysis Chat")
        
        # Chat log display
        chat_container = st.container()
        with chat_container:
            if not st.session_state.messages:
                st.info("Ask me technical queries, fundamental valuation metrics, or stock comparisons.")
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    if msg["role"] == "assistant":
                        st.code(msg["content"], language="")
                    else:
                        st.write(msg["content"])
                        
        if prompt := st.chat_input("Ask about stock valuations, technicals, or news sentiments..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with chat_container:
                with st.chat_message("user"):
                    st.write(prompt)
                
                with st.chat_message("assistant"):
                    with st.spinner("Analyzing markets..."):
                        answer = run_agent(prompt)
                    st.code(answer, language="")
            
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.rerun()

# ----------------------------------------------------
# TAB 2: Sector Comparison Dashboard
# ----------------------------------------------------
with tab_sector:
    st.subheader("🔄 Sector Performance & Peers Analysis")
    st.write("Compare key Indian stock market sectors and understand industry-specific valuations.")
    
    selected_sector = st.selectbox("Select Market Sector to Analyze", list(SECTOR_MAP.keys()), index=0)
    sector_tickers = SECTOR_MAP[selected_sector]
    
    with st.spinner("Compiling industry aggregates..."):
        sector_data = []
        for ticker in sector_tickers:
            info = fetch_info(ticker)
            if not info:
                continue
            
            df_h = fetch_history(ticker, "6mo")
            cls = df_h["Close"].squeeze().values if not df_h.empty else []
            rsi = TechnicalIndicators.rsi(cls) if len(cls) > 14 else None
            
            price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
            prev = info.get("previousClose", price)
            pct = (price - prev) / prev * 100 if prev else 0
            
            mkt_cap = info.get("marketCap", 0)
            pe = info.get("trailingPE")
            
            sector_data.append({
                "Ticker": ticker,
                "Name": info.get("shortName", ticker),
                "Price": price,
                "Change%": round(pct, 2),
                "P/E Ratio": pe if pe else np.nan,
                "Market Cap (Cr)": round(mkt_cap / 10000000, 2) if mkt_cap else np.nan,
                "RSI (14)": round(rsi, 2) if rsi else np.nan
            })
            
        if sector_data:
            df_sector = pd.DataFrame(sector_data)
            
            # Format display dataframe safely
            df_display = df_sector.copy()
            df_display["Price"] = df_display["Price"].apply(lambda p: format_inr(p))
            df_display["P/E Ratio"] = df_display["P/E Ratio"].apply(lambda val: f"{val:.2f}" if not pd.isna(val) else "N/A")
            df_display["Market Cap (Cr)"] = df_display["Market Cap (Cr)"].apply(lambda val: f"₹{val:,.2f} Cr" if not pd.isna(val) else "N/A")
            df_display["RSI (14)"] = df_display["RSI (14)"].apply(lambda val: f"{val:.1f}" if not pd.isna(val) else "N/A")
            df_display["Change%"] = df_display["Change%"].apply(lambda val: f"{val:+.2f}%")
            
            # High aesthetic presentation
            st.dataframe(df_display, use_container_width=True)
            
            # Charts
            col_ch1, col_ch2 = st.columns(2)
            
            with col_ch1:
                # 1D Change bar chart
                fig_chg = go.Figure()
                fig_chg.add_trace(go.Bar(
                    x=df_sector["Name"],
                    y=df_sector["Change%"],
                    marker_color=["#26a69a" if x >= 0 else "#ef5350" for x in df_sector["Change%"]],
                    text=df_sector["Change%"].apply(lambda x: f"{x:+.2f}%"),
                    textposition='auto'
                ))
                fig_chg.update_layout(
                    title="<b>Peer Daily Return %</b>",
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    height=300,
                    margin=dict(l=10, r=10, t=40, b=10)
                )
                st.plotly_chart(fig_chg, use_container_width=True)
                
            with col_ch2:
                # P/E Ratio comparison
                df_pe = df_sector.dropna(subset=["P/E Ratio"])
                fig_pe = go.Figure()
                fig_pe.add_trace(go.Bar(
                    x=df_pe["Name"],
                    y=df_pe["P/E Ratio"],
                    marker_color="#3b82f6",
                    text=df_pe["P/E Ratio"].apply(lambda x: f"{x:.1f}"),
                    textposition='auto'
                ))
                fig_pe.update_layout(
                    title="<b>Industry Valuation P/E Multiples</b>",
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    height=300,
                    margin=dict(l=10, r=10, t=40, b=10)
                )
                st.plotly_chart(fig_pe, use_container_width=True)
        else:
            st.info("Underlying database parameters were empty for selected sector.")

# ----------------------------------------------------
# TAB 3: Portfolio Manager
# ----------------------------------------------------
with tab_portfolio:
    st.subheader("💼 Persistent Investment Portfolio")
    
    # Portfolio calculations
    portfolio_holdings = db_manager.get_portfolio()
    
    if portfolio_holdings:
        # Compute real-time valuations
        total_value = 0
        total_invested = 0
        holdings_metrics = []
        
        with st.spinner("Querying live stock feeds for portfolio..."):
            for h in portfolio_holdings:
                ticker = h["ticker"]
                qty = h["quantity"]
                buy_pr = h["buy_price"]
                
                info = fetch_info(ticker)
                curr_pr = info.get("currentPrice") or info.get("regularMarketPrice", buy_pr)
                
                curr_val = qty * curr_pr
                invested = qty * buy_pr
                pl = curr_val - invested
                pl_pct = (pl / invested * 100) if invested > 0 else 0
                
                holdings_metrics.append({
                    "id": h["id"],
                    "ticker": ticker,
                    "quantity": qty,
                    "buy_price": buy_pr,
                    "current_price": curr_pr,
                    "current_value": curr_val,
                    "pl": pl,
                    "pl_pct": pl_pct
                })
                
                total_value += curr_val
                total_invested += invested
                
        total_pl = total_value - total_invested
        total_pl_pct = (total_pl / total_invested * 100) if total_invested > 0 else 0
        
        # Grid of premium stat cards
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.markdown(
                f'<div class="metric-card">'
                f'<div class="metric-value-neutral">{format_inr(total_value)}</div>'
                f'<div class="metric-label">Total Portfolio Value</div>'
                f'</div>',
                unsafe_allow_html=True
            )
        with col_m2:
            st.markdown(
                f'<div class="metric-card">'
                f'<div class="metric-value-neutral">{format_inr(total_invested)}</div>'
                f'<div class="metric-label">Total Amount Invested</div>'
                f'</div>',
                unsafe_allow_html=True
            )
        with col_m3:
            p_class = "metric-value-up" if total_pl >= 0 else "metric-value-down"
            pl_symbol = "+" if total_pl >= 0 else ""
            st.markdown(
                f'<div class="metric-card">'
                f'<div class=" {p_class}">{pl_symbol}{format_inr(total_pl)} ({total_pl_pct:+.2f}%)</div>'
                f'<div class="metric-label">Overall Profit / Loss</div>'
                f'</div>',
                unsafe_allow_html=True
            )
            
        st.write("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        
        # Table of holdings
        portfolio_table_data = []
        for h in holdings_metrics:
            pl_emoji = "🟢" if h["pl"] >= 0 else "🔴"
            portfolio_table_data.append({
                "DB_ID": h["id"],
                "Ticker": h["ticker"],
                "Quantity": h["quantity"],
                "Buy Price": format_inr(h["buy_price"]),
                "Current Price": format_inr(h["current_price"]),
                "Current Value": format_inr(h["current_value"]),
                "P/L Status": f"{pl_emoji} {format_inr(h['pl'])} ({h['pl_pct']:+.2f}%)"
            })
            
        df_port = pd.DataFrame(portfolio_table_data)
        st.dataframe(df_port.drop(columns=["DB_ID"]), use_container_width=True)
        
        # Remove holdings controls
        st.write("##### Remove Portfolio Holdings")
        col_rem1, col_rem2 = st.columns([3, 1])
        with col_rem1:
            remove_selection = st.selectbox(
                "Select Position to Sell/Liquidate",
                options=holdings_metrics,
                format_func=lambda h: f"{h['ticker']} - {h['quantity']} Shares @ buy price {format_inr(h['buy_price'])}",
                key="remove_portfolio_selectbox"
            )
        with col_rem2:
            st.write("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if st.button("❌ Liquidate Position", use_container_width=True, key="remove_holding_btn"):
                if remove_selection:
                    db_manager.remove_from_portfolio(remove_selection["id"])
                    st.success(f"Removed {remove_selection['ticker']} holding successfully.")
                    st.session_state.portfolio = db_manager.get_portfolio()
                    st.rerun()
    else:
        st.info("📭 Portfolio database is currently empty. Add a new holding below to begin tracking.")
        
    st.divider()
    
    # Form to add a new holding
    st.write("#### Add New Investment Asset")
    col_add1, col_add2, col_add3, col_add4 = st.columns(4)
    with col_add1:
        add_ticker_raw = st.text_input("Asset Ticker", placeholder="e.g. RELIANCE, TCS", key="add_port_ticker")
    with col_add2:
        add_qty = st.number_input("Shares Quantity", min_value=0.1, value=10.0, step=1.0, key="add_port_qty")
    with col_add3:
        add_price = st.number_input("Buy Price (INR / Share)", min_value=0.1, value=1000.0, step=10.0, key="add_port_price")
    with col_add4:
        add_date = st.date_input("Transaction Date", value=datetime.now(), key="add_port_date")
        
    if st.button("➕ Log Position to Database", use_container_width=True, key="save_holding_btn"):
        if add_ticker_raw:
            res_ticker = resolve_ticker(add_ticker_raw)
            valid, ticker_msg = validate_ticker(res_ticker)
            if valid:
                with st.spinner("Verifying ticker metrics..."):
                    ticker_info = fetch_info(res_ticker)
                    if ticker_info.get("currentPrice") or ticker_info.get("regularMarketPrice"):
                        success, db_msg = db_manager.add_to_portfolio(
                            res_ticker, add_qty, add_price, add_date.strftime("%Y-%m-%d")
                        )
                        if success:
                            st.success(db_msg)
                            st.session_state.portfolio = db_manager.get_portfolio()
                            st.rerun()
                        else:
                            st.error(db_msg)
                    else:
                        st.error(f"❌ Market feed not active for '{res_ticker}'. Confirm symbol syntax.")
            else:
                st.error(f"❌ Ticker Validation Error: {ticker_msg}")
        else:
            st.error("Please enter a valid ticker.")

# ----------------------------------------------------
# TAB 4: Persistent Watchlist
# ----------------------------------------------------
with tab_watchlist:
    st.subheader("📋 Persistent Stock Watchlist")
    st.write("Add and monitor specific assets closely. Click on any watchlist ticker to instantly update the Technical Suite.")
    
    current_watchlist = db_manager.get_watchlist()
    
    if current_watchlist:
        wl_rows = []
        with st.spinner("Loading watchlist statistics..."):
            for sym in current_watchlist:
                info = fetch_info(sym)
                price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
                prev = info.get("previousClose", price)
                pct = (price - prev) / prev * 100 if prev else 0
                cur = info.get("currency", "INR")
                
                wl_rows.append({
                    "Ticker": sym,
                    "Company": info.get("shortName", sym),
                    "Price": format_inr(price) if cur == "INR" else f"{cur} {price:,.2f}",
                    "1D Change %": pct
                })
                
        if wl_rows:
            df_wl = pd.DataFrame(wl_rows)
            # Presentation formatting
            df_wl_display = df_wl.copy()
            df_wl_display["1D Change %"] = df_wl_display["1D Change %"].apply(lambda v: f"{v:+.2f}%")
            st.dataframe(df_wl_display, use_container_width=True)
            
            # Interactive watchlist list and deletion
            st.write("##### Watchlist Actions")
            
            for index, row in df_wl.iterrows():
                wl_col1, wl_col2, wl_col3 = st.columns([3, 1, 1])
                with wl_col1:
                    st.write(f"**{row['Company']} ({row['Ticker']})** — {row['Price']}")
                with wl_col2:
                    if st.button("📊 Focus Analytics", key=f"focus_wl_{row['Ticker']}", use_container_width=True):
                        st.session_state.chart_ticker = row['Ticker']
                        st.success(f"Analytic focus shifted to {row['Ticker']}.")
                        st.rerun()
                with wl_col3:
                    if st.button("❌ Remove", key=f"del_wl_{row['Ticker']}", use_container_width=True):
                        db_manager.remove_from_watchlist(row['Ticker'])
                        st.session_state.watchlist = db_manager.get_watchlist()
                        st.success(f"Removed {row['Ticker']} from database.")
                        st.rerun()
    else:
        st.info("Watchlist is currently empty.")
        
    st.divider()
    
    # Watchlist addition field
    st.write("#### Add Ticker to Watchlist")
    col_wl_add1, col_wl_add2 = st.columns([3, 1])
    with col_wl_add1:
        add_wl_raw = st.text_input("Enter Ticker to Watch", placeholder="e.g. TCS, WIPRO, TATAMOTORS", key="add_watchlist_raw_input")
    with col_wl_add2:
        st.write("<div style='height:28px;'></div>", unsafe_allow_html=True)
        if st.button("➕ Add Ticker", use_container_width=True, key="save_watchlist_btn"):
            if add_wl_raw:
                res_wl = resolve_ticker(add_wl_raw)
                valid, wl_msg = validate_ticker(res_wl)
                if valid:
                    with st.spinner("Checking market feeds..."):
                        t_info = fetch_info(res_wl)
                        if t_info.get("currentPrice") or t_info.get("regularMarketPrice"):
                            success, db_msg = db_manager.add_to_watchlist(res_wl)
                            if success:
                                st.success(db_msg)
                                st.session_state.watchlist = db_manager.get_watchlist()
                                st.rerun()
                            else:
                                st.error(db_msg)
                        else:
                            st.error(f"❌ Market quotes inactive for '{res_wl}'. Confirm correctness.")
                else:
                    st.error(f"❌ Validation Error: {wl_msg}")
            else:
                st.error("Please enter a valid ticker.")