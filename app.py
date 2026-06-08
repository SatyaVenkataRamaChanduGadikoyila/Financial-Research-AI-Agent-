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

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_groq import ChatGroq

import db_manager
import pdf_generator

load_dotenv()
db_manager.init_db()

GROQ_API_KEY  = os.getenv("GROQ_API_KEY", "")
NEWS_API_KEY  = os.getenv("NEWS_API_KEY", "")

st.set_page_config(
    page_title="StockBot India — AI Financial Research",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
h1,h2,h3,h4,h5,h6 { font-family: 'Outfit', sans-serif; font-weight:700; letter-spacing:-0.5px; }

/* ─── Header gradient ─── */
.main-header {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    border-radius: 16px;
    padding: 28px 32px 20px;
    margin-bottom: 24px;
    border: 1px solid rgba(56,189,248,0.15);
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
}
.main-title {
    background: linear-gradient(135deg, #38bdf8 0%, #3b82f6 50%, #818cf8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.6rem;
    font-weight: 800;
    margin: 0 0 6px 0;
}
.sub-title  { color:#94a3b8; font-size:1.05rem; margin:0 0 14px 0; }
.api-badges { display:flex; gap:10px; flex-wrap:wrap; margin-top:8px; }
.api-badge  {
    background: rgba(59,130,246,0.12);
    border: 1px solid rgba(59,130,246,0.3);
    color: #93c5fd;
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.3px;
}
.api-badge.green { background:rgba(16,185,129,0.12); border-color:rgba(16,185,129,0.3); color:#6ee7b7; }
.api-badge.purple{ background:rgba(139,92,246,0.12); border-color:rgba(139,92,246,0.3); color:#c4b5fd; }

/* ─── Glassmorphism cards ─── */
.glass-card {
    background: rgba(30,41,59,0.45);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px;
    padding: 22px;
    margin-bottom: 18px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.18);
    backdrop-filter: blur(12px);
}
.metric-card {
    background: linear-gradient(135deg, rgba(30,41,59,0.85) 0%, rgba(15,23,42,0.85) 100%);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 18px;
    text-align: center;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    margin-bottom: 12px;
}
.metric-card:hover { transform: translateY(-3px); box-shadow: 0 10px 30px rgba(0,0,0,0.25); }
.metric-value      { font-family:'Outfit',sans-serif; font-size:1.55rem; font-weight:700; }
.metric-value.up   { color:#10b981; }
.metric-value.down { color:#f43f5e; }
.metric-value.neutral { color:#3b82f6; }
.metric-label      { font-size:0.82rem; text-transform:uppercase; letter-spacing:0.6px; color:#94a3b8; margin-top:5px; }

/* ─── Tabs ─── */
.stTabs [data-baseweb="tab-list"] { gap:6px; }
.stTabs [data-baseweb="tab"] {
    border-radius: 8px 8px 0 0;
    padding: 10px 18px;
    background: rgba(30,41,59,0.25);
    color: #94a3b8;
    border: 1px solid rgba(255,255,255,0.05);
    font-weight: 600; font-size:0.93rem;
}
.stTabs [aria-selected="true"] {
    background: rgba(59,130,246,0.18) !important;
    color: #60a5fa !important;
    border-bottom: 2px solid #3b82f6 !important;
}

/* ─── Sidebar enhancements ─── */
section[data-testid="stSidebar"] { background: rgba(10,15,28,0.97); }

/* ─── Chat bubbles ─── */
.stChatMessage { border-radius: 10px; margin-bottom: 10px; }

/* ─── Disclaimer banner ─── */
.disclaimer-box {
    background: rgba(251,191,36,0.07);
    border-left: 4px solid #fbbf24;
    border-radius: 8px;
    padding: 12px 16px;
    margin-top: 20px;
    color: #d97706;
    font-size: 0.83rem;
}

/* ─── Scrollbar ─── */
::-webkit-scrollbar       { width:6px; }
::-webkit-scrollbar-track { background:#0f172a; }
::-webkit-scrollbar-thumb { background:#334155; border-radius:3px; }
</style>
""", unsafe_allow_html=True)


SECTOR_MAP = {
    "IT & Software":       ["TCS.NS","INFY.NS","WIPRO.NS","HCLTECH.NS"],
    "Banking & Finance":   ["HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","AXISBANK.NS"],
    "Energy & Oil":        ["RELIANCE.NS","ONGC.NS","NTPC.NS","POWERGRID.NS"],
    "Automobile":          ["TATAMOTORS.NS","MARUTI.NS","BAJAJ-AUTO.NS","HEROMOTOCO.NS"],
    "Pharmaceuticals":     ["SUNPHARMA.NS","CIPLA.NS","DRREDDY.NS","APOLLOHOSP.NS"],
}

ALIASES = {
    "reliance":"RELIANCE.NS", "ril":"RELIANCE.NS",
    "tcs":"TCS.NS", "tata consultancy":"TCS.NS",
    "infosys":"INFY.NS", "infy":"INFY.NS",
    "wipro":"WIPRO.NS",

    "hdfc":"HDFCBANK.NS", "hdfc bank":"HDFCBANK.NS",
    "icici":"ICICIBANK.NS", "icici bank":"ICICIBANK.NS",
    "sbi":"SBIN.NS", "state bank":"SBIN.NS", "sbin":"SBIN.NS",
    "bajaj":"BAJFINANCE.NS", "bajaj finance":"BAJFINANCE.NS",
    "itc":"ITC.NS",
    "maruti":"MARUTI.NS", "maruti suzuki":"MARUTI.NS",
    "tata motors":"TATAMOTORS.NS", "tatamotors":"TATAMOTORS.NS",
    "axis bank":"AXISBANK.NS", "axis":"AXISBANK.NS",
    "hcl tech":"HCLTECH.NS", "hcltech":"HCLTECH.NS",
    "sun pharma":"SUNPHARMA.NS", "sunpharma":"SUNPHARMA.NS",
    "nifty":"^NSEI", "nifty 50":"^NSEI",
    "sensex":"^BSESN",
    "apple":"AAPL", "microsoft":"MSFT",
    "google":"GOOGL", "tesla":"TSLA", "nvidia":"NVDA",
    "amazon":"AMZN", "meta":"META",
}

US_TICKERS = {"AAPL","MSFT","GOOGL","TSLA","NVDA","AMZN","META","NFLX","AMD","GOOG"}

_ticker_cache: dict = {}

def resolve_ticker(name: str) -> str:
    """Resolve plain company name → exchange ticker with caching."""
    key = name.strip().lower()
    if key in _ticker_cache:
        return _ticker_cache[key]
    result = ALIASES.get(key, name.strip().upper())
    if not any(result.endswith(s) for s in (".NS",".BO")) and not result.startswith("^") and result not in US_TICKERS:
        result = f"{result}.NS"
    _ticker_cache[key] = result
    return result



def validate_ticker(ticker: str):
    if not ticker or not isinstance(ticker, str):
        return False, "Invalid ticker format"
    ticker = ticker.strip()
    if not ticker:
        return False, "Ticker cannot be empty"
    if not all(c.isalnum() or c in ("^",".","-") for c in ticker):
        return False, "Invalid ticker characters"
    return True, ticker


class RateLimiter:
    def __init__(self, max_calls=15, time_window=60):
        self.max_calls   = max_calls
        self.time_window = time_window
        self.call_times  = defaultdict(list)

    def is_allowed(self, key="default"):
        now = time.time()
        self.call_times[key] = [t for t in self.call_times[key] if now-t < self.time_window]
        if len(self.call_times[key]) < self.max_calls:
            self.call_times[key].append(now)
            return True, None
        retry_after = int(self.call_times[key][0]-(now-self.time_window)) + 1
        return False, retry_after

rate_limiter = RateLimiter(max_calls=15, time_window=60)

def format_inr(number):
    """Format number in Indian numbering (₹ Lakhs/Crores style)."""
    if number is None:
        return "₹N/A"
    try:
        number = round(float(number), 2)
        if np.isnan(number):
            return "₹N/A"
        neg = number < 0
        number = abs(number)
        s = f"{number:.2f}"
        int_part, dec_part = s.split(".")
        if len(int_part) <= 3:
            formatted = int_part
        else:
            last3 = int_part[-3:]
            rest   = int_part[:-3]
            grps   = []
            while rest:
                grps.append(rest[-2:])
                rest = rest[:-2]
            grps.reverse()
            formatted = ",".join(grps) + "," + last3
        return f"₹{'-' if neg else ''}{formatted}.{dec_part}"
    except Exception:
        return f"₹{number}"


def get_indian_market_status():
    tz  = pytz.timezone("Asia/Kolkata")
    now = datetime.now(tz)
    if now.weekday() >= 5:
        return False, "Closed (Weekend)", now
    ms = now.replace(hour=9,  minute=15, second=0, microsecond=0)
    me = now.replace(hour=15, minute=30, second=0, microsecond=0)
    if ms <= now <= me:
        return True,  "Open", now
    elif now < ms:
        return False, "Closed (Opens at 9:15 AM IST)", now
    else:
        return False, "Closed (Session ended)", now


class TechnicalIndicators:

    @staticmethod
    def _rsi_series(prices, period=14):
        if len(prices) < period + 1:
            return [None] * len(prices)
        deltas = np.diff(prices)
        seed   = deltas[:period]
        up     = seed[seed >= 0].sum() / period
        down   = -seed[seed < 0].sum() / period
        result = [None] * period
        rs     = up / down if down != 0 else 1e9
        result.append(100. - 100. / (1. + rs))
        for d in deltas[period:]:
            up   = (up * (period-1) + max(d, 0)) / period
            down = (down * (period-1) + max(-d, 0)) / period
            rs   = up / down if down != 0 else 1e9
            result.append(100. - 100. / (1. + rs))
        return result

    @staticmethod
    def calculate_rsi_series(prices, period=14):
        return TechnicalIndicators._rsi_series(prices, period)

    @staticmethod
    def rsi(prices, period=14):
        series = TechnicalIndicators._rsi_series(prices, period)
        vals   = [v for v in series if v is not None]
        return vals[-1] if vals else None

    @staticmethod
    def bollinger_bands(prices, period=20, std_dev=2):
        if len(prices) < period:
            return None, None, None
        sma = np.mean(prices[-period:])
        std = np.std(prices[-period:])
        return sma + std_dev*std, sma, sma - std_dev*std

    @staticmethod
    def moving_averages(prices, periods=(20,50,200)):
        return {f"ma{p}": float(np.mean(prices[-p:])) if len(prices) >= p else None for p in periods}

    @staticmethod
    def interpret_rsi(rsi):
        if rsi is None:
            return "Insufficient Data"
        if rsi >= 70: return "⚠️ Overbought — Consider Profit Taking"
        if rsi >= 50: return "📈 Bullish — Upward Momentum"
        if rsi >  30: return "📉 Bearish — Downward Pressure"
        return "✅ Oversold — Potential Reversal Zone"

def analyze_sentiment(text: str):
    pol = TextBlob(str(text)).sentiment.polarity
    if pol > 0.1:  return "positive", pol
    if pol < -0.1: return "negative", pol
    return "neutral", pol


def get_news_sentiment(ticker: str, limit=5):
    """Fetch & analyse news with fallback to mock headlines."""
    try:
        if not NEWS_API_KEY or NEWS_API_KEY in ("", "YOUR_NEWS_API_KEY"):
            raise ValueError("No key — use mock")

        company = ticker.split(".")[0]
        r = requests.get(
            "https://newsapi.org/v2/everything",
            params={"q": company, "sortBy": "publishedAt",
                    "language": "en", "pageSize": limit, "apiKey": NEWS_API_KEY},
            timeout=6,
        )
        if r.status_code != 200:
            raise ValueError(f"NewsAPI {r.status_code}")
        articles = r.json().get("articles", [])
    except Exception:
        articles = None

    if not articles:
        mock_titles = [
            f"{ticker.split('.')[0]} posts steady revenue growth in Q4 results.",
            f"Analysts maintain Buy rating on {ticker.split('.')[0]} amid sectoral headwinds.",
            f"{ticker.split('.')[0]} expands operations across emerging markets.",
            f"Regulatory review puts temporary pressure on {ticker.split('.')[0]} shares.",
            f"{ticker.split('.')[0]} inks strategic partnership for digital transformation.",
        ]
        processed, scores = [], []
        for t in mock_titles[:limit]:
            s, p = analyze_sentiment(t)
            processed.append({"title": t, "sentiment": s, "polarity": round(p,3), "source": "Demo Feed"})
            scores.append(p)
        avg = float(np.mean(scores)) if scores else 0
        overall = "positive" if avg > 0.05 else "negative" if avg < -0.05 else "neutral"
        return {"status":"success","overall_sentiment":overall,"avg_polarity":round(avg,3),"articles":processed,"is_mock":True}

    processed, scores = [], []
    for a in articles[:limit]:
        text = f"{a.get('title','')} {a.get('description','')}"
        s, p = analyze_sentiment(text)
        title = a.get("title","")
        processed.append({"title": title[:110]+"…" if len(title)>110 else title,
                           "sentiment": s, "polarity": round(p,3),
                           "source": a.get("source",{}).get("name","Financial Feed")})
        scores.append(p)
    avg = float(np.mean(scores)) if scores else 0
    overall = "positive" if avg > 0.05 else "negative" if avg < -0.05 else "neutral"
    return {"status":"success","overall_sentiment":overall,"avg_polarity":round(avg,3),"articles":processed,"is_mock":False}



@st.cache_data(ttl=120)
def fetch_info(ticker: str) -> dict:
    try:
        return yf.Ticker(ticker).info or {}
    except Exception:
        return {}


@st.cache_data(ttl=60)
def fetch_history(ticker: str, period: str = "3mo") -> pd.DataFrame:
    """Fetch OHLCV history and flatten any MultiIndex columns."""
    try:
        df = yf.download(ticker, period=period, progress=False, auto_adjust=True)
        if df is None or df.empty:
            df = yf.download(ticker, period="1mo", progress=False, auto_adjust=True)
        if df is None:
            return pd.DataFrame()
        # ── FIX: flatten MultiIndex columns produced by newer yfinance versions ──
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.reset_index()
        # Rename 'Datetime' or 'index' to 'Date' uniformly
        if "Datetime" in df.columns:
            df = df.rename(columns={"Datetime": "Date"})
        if "Date" not in df.columns and df.columns[0] not in ("Date",):
            df = df.rename(columns={df.columns[0]: "Date"})
        return df
    except Exception:
        return pd.DataFrame()


def _price(ticker_raw: str) -> str:
    valid, msg = validate_ticker(ticker_raw.strip())
    if not valid:
        return f"❌ Input Error: {msg}"
    ticker = resolve_ticker(msg)
    info   = fetch_info(ticker)
    price  = info.get("currentPrice") or info.get("regularMarketPrice")
    if not price:
        return f"❌ No price data for '{ticker}'. Try symbols like RELIANCE.NS, TCS.NS, or AAPL."
    prev  = info.get("previousClose", price)
    chg   = price - prev
    pct   = chg / prev * 100 if prev else 0
    cur   = info.get("currency", "INR")
    name  = info.get("shortName", ticker)
    cap   = info.get("marketCap", 0) or 0
    pe    = info.get("trailingPE", 0) or 0
    arrow = "▲" if chg >= 0 else "▼"
    dot   = "🟢" if chg >= 0 else "🔴"
    pfmt  = format_inr(price) if cur=="INR" else f"{cur} {price:,.2f}"
    cfmt  = format_inr(abs(chg)) if cur=="INR" else f"{cur} {abs(chg):,.2f}"
    pvfmt = format_inr(prev) if cur=="INR" else f"{cur} {prev:,.2f}"
    hi52  = format_inr(info.get("fiftyTwoWeekHigh",0)) if cur=="INR" else f"{cur} {info.get('fiftyTwoWeekHigh',0):,.2f}"
    lo52  = format_inr(info.get("fiftyTwoWeekLow",0)) if cur=="INR" else f"{cur} {info.get('fiftyTwoWeekLow',0):,.2f}"
    capfmt= f"₹{cap/10000000:,.2f} Cr" if cur=="INR" else f"{cur} {cap/1e9:.2f}B"
    st.session_state["chart_ticker"] = ticker
    result = (
        f"{'='*52}\n📊 {name} ({ticker})\n{'='*52}\n"
        f"💰 Current Price   : {pfmt}\n"
        f"{dot} {arrow} Change (1D)  : {cfmt} ({pct:+.2f}%)\n"
        f"📍 Prev Close      : {pvfmt}\n"
        f"📈 52W High        : {hi52}\n"
        f"📉 52W Low         : {lo52}\n"
        f"🏢 Market Cap      : {capfmt}\n"
    )
    if pe > 0:
        result += f"📊 P/E Ratio       : {pe:.2f}"
    return result


def _technical_analysis(ticker_raw: str) -> str:
    ticker = resolve_ticker(ticker_raw.strip().split()[0])
    df     = fetch_history(ticker, "6mo")
    if df.empty or "Close" not in df.columns:
        return f"❌ No historical data for '{ticker}'"
    close  = df["Close"].values.astype(float)
    rsi    = TechnicalIndicators.rsi(close)
    up, sma, lo = TechnicalIndicators.bollinger_bands(close)
    mas    = TechnicalIndicators.moving_averages(close, (20,50,200))
    curr   = close[-1]
    prev   = close[-2] if len(close) > 1 else curr
    chgpct = (curr - prev) / prev * 100 if prev else 0
    st.session_state["chart_ticker"] = ticker
    result = (
        f"{'='*60}\n📈 Technical Suite: {ticker}\n{'='*60}\n"
        f"💰 Latest Price      : {curr:,.2f}\n"
        f"📊 Daily Performance : {chgpct:+.2f}%\n\n"
        f"🔧 LEADING INDICATORS:\n"
    )
    if rsi is not None:
        result += f"  RSI (14)          : {rsi:.2f}  →  {TechnicalIndicators.interpret_rsi(rsi)}\n"
    if sma is not None:
        result += (
            f"\n  Bollinger Bands (20,2):\n"
            f"    Upper Band       : {up:,.2f}\n"
            f"    Middle (SMA-20)  : {sma:,.2f}\n"
            f"    Lower Band       : {lo:,.2f}\n"
        )
    result += "\n📍 MOVING AVERAGES:\n"
    for k, lbl in [("ma20","MA-20"),("ma50","MA-50"),("ma200","MA-200")]:
        if mas.get(k):
            result += f"  {lbl:<18}: {mas[k]:,.2f}\n"
    if mas.get("ma20") and mas.get("ma50"):
        sig = "🟢 BULLISH CROSSOVER" if mas["ma20"] > mas["ma50"] else "🔴 BEARISH CROSSOVER"
        result += f"\n🎯 Golden/Death Cross : {sig}"
    return result


def _history(query: str) -> str:
    parts  = query.strip().split()
    ticker = resolve_ticker(parts[0])
    period = parts[1] if len(parts) > 1 else "1mo"
    df     = fetch_history(ticker, period)
    if df.empty:
        return f"❌ Historical data unavailable for '{ticker}' — period '{period}'"
    close  = df["Close"]
    ret    = (close.iloc[-1] - close.iloc[0]) / close.iloc[0] * 100
    st.session_state["chart_ticker"] = ticker
    st.session_state["chart_period"]  = period
    tail   = df.tail(5).copy()
    if "Date" in tail.columns:
        tail["Date"] = pd.to_datetime(tail["Date"]).dt.strftime("%Y-%m-%d")
        tail = tail.set_index("Date")
    return (
        f"{'='*60}\n📈 History: {ticker} ({period})\n{'='*60}\n"
        f"📊 Period Return    : {ret:+.2f}%\n"
        f"📈 Period High      : {df['High'].max():,.2f}\n"
        f"📉 Period Low       : {df['Low'].min():,.2f}\n"
        f"💱 Avg Daily Volume : {df['Volume'].mean():,.0f}\n"
        f"📅 Volatility (σ)   : {close.std():.2f}\n"
        f"{'─'*60}\nRecent 5 Sessions:\n{'─'*60}\n"
        f"{tail[['Open','High','Low','Close','Volume']].round(2).to_string()}"
    )


def _compare(query: str) -> str:
    tickers = [resolve_ticker(t) for t in query.strip().split()[:4]]
    rows = []
    for t in tickers:
        info = fetch_info(t)
        if not info:
            continue
        df    = fetch_history(t, "6mo")
        close = df["Close"].values.astype(float) if not df.empty else []
        rsi   = TechnicalIndicators.rsi(close) if len(close) > 14 else None
        price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
        prev  = info.get("previousClose", price)
        pct   = (price-prev)/prev*100 if prev else 0
        cur   = info.get("currency","INR")
        cap   = info.get("marketCap",0) or 0
        rows.append({
            "Ticker": t,
            "Name"  : (info.get("shortName", t) or t)[:14],
            "Price" : format_inr(price) if cur=="INR" else f"{cur} {price:,.2f}",
            "Chg%"  : f"{pct:+.1f}%",
            "RSI"   : f"{rsi:.0f}" if rsi else "N/A",
            "P/E"   : f"{info.get('trailingPE',0):.1f}" if info.get("trailingPE") else "N/A",
            "Mkt Cap": f"₹{cap/10000000:,.1f}Cr" if cur=="INR" else f"${cap/1e9:,.1f}B",
        })
    if not rows:
        return "❌ Could not fetch data for given tickers."
    return f"{'='*70}\n🔄 Comparative Analysis\n{'='*70}\n{pd.DataFrame(rows).to_string(index=False)}"


def _news_sentiment(ticker_raw: str) -> str:
    ticker = resolve_ticker(ticker_raw.strip().split()[0])
    data   = get_news_sentiment(ticker)
    if data["status"] == "error":
        return f"❌ Sentiment error: {data['message']}"
    emo = {"positive":"📈","negative":"📉","neutral":"➡️"}
    col = {"positive":"🟢","negative":"🔴","neutral":"⚪"}
    badge = " [DEMO FEED]" if data.get("is_mock") else ""
    r = (
        f"{'='*60}\n📰 Sentiment{badge}: {ticker}\n{'='*60}\n"
        f"{col[data['overall_sentiment']]} Overall: {data['overall_sentiment'].upper()}\n"
        f"📊 Avg Polarity : {data['avg_polarity']:+.3f}  (-1 bearish → +1 bullish)\n"
        f"{'─'*60}\n"
    )
    for i, a in enumerate(data["articles"], 1):
        r += (
            f"{i}. {emo.get(a['sentiment'],'❓')} {a['title']}\n"
            f"   Sentiment: {a['sentiment'].upper()} | Polarity: {a['polarity']:+.3f} | {a['source']}\n\n"
        )
    return r


def _fundamental_analysis(ticker_raw: str) -> str:
    ticker = resolve_ticker(ticker_raw.strip().split()[0])
    info   = fetch_info(ticker)
    if not info:
        return f"❌ Fundamentals unavailable for '{ticker}'"
    cur = info.get("currency","INR")
    roe = info.get("returnOnEquity","N/A")
    if isinstance(roe,(float,int)): roe = f"{roe*100:.2f}%"
    roa = info.get("returnOnAssets","N/A")
    if isinstance(roa,(float,int)): roa = f"{roa*100:.2f}%"
    dy  = info.get("dividendYield")
    dys = f"{dy*100:.2f}%" if dy else "0.00%"
    return (
        f"{'='*60}\n💼 Fundamental Matrix: {ticker}\n{'='*60}\n"
        f"📊 Valuation:\n"
        f"  P/E (TTM)        : {info.get('trailingPE','N/A')}\n"
        f"  P/E (Forward)    : {info.get('forwardPE','N/A')}\n"
        f"  Price/Book       : {info.get('priceToBook','N/A')}\n\n"
        f"💰 Returns:\n"
        f"  Dividend Yield   : {dys}\n"
        f"  ROE              : {roe}\n"
        f"  ROA              : {roa}\n\n"
        f"💳 Balance Sheet:\n"
        f"  Debt/Equity      : {info.get('debtToEquity','N/A')}\n"
        f"  Current Ratio    : {info.get('currentRatio','N/A')}\n"
        f"  Quick Ratio      : {info.get('quickRatio','N/A')}\n\n"
        f"📈 Operations:\n"
        f"  Avg Daily Volume : {info.get('averageVolume',0):,}\n"
        f"  52W Price Change : {info.get('52WeekChange','N/A')}"
    )


@tool
def get_stock_price(ticker: str) -> str:
    """Get live stock price, daily change, 52W range, market cap and P/E.
    Input: company name or ticker symbol e.g. 'reliance', 'TCS.NS', 'AAPL'"""
    return _price(ticker)

@tool
def get_technical_analysis(ticker: str) -> str:
    """Get RSI, Moving Averages (20/50/200), Bollinger Bands and cross signals.
    Input: ticker e.g. 'RELIANCE.NS', 'TCS', 'INFY'"""
    return _technical_analysis(ticker)

@tool
def get_historical_data(query: str) -> str:
    """Retrieve OHLCV history, period return, volatility.
    Input: 'TICKER period'  e.g. 'TCS.NS 3mo'  (periods: 1d 5d 1mo 3mo 6mo 1y 2y)"""
    return _history(query)

@tool
def compare_stocks(tickers: str) -> str:
    """Compare 2-4 stocks: price, change, RSI, P/E, market cap.
    Input: space-separated tickers e.g. 'RELIANCE.NS TCS.NS INFY.NS'"""
    return _compare(tickers)

@tool
def get_news_sentiment_analysis(ticker: str) -> str:
    """Get recent news and TextBlob sentiment analysis for a stock.
    Input: ticker e.g. 'RELIANCE.NS', 'AAPL'"""
    return _news_sentiment(ticker)

@tool
def get_fundamental_analysis(ticker: str) -> str:
    """Get P/E, Dividend Yield, ROE, Debt-to-Equity and balance sheet metrics.
    Input: ticker e.g. 'RELIANCE.NS'"""
    return _fundamental_analysis(ticker)

ALL_TOOLS = [
    get_stock_price, get_technical_analysis, get_historical_data,
    compare_stocks, get_news_sentiment_analysis, get_fundamental_analysis,
]

TOOL_MAP = {
    "get_stock_price":            lambda a: _price(a.get("ticker","")),
    "get_technical_analysis":     lambda a: _technical_analysis(a.get("ticker","")),
    "get_historical_data":        lambda a: _history(a.get("query","")),
    "compare_stocks":             lambda a: _compare(a.get("tickers","")),
    "get_news_sentiment_analysis":lambda a: _news_sentiment(a.get("ticker","")),
    "get_fundamental_analysis":   lambda a: _fundamental_analysis(a.get("ticker","")),
}

SYSTEM_PROMPT = """You are StockBot India — a professional financial AI assistant for NSE, BSE and global markets.

IMPORTANT: Classify the user query into ONE of these categories:

1. EDUCATIONAL/CONCEPTUAL QUERY (e.g., "What is NSE?", "Explain P/E ratio", "What does RSI mean?")
   → RESPOND DIRECTLY with clear, beginner-friendly explanation
   → DO NOT call any tools
   → DO NOT fetch stock data
   → Just provide educational information

2. DATA REQUEST QUERY (e.g., "Price of RELIANCE", "Technical analysis of TCS", "Compare AAPL and MSFT")
   → Call EXACTLY ONE appropriate tool
   → After getting results, provide a 2-sentence analytical summary

RULES:
1. If unsure, ask yourself: "Is the user asking FOR A CONCEPT/DEFINITION?" → No tools
2. If unsure, ask yourself: "Is the user asking FOR STOCK DATA/ANALYSIS?" → Call one tool
3. Never give direct buy/sell advice. Provide objective data and indicators.
4. Auto-resolve: reliance→RELIANCE.NS, tcs→TCS.NS, sbi→SBIN.NS, hdfc→HDFCBANK.NS.
5. Always respond in clear, structured format.
6. NEVER call tools for educational queries - just answer directly."""


@st.cache_resource
def _build_llm():
    return ChatGroq(api_key=GROQ_API_KEY, model="llama-3.3-70b-versatile",
                    temperature=0, max_tokens=512).bind_tools(ALL_TOOLS, tool_choice="auto")

@st.cache_resource
def _build_llm_plain():
    return ChatGroq(api_key=GROQ_API_KEY, model="llama-3.3-70b-versatile",
                    temperature=0, max_tokens=256)


def run_agent(user_query: str) -> str:
    """Run the Groq LangChain agent — FIXED tool-call handling."""
    allowed, retry_after = rate_limiter.is_allowed("agent")
    if not allowed:
        return f"⏳ Rate limit active. Retry in {retry_after}s."
    if not GROQ_API_KEY:
        return "❌ GROQ_API_KEY not set. Please add it to your .env file."

    messages = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_query)]
    try:
        llm      = _build_llm()
        response = llm.invoke(messages)
    except Exception as e:
        # Graceful fallback: run tool locally without LLM
        return _fallback_direct(user_query)

    messages.append(response)
    tool_outputs = []

    # If agent decides NO tools are needed (educational query), return direct answer
    if not response.tool_calls:
        return response.content or "Analysis complete."

    # Process tool calls if any
    for tc in response.tool_calls:
        name = tc.get("name","")
        args = tc.get("args", {})
        if name in TOOL_MAP:
            try:
                result = TOOL_MAP[name](args)
            except Exception as e2:
                result = f"❌ Tool error: {e2}"
        else:
            result = f"❌ Unknown tool: {name}"
        tool_outputs.append(result)
        messages.append(ToolMessage(content=result, tool_call_id=tc["id"]))

    raw = "\n\n".join(tool_outputs) if tool_outputs else (response.content or "")

    if tool_outputs:
        try:
            summary_resp = _build_llm_plain().invoke(
                messages + [HumanMessage(content="Write a concise 2-sentence market insight summary. Do not call any tools.")]
            )
            summary = summary_resp.content.strip()
            if summary:
                raw += f"\n\n💬 Summary:\n{summary}"
        except Exception:
            pass

    return raw if raw else "Analysis complete."


def _fallback_direct(query: str) -> str:
    """Fallback: parse intent directly without LLM if Groq fails."""
    q = query.lower()
    parts = query.strip().split()
    candidates = [resolve_ticker(p) for p in parts if len(p) >= 2]

    if any(w in q for w in ("price","cost","worth","trading at","current")):
        t = candidates[0] if candidates else "RELIANCE.NS"
        return _price(t)
    if any(w in q for w in ("technical","rsi","bollinger","moving average","ma")):
        t = candidates[0] if candidates else "RELIANCE.NS"
        return _technical_analysis(t)
    if any(w in q for w in ("news","sentiment","headlines")):
        t = candidates[0] if candidates else "RELIANCE.NS"
        return _news_sentiment(t)
    if "compare" in q or "vs" in q:
        tickers = " ".join(candidates[:4]) if candidates else "RELIANCE.NS TCS.NS"
        return _compare(tickers)
    if any(w in q for w in ("fundamental","pe ratio","balance sheet","roe","debt")):
        t = candidates[0] if candidates else "RELIANCE.NS"
        return _fundamental_analysis(t)
    t = candidates[0] if candidates else "RELIANCE.NS"
    return _price(t)


def show_chart(ticker: str, period: str = "3mo"):
    df = fetch_history(ticker, period)
    if df.empty:
        st.warning(f"⚠️ No chart data available for **{ticker}** in period **{period}**. "
                   "The market may be closed or the symbol may be invalid.")
        return

    df["MA20"]  = df["Close"].rolling(20).mean()
    df["MA50"]  = df["Close"].rolling(50).mean()
    df["MA200"] = df["Close"].rolling(200).mean()
    df["BB_Mid"] = df["Close"].rolling(20).mean()
    df["BB_Std"] = df["Close"].rolling(20).std()
    df["BB_Up"]  = df["BB_Mid"] + 2 * df["BB_Std"]
    df["BB_Lo"]  = df["BB_Mid"] - 2 * df["BB_Std"]

    rsi_vals = TechnicalIndicators.calculate_rsi_series(df["Close"].values.astype(float))
    df["RSI"] = rsi_vals + [None] * (len(df) - len(rsi_vals)) if len(rsi_vals) < len(df) else rsi_vals[:len(df)]

    date_col = df["Date"] if "Date" in df.columns else df.index

    fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True,
        row_heights=[0.55, 0.20, 0.25],
        vertical_spacing=0.05,
    )

    fig.add_trace(go.Candlestick(
        x=date_col, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"], name="Price OHLC",
        increasing_line_color="#26a69a", decreasing_line_color="#ef5350",
        increasing_fillcolor="#26a69a", decreasing_fillcolor="#ef5350",
    ), row=1, col=1)

    for ma, color, name in [("MA20","#fb923c","MA 20"), ("MA50","#3b82f6","MA 50"), ("MA200","#f43f5e","MA 200")]:
        fig.add_trace(go.Scatter(x=date_col, y=df[ma], name=name,
                                 line=dict(color=color, width=1.5), opacity=0.9), row=1, col=1)

    fig.add_trace(go.Scatter(x=date_col, y=df["BB_Up"], name="BB Upper",
                             line=dict(color="rgba(139,92,246,0)", width=0), showlegend=False), row=1, col=1)
    fig.add_trace(go.Scatter(x=date_col, y=df["BB_Lo"], name="Bollinger Bands",
                             line=dict(color="rgba(139,92,246,0)", width=0),
                             fill="tonexty", fillcolor="rgba(139,92,246,0.07)"), row=1, col=1)

    bar_colors = ["#26a69a" if c >= o else "#ef5350"
                  for c, o in zip(df["Close"].fillna(0), df["Open"].fillna(0))]
    fig.add_trace(go.Bar(x=date_col, y=df["Volume"], name="Volume",
                         marker_color=bar_colors, opacity=0.55), row=2, col=1)

    fig.add_trace(go.Scatter(x=date_col, y=df["RSI"], name="RSI (14)",
                             line=dict(color="#818cf8", width=2)), row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="#ef5350", opacity=0.6, row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="#26a69a", opacity=0.6, row=3, col=1)

    fig.update_layout(
        title=dict(text=f"<b>{ticker}</b> | {period} — Technical Dashboard",
                   font=dict(size=15, color="#e2e8f0")),
        xaxis_rangeslider_visible=False,
        height=700,
        hovermode="x unified",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=1.03, x=0, font=dict(size=10)),
        font=dict(family="Inter", size=10, color="#94a3b8"),
        margin=dict(l=0, r=0, t=50, b=0),
    )
    fig.update_yaxes(title_text="Price (INR)", row=1, col=1, gridcolor="rgba(255,255,255,0.04)")
    fig.update_yaxes(title_text="Volume",      row=2, col=1, gridcolor="rgba(255,255,255,0.04)")
    fig.update_yaxes(title_text="RSI",         row=3, col=1, gridcolor="rgba(255,255,255,0.04)", range=[0,100])
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.04)")

    st.plotly_chart(fig, use_container_width=True)


for k, v in [("messages",[]), ("chart_ticker","RELIANCE.NS"),
              ("chart_period","3mo"), ("active_tab","chart")]:
    if k not in st.session_state:
        st.session_state[k] = v
if "watchlist" not in st.session_state:
    st.session_state.watchlist = db_manager.get_watchlist()
if "portfolio" not in st.session_state:
    st.session_state.portfolio = db_manager.get_portfolio()


st.markdown("""
<div class="main-header">
  <div class="main-title">📈 StockBot India</div>

</div>
""", unsafe_allow_html=True)

with st.sidebar:
    # Market clock
    is_open, status_text, ist_now = get_indian_market_status()
    ist_str = ist_now.strftime("%I:%M:%S %p IST")
    if is_open:
        st.markdown(f"""<div style="background:rgba(16,185,129,0.1);border:1px solid #10b981;
            border-radius:10px;padding:12px;text-align:center;margin-bottom:18px">
            <span style="color:#10b981;font-weight:700;font-size:14px">🟢 NSE/BSE OPEN</span><br>
            <span style="color:#cbd5e1;font-size:11px">{ist_str}</span></div>""",
            unsafe_allow_html=True)
    else:
        st.markdown(f"""<div style="background:rgba(239,83,80,0.1);border:1px solid #ef5350;
            border-radius:10px;padding:12px;text-align:center;margin-bottom:18px">
            <span style="color:#ef5350;font-weight:700;font-size:14px">🔴 NSE/BSE CLOSED</span><br>
            <span style="color:#cbd5e1;font-size:11px">{ist_str}</span><br>
            <span style="color:#94a3b8;font-size:10px;font-style:italic">{status_text}</span><br>
            <span style="color:#fbbf24;font-size:9px;font-weight:600">⚠️ Showing cached / historical data</span></div>""",
            unsafe_allow_html=True)

    st.markdown("### ⚡ Quick Analysis")
    col_l, col_r = st.columns(2)
    with col_l:
        st.caption("**Price Checks**")
        for lbl, sym in [("Reliance","RELIANCE.NS"),("TCS","TCS.NS"),
                          ("HDFC Bank","HDFCBANK.NS"),("Infosys","INFY.NS")]:
            if st.button(f"💰 {lbl}", use_container_width=True, key=f"sb_price_{sym}"):
                q = f"What is the current price of {sym}?"
                st.session_state.messages.append({"role":"user","content":q})
                with st.spinner("Fetching…"):
                    ans = run_agent(q)
                st.session_state.messages.append({"role":"assistant","content":ans})
                st.rerun()
    with col_r:
        st.caption("**Technical**")
        for lbl, sym in [("SBI","SBIN.NS"),("Wipro","WIPRO.NS"),
                          ("Nifty 50","^NSEI"),("Sensex","^BSESN")]:
            if st.button(f"📈 {lbl}", use_container_width=True, key=f"sb_tech_{sym}"):
                q = f"Technical analysis for {sym}"
                st.session_state.messages.append({"role":"user","content":q})
                with st.spinner("Analyzing…"):
                    ans = run_agent(q)
                st.session_state.messages.append({"role":"assistant","content":ans})
                st.rerun()

    st.divider()
    st.markdown("### 📊 Chart Controls")
    sb_ticker = st.text_input("Ticker", value=st.session_state.chart_ticker, key="sb_chart_ticker")
    sb_period = st.selectbox("Period", ["1d","5d","1mo","3mo","6mo","1y","2y"],
                              index=3, key="sb_chart_period")
    if st.button("🔄 Update Chart", use_container_width=True, key="sb_update_chart"):
        st.session_state.chart_ticker = resolve_ticker(sb_ticker)
        st.session_state.chart_period  = sb_period
        st.rerun()

    st.divider()
    st.markdown("### 🔑 API Status")
    st.success("✅ Yahoo Finance — always free")
    if GROQ_API_KEY:
        st.success("🤖 Groq AI — CONNECTED")
    else:
        st.error("🤖 Groq AI — KEY MISSING")
        st.caption("Add GROQ_API_KEY to `.env`")
    if NEWS_API_KEY and NEWS_API_KEY not in ("","YOUR_NEWS_API_KEY"):
        st.success("📰 NewsAPI — CONNECTED")
    else:
        st.warning("📰 NewsAPI — DEMO MODE")
        st.caption("Add NEWS_API_KEY to `.env` for live news")

    st.divider()
    st.caption("⚖️ **Disclaimer:** StockBot India provides technical research only. Not SEBI-registered investment advice. Always consult a certified financial advisor before investing.")


tab_chart, tab_sector, tab_portfolio, tab_watchlist = st.tabs([
    "📈 Stock Research & Charts",
    "🔄 Sector Comparison",
    "💼 Portfolio Manager",
    "📋 Persistent Watchlist",
])

with tab_chart:
    st.subheader(f"📊 Technical Suite: {st.session_state.chart_ticker}")

    c1, c2, c3 = st.columns([3, 2, 2])
    with c1:
        inp_ticker = st.text_input("Enter Ticker / Company Name",
                                   value=st.session_state.chart_ticker,
                                   key="tab_chart_ticker")
    with c2:
        inp_period = st.selectbox("Historical Window",
                                  ["1d","5d","1mo","3mo","6mo","1y","2y"],
                                  index=3, key="tab_chart_period")
    with c3:
        st.write("")
        st.write("")
        if st.button("🔄 Render Chart", use_container_width=True, key="tab_render_btn"):
            st.session_state.chart_ticker = resolve_ticker(inp_ticker)
            st.session_state.chart_period  = inp_period
            st.rerun()

    show_chart(st.session_state.chart_ticker, st.session_state.chart_period)

    st.divider()

    col_pdf, col_tip = st.columns([1, 2])
    with col_pdf:
        st.markdown("#### 📄 Export PDF Report")
        st.caption("Generate a SEBI-compliant research report for the current symbol.")
        if st.button("📝 Compile Research PDF", use_container_width=True, key="tab_pdf_btn"):
            with st.spinner("Compiling report…"):
                active = st.session_state.chart_ticker
                info   = fetch_info(active)
                df_h   = fetch_history(active, "6mo")
                close  = df_h["Close"].values.astype(float) if not df_h.empty else []
                rsi_v  = TechnicalIndicators.rsi(close) if len(close) > 14 else None
                rsi_i  = TechnicalIndicators.interpret_rsi(rsi_v)
                mas    = TechnicalIndicators.moving_averages(close, (20,50,200))
                sent   = get_news_sentiment(active, limit=4)
                try:
                    pdf_bytes = pdf_generator.generate_pdf_report(active, info, rsi_v, rsi_i, mas, sent)
                    st.download_button(
                        "📥 Download PDF Report",
                        data=pdf_bytes,
                        file_name=f"StockBot_{active}_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                    st.success("Report compiled successfully!")
                except Exception as ex:
                    st.error(f"PDF error: {ex}")
    with col_tip:
        st.markdown("#### 💡 Example AI Queries")
        st.markdown("""
```
What is the current price of RELIANCE.NS?
Technical analysis for TCS
Compare TCS INFY WIPRO HCLTECH
News sentiment analysis for SBIN.NS
Fundamental metrics for HDFCBANK
History of TATAMOTORS.NS 6mo
```
        """)

    # Disclaimer
    st.markdown("""<div class="disclaimer-box">
    ⚖️ <strong>Regulatory Disclaimer:</strong> StockBot India provides technical indicators and market data for informational purposes only.
    This is NOT investment advice. Past performance does not guarantee future results. Consult a SEBI-registered financial advisor before investing.
    </div>""", unsafe_allow_html=True)


with tab_sector:
    st.subheader("🔄 Sector Peer Comparison Dashboard")
    st.caption("Compare industry peers across key Indian market sectors.")

    sel_sector   = st.selectbox("Select Sector", list(SECTOR_MAP.keys()), key="sector_sel")
    sector_syms  = SECTOR_MAP[sel_sector]

    with st.spinner("Fetching sector data…"):
        rows = []
        for t in sector_syms:
            info  = fetch_info(t)
            if not info:
                continue
            dh    = fetch_history(t, "6mo")
            cls   = dh["Close"].values.astype(float) if not dh.empty else []
            rsi   = TechnicalIndicators.rsi(cls) if len(cls) > 14 else None
            price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
            prev  = info.get("previousClose", price)
            pct   = (price-prev)/prev*100 if prev else 0
            cap   = info.get("marketCap",0) or 0
            rows.append({
                "Ticker": t,
                "Name"  : info.get("shortName", t),
                "Price" : price,
                "Chg%"  : round(pct,2),
                "P/E"   : info.get("trailingPE", np.nan),
                "Mkt Cap (Cr)": round(cap/10000000,2) if cap else np.nan,
                "RSI"   : round(rsi,2) if rsi else np.nan,
            })

    if rows:
        df_sec = pd.DataFrame(rows)
        df_disp = df_sec.copy()
        df_disp["Price"]       = df_disp["Price"].apply(format_inr)
        df_disp["Chg%"]        = df_disp["Chg%"].apply(lambda v: f"{v:+.2f}%")
        df_disp["P/E"]         = df_disp["P/E"].apply(lambda v: f"{v:.1f}" if not pd.isna(v) else "N/A")
        df_disp["Mkt Cap (Cr)"]= df_disp["Mkt Cap (Cr)"].apply(lambda v: f"₹{v:,.1f}Cr" if not pd.isna(v) else "N/A")
        df_disp["RSI"]         = df_disp["RSI"].apply(lambda v: f"{v:.1f}" if not pd.isna(v) else "N/A")
        st.dataframe(df_disp, use_container_width=True, hide_index=True)

        ch1, ch2 = st.columns(2)
        with ch1:
            fig_chg = go.Figure(go.Bar(
                x=df_sec["Name"], y=df_sec["Chg%"],
                marker_color=["#26a69a" if x>=0 else "#ef5350" for x in df_sec["Chg%"]],
                text=df_sec["Chg%"].apply(lambda x: f"{x:+.2f}%"),
                textposition="auto",
            ))
            fig_chg.update_layout(title="<b>1-Day Return %</b>", template="plotly_dark",
                                  paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                  height=320, margin=dict(l=10,r=10,t=40,b=10))
            st.plotly_chart(fig_chg, use_container_width=True)

        with ch2:
            df_pe = df_sec.dropna(subset=["P/E"])
            fig_pe = go.Figure(go.Bar(
                x=df_pe["Name"], y=df_pe["P/E"],
                marker_color="#3b82f6",
                text=df_pe["P/E"].apply(lambda x: f"{x:.1f}x"),
                textposition="auto",
            ))
            fig_pe.update_layout(title="<b>P/E Valuation Multiple</b>", template="plotly_dark",
                                 paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                 height=320, margin=dict(l=10,r=10,t=40,b=10))
            st.plotly_chart(fig_pe, use_container_width=True)
    else:
        st.info("Could not load sector data — market may be closed.")

with tab_portfolio:
    st.subheader("💼 Investment Portfolio Tracker")

    holdings = db_manager.get_portfolio()
    if holdings:
        total_val, total_inv, metrics = 0, 0, []
        with st.spinner("Fetching live prices for portfolio…"):
            for h in holdings:
                info   = fetch_info(h["ticker"])
                curr   = info.get("currentPrice") or info.get("regularMarketPrice", h["buy_price"])
                cv     = h["quantity"] * curr
                inv    = h["quantity"] * h["buy_price"]
                pl     = cv - inv
                plpct  = pl/inv*100 if inv else 0
                metrics.append({**h, "curr_price":curr, "curr_val":cv, "pl":pl, "pl_pct":plpct})
                total_val += cv
                total_inv += inv

        total_pl    = total_val - total_inv
        total_plpct = total_pl/total_inv*100 if total_inv else 0

        m1, m2, m3 = st.columns(3)
        for col, val, lbl, cls in [
            (m1, format_inr(total_val),  "Total Portfolio Value", "neutral"),
            (m2, format_inr(total_inv),  "Total Amount Invested",  "neutral"),
            (m3, f"{'+'if total_pl>=0 else ''}{format_inr(total_pl)} ({total_plpct:+.2f}%)",
             "Overall P&L", "up" if total_pl>=0 else "down"),
        ]:
            col.markdown(f"""<div class="metric-card">
                <div class="metric-value {cls}">{val}</div>
                <div class="metric-label">{lbl}</div></div>""", unsafe_allow_html=True)

        table = []
        for h in metrics:
            em = "🟢" if h["pl"]>=0 else "🔴"
            table.append({
                "Ticker": h["ticker"], "Qty": h["quantity"],
                "Buy Price": format_inr(h["buy_price"]),
                "Current Price": format_inr(h["curr_price"]),
                "Current Value": format_inr(h["curr_val"]),
                "P&L": f"{em} {format_inr(h['pl'])} ({h['pl_pct']:+.2f}%)",
            })
        st.dataframe(pd.DataFrame(table), use_container_width=True, hide_index=True)

        st.markdown("##### Remove a Position")
        rc1, rc2 = st.columns([3,1])
        with rc1:
            sel = st.selectbox("Select position",
                               options=metrics,
                               format_func=lambda h: f"{h['ticker']} — {h['quantity']} shares @ {format_inr(h['buy_price'])}",
                               key="port_remove_sel")
        with rc2:
            st.write(""); st.write("")
            if st.button("❌ Remove", use_container_width=True, key="port_remove_btn"):
                db_manager.remove_from_portfolio(sel["id"])
                st.success(f"Removed {sel['ticker']} from portfolio.")
                st.rerun()
    else:
        st.info("📭 Portfolio is empty. Add a holding below to start tracking.")

    st.divider()
    st.markdown("#### ➕ Add New Holding")
    a1,a2,a3,a4 = st.columns(4)
    with a1: add_t  = st.text_input("Ticker", placeholder="RELIANCE.NS", key="port_add_tick")
    with a2: add_q  = st.number_input("Quantity", min_value=0.1, value=10.0, step=1.0, key="port_add_qty")
    with a3: add_p  = st.number_input("Buy Price (₹)", min_value=0.1, value=1000.0, key="port_add_price")
    with a4: add_d  = st.date_input("Buy Date", value=datetime.now(), key="port_add_date")

    if st.button("💾 Save to Portfolio", use_container_width=True, key="port_save_btn"):
        if add_t.strip():
            rt = resolve_ticker(add_t)
            ok, _ = validate_ticker(rt)
            if ok:
                info2 = fetch_info(rt)
                if info2.get("currentPrice") or info2.get("regularMarketPrice"):
                    s, m2 = db_manager.add_to_portfolio(rt, add_q, add_p, add_d.strftime("%Y-%m-%d"))
                    if s: st.success(m2)
                    else: st.error(m2)
                    if s: st.rerun()
                else:
                    st.error(f"❌ No live data for '{rt}'. Check ticker symbol.")
            else:
                st.error("Invalid ticker format.")
        else:
            st.error("Please enter a ticker symbol.")

with tab_watchlist:
    st.subheader("📋 Stock Watchlist (SQLite Persistent)")
    wl = db_manager.get_watchlist()

    if wl:
        wl_rows = []
        with st.spinner("Loading watchlist data…"):
            for sym in wl:
                info  = fetch_info(sym)
                price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
                prev  = info.get("previousClose", price)
                pct   = (price-prev)/prev*100 if prev else 0
                cur   = info.get("currency","INR")
                wl_rows.append({
                    "Ticker": sym,
                    "Company": info.get("shortName", sym),
                    "Price": format_inr(price) if cur=="INR" else f"{cur} {price:,.2f}",
                    "1D Chg%": f"{pct:+.2f}%",
                    "Status": "🟢 Up" if pct>=0 else "🔴 Down",
                })

        st.dataframe(pd.DataFrame(wl_rows), use_container_width=True, hide_index=True)

        st.markdown("##### Watchlist Actions")
        for row in wl_rows:
            wc1, wc2, wc3 = st.columns([4,1,1])
            with wc1:
                st.write(f"**{row['Company']}** `{row['Ticker']}` — {row['Price']} {row['1D Chg%']}")
            with wc2:
                if st.button("📊 Analyze", key=f"wl_focus_{row['Ticker']}", use_container_width=True):
                    st.session_state.chart_ticker = row["Ticker"]
                    st.rerun()
            with wc3:
                if st.button("❌ Remove", key=f"wl_del_{row['Ticker']}", use_container_width=True):
                    db_manager.remove_from_watchlist(row["Ticker"])
                    st.rerun()
    else:
        st.info("Watchlist is empty. Add tickers below.")

    st.divider()
    st.markdown("#### ➕ Add to Watchlist")
    wla1, wla2 = st.columns([3,1])
    with wla1:
        add_wl = st.text_input("Ticker / Company Name", placeholder="TCS, WIPRO, TATAMOTORS", key="wl_add_input")
    with wla2:
        st.write(""); st.write("")
        if st.button("➕ Add", use_container_width=True, key="wl_add_btn"):
            if add_wl.strip():
                rt = resolve_ticker(add_wl)
                ok, _ = validate_ticker(rt)
                if ok:
                    tinfo = fetch_info(rt)
                    if tinfo.get("currentPrice") or tinfo.get("regularMarketPrice"):
                        s, m3 = db_manager.add_to_watchlist(rt)
                        if s: st.success(m3)
                        else: st.warning(m3)
                        if s: st.rerun()
                    else:
                        st.error(f"No market data for '{rt}'. Check the symbol.")
                else:
                    st.error("Invalid ticker characters.")
            else:
                st.error("Please enter a ticker symbol.")


st.divider()
st.markdown("## 💬 Agent Analysis Chat")
st.caption(
    "Ask anything about stocks, technical indicators, sector comparisons, or news sentiment. "
    "Powered by **Groq LLaMA-3.3-70b** with fallback direct analysis."
)

chat_box = st.container()
with chat_box:
    if not st.session_state.messages:
        st.info("💡 Try: *'What is the current price of TCS?'* or *'Technical analysis for RELIANCE.NS'*")
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["role"] == "assistant":
                st.code(msg["content"], language="")
            else:
                st.write(msg["content"])

if prompt := st.chat_input("Ask about stocks, technicals, news, comparisons…", key="main_chat_input"):
    st.session_state.messages.append({"role":"user","content":prompt})
    with st.chat_message("user"):
        st.write(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Analyzing markets…"):
            answer = run_agent(prompt)
        st.code(answer, language="")
    st.session_state.messages.append({"role":"assistant","content":answer})
    st.rerun()