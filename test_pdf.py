#!/usr/bin/env python3
# Simple test to generate a sample PDF report using pdf_generator.generate_pdf_report
from pdf_generator import generate_pdf_report

sample_info = {
    "longName": "Demo Corp 📈",
    "shortName": "DemoCorp",
    "sector": "Technology",
    "industry": "Software",
    "currency": "INR",
    "currentPrice": 1267.90,
    "previousClose": 1291.00,
    "exchange": "NSE",
    "website": "https://democorp.example",
    "fiftyTwoWeekHigh": 1611.80,
    "fiftyTwoWeekLow": 1267.00,
    "marketCap": 1715782180000,
    "trailingPE": 21.26,
    "forwardPE": 19.5,
    "priceToBook": 3.2,
    "dividendYield": 0.012,
    "returnOnEquity": 0.18,
    "debtToEquity": 0.5,
    "currentRatio": 1.3,
}

rsi_val = 58.27
rsi_interpretation = "Neutral-to-Bullish"
mas = {"MA20": 1200.0, "MA50": 1150.0, "MA200": 1000.0}

sentiment = {
    "status": "success",
    "overall_sentiment": "POSITIVE",
    "avg_polarity": 0.12,
    "articles": [
        {"title": "DemoCorp reports strong quarter 📈", "source": "NewsWire", "sentiment": "positive", "polarity": 0.3},
        {"title": "Analysts upbeat on DemoCorp", "source": "MarketWatch", "sentiment": "positive", "polarity": 0.15},
    ]
}

if __name__ == '__main__':
    pdf_bytes = generate_pdf_report('DEMOCORP.NS', sample_info, rsi_val, rsi_interpretation, mas, sentiment)
    # FPDF may return either str or bytes; ensure bytes for writing
    if isinstance(pdf_bytes, str):
        pdf_bytes = pdf_bytes.encode('latin-1')
    out_path = 'd:\\AIProject\\sample_report.pdf'
    with open(out_path, 'wb') as f:
        f.write(pdf_bytes)
    print(f"Sample PDF written to: {out_path}")
