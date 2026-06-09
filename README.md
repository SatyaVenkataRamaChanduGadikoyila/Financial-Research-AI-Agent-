# 📈 StockBot India — AI Financial Research Agent

> **An intelligent AI-powered financial research assistant for Indian and global stock markets.**
>
> Built with **Groq LLaMA-3.3-70B**, **LangChain**, **Streamlit**, **Yahoo Finance**, and **NewsAPI**.

---

## 🚀 Overview

StockBot India is a conversational AI agent that helps investors, students, and researchers analyze stocks using real-time market data, technical indicators, sentiment analysis, and AI-generated insights.

The application supports NSE, BSE, Nifty, Sensex, NYSE, and NASDAQ stocks through a simple chat-based interface.

---

## ✨ Key Features

### 🤖 AI-Powered Financial Assistant

* Natural language stock research
* Tool-calling AI agent using Groq LLaMA-3.3-70B
* Intelligent ticker resolution and market insights

### 💰 Live Stock Market Data

* Real-time stock prices
* Historical OHLCV data
* Market statistics via Yahoo Finance

### 📊 Technical Analysis

* RSI (14)
* Bollinger Bands
* Moving Averages (20, 50, 200)
* Golden Cross & Death Cross detection
* Trend analysis

### 📰 News Sentiment Analysis

* Live financial news headlines
* Sentiment scoring using TextBlob
* Positive, Neutral, and Negative classification

### 💼 Portfolio Tracker

* SQLite-backed portfolio management
* Profit & Loss tracking
* Live portfolio valuation

### 📋 Watchlist Management

* Persistent stock watchlist
* Quick stock monitoring
* One-click analysis

### 🔄 Sector Comparison

Compare stocks across sectors:

* Information Technology
* Banking
* Energy
* Automobile
* Pharmaceuticals

### 📄 PDF Research Reports

* Export stock research reports
* Professional PDF generation using FPDF2
* Educational-use disclaimer included

### 📈 Interactive Charts

* Candlestick charts
* RSI visualization
* Volume analysis
* Moving Average overlays
* Plotly interactive dashboards

---

## 🏗️ Project Architecture

```text
AIProject/
├── app.py               # Main Streamlit application
├── db_manager.py        # Database management layer
├── pdf_generator.py     # PDF report generation
├── requirements.txt     # Dependencies
├── .env                 # API keys
├── .gitignore           # Git ignore rules
├── financial_agent.db   # SQLite database
├── test_agent.py        # Agent tests
├── test_groq.py         # Groq connectivity tests
├── test_portfolio.py    # Portfolio tests
├── test_yfinance.py     # Market data tests
└── verify_syntax.py     # Syntax checker
```

---

## ⚙️ Technology Stack

| Category               | Technology               |
| ---------------------- | ------------------------ |
| LLM                    | Groq LLaMA-3.3-70B       |
| Agent Framework        | LangChain                |
| Frontend               | Streamlit                |
| Market Data            | Yahoo Finance (yfinance) |
| Sentiment Analysis     | TextBlob, VaderSentiment |
| Database               | SQLite                   |
| Visualization          | Plotly                   |
| Report Generation      | FPDF2                    |
| Environment Management | python-dotenv            |

---

## 📋 Prerequisites

* Python 3.10+
* pip
* Groq API Key
* (Optional) NewsAPI Key

---

## 🔧 Installation

### 1. Clone Repository

```bash
git clone https://github.com/SatyaVenkataRamaChanduGadikoyila/Financial-Research-AI-Agent-.git

cd Financial-Research-AI-Agent-
```

### 2. Create Virtual Environment

#### Windows

```bash
python -m venv venv

venv\Scripts\activate
```

#### Linux / macOS

```bash
python -m venv venv

source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Download TextBlob Corpora

```bash
python -m textblob.download_corpora
```

### 5. Configure Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=gsk_your_groq_api_key

NEWS_API_KEY=your_newsapi_key
```

---

## 🔑 API Configuration

### Groq API (Required)

Used for:

* AI chat interface
* Market analysis
* Tool calling
* Research generation

Get a free API key from:

https://console.groq.com

---

### NewsAPI (Optional)

Used for:

* Live news headlines
* Sentiment analysis

Get a free API key from:

https://newsapi.org

If no NewsAPI key is provided, the application automatically switches to Demo Mode.

---

## ▶️ Running the Application

```bash
streamlit run app.py
```

Open:

```text
http://localhost:8501
```

---

## 💬 Example Queries

```text
What is the current price of RELIANCE.NS?

Technical analysis for TCS

Compare TCS INFY WIPRO HCLTECH

News sentiment analysis for SBIN.NS

Fundamental metrics for HDFCBANK

History of TATAMOTORS.NS 6mo

What is the RSI for Infosys?

Show me Bollinger Bands for Wipro

Compare AAPL MSFT GOOGL

Analyze Reliance Industries stock
```

---

## 🌍 Supported Markets

| Market   | Example     |
| -------- | ----------- |
| NSE      | RELIANCE.NS |
| BSE      | RELIANCE.BO |
| Nifty 50 | ^NSEI       |
| Sensex   | ^BSESN      |
| NASDAQ   | AAPL        |
| NYSE     | TSLA        |

### Smart Alias Support

Users can type:

```text
reliance
tcs
sbi
infosys
apple
tesla
nifty
sensex
```

and the agent automatically maps them to valid ticker symbols.

---

## 🗄️ Database

SQLite database is automatically created on first launch.

Default watchlist:

```text
RELIANCE.NS
TCS.NS
INFY.NS
HDFCBANK.NS
SBIN.NS
```

No manual database setup required.

---

## 📦 Dependencies

```text
streamlit
plotly
yfinance
pandas
numpy
langchain
langchain-core
langchain-groq
textblob
vaderSentiment
requests
python-dotenv
fpdf2
pytz
cachetools
```

---

## ⚠️ Important Disclaimer

This project is intended solely for educational, research, and learning purposes.

It does not provide financial, investment, legal, or tax advice.

Always consult a SEBI-registered investment advisor or qualified financial professional before making investment decisions.

Past performance is not indicative of future results.

---

## 📚 Learning Objectives

This project demonstrates:

* AI Agent Development
* Tool Calling with LLMs
* Financial Data Analysis
* Sentiment Analysis
* LangChain Integration
* Streamlit Application Development
* Database Management
* Report Generation
* Data Visualization

---

## 🤝 Contributing

Contributions, feature requests, and improvements are welcome.

1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Open a Pull Request

---

## 📄 License

This project is developed for academic and educational purposes.

Financial data belongs to their respective providers and is subject to their terms of service.

---

## 👨‍💻 Author

**Satya Venkata Rama Chandu Gadikoyila**

AI/ML Enthusiast | Financial Analytics | Generative AI

GitHub:
https://github.com/SatyaVenkataRamaChanduGadikoyila
