import yfinance as yf
import pandas as pd
import sys
import os

print("yfinance version:", yf.__version__)
ticker = "RELIANCE.NS"
print(f"Testing fetch_info for {ticker}...")
try:
    ticker_obj = yf.Ticker(ticker)
    info = ticker_obj.info
    print("Info success!")
    print("Keys in info:", list(info.keys())[:10] if info else "Empty info dict")
    price = info.get("currentPrice") or info.get("regularMarketPrice")
    print("Current price:", price)
except Exception as e:
    print("fetch_info failed:", e)

print(f"Testing download history for {ticker}...")
try:
    df = yf.download(ticker, period="3mo", progress=False)
    print("Download success! Shape:", df.shape)
    print("Columns:", df.columns)
    print("Head:\n", df.head())
except Exception as e:
    print("download failed:", e)
