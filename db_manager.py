import sqlite3
import os
from datetime import datetime

DB_FILE = "financial_agent.db"

def get_connection():
    """Get a database connection"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # access columns by name
    return conn

def init_db():
    """Initialize the database and create tables if they do not exist"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT UNIQUE NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            quantity REAL NOT NULL,
            buy_price REAL NOT NULL,
            buy_date TEXT NOT NULL
        )
    """)
    
    conn.commit()
    
    cursor.execute("SELECT COUNT(*) FROM watchlist")
    if cursor.fetchone()[0] == 0:
        default_watchlist = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "SBIN.NS"]
        for ticker in default_watchlist:
            try:
                cursor.execute("INSERT INTO watchlist (ticker) VALUES (?)", (ticker,))
            except sqlite3.IntegrityError:
                pass
        conn.commit()
        
    conn.close()

def get_watchlist():
    """Retrieve all tickers from watchlist"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ticker FROM watchlist ORDER BY added_at ASC")
    rows = cursor.fetchall()
    conn.close()
    return [row["ticker"] for row in rows]

def add_to_watchlist(ticker):
    """Add a ticker to the watchlist"""
    ticker = ticker.strip().upper()
    if not ticker:
        return False, "Ticker cannot be empty"
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO watchlist (ticker) VALUES (?)", (ticker,))
        conn.commit()
        success, msg = True, f"Added {ticker} to watchlist"
    except sqlite3.IntegrityError:
        success, msg = False, f"{ticker} is already in watchlist"
    finally:
        conn.close()
    return success, msg

def remove_from_watchlist(ticker):
    """Remove a ticker from the watchlist"""
    ticker = ticker.strip().upper()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM watchlist WHERE ticker = ?", (ticker,))
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    if rows_affected > 0:
        return True, f"Removed {ticker} from watchlist"
    return False, f"{ticker} was not in watchlist"

def get_portfolio():
    """Retrieve all holdings from portfolio"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, ticker, quantity, buy_price, buy_date FROM portfolio ORDER BY ticker ASC")
    rows = cursor.fetchall()
    conn.close()
    
    holdings = []
    for row in rows:
        holdings.append({
            "id": row["id"],
            "ticker": row["ticker"],
            "quantity": row["quantity"],
            "buy_price": row["buy_price"],
            "buy_date": row["buy_date"]
        })
    return holdings

def add_to_portfolio(ticker, quantity, buy_price, buy_date):
    """Add a stock holding to the portfolio"""
    ticker = ticker.strip().upper()
    if not ticker:
        return False, "Ticker cannot be empty"
    if quantity <= 0:
        return False, "Quantity must be greater than zero"
    if buy_price <= 0:
        return False, "Buy price must be greater than zero"
        
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO portfolio (ticker, quantity, buy_price, buy_date) VALUES (?, ?, ?, ?)",
            (ticker, quantity, buy_price, buy_date)
        )
        conn.commit()
        success, msg = True, f"Added {quantity} shares of {ticker} to portfolio"
    except Exception as e:
        success, msg = False, f"Failed to add holding: {str(e)}"
    finally:
        conn.close()
    return success, msg

def remove_from_portfolio(holding_id):
    """Remove a holding from the portfolio by its database ID"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM portfolio WHERE id = ?", (holding_id,))
    rows_affected = cursor.rowcount
    conn.commit()
    conn.close()
    if rows_affected > 0:
        return True, "Holding removed from portfolio"
    return False, "Holding not found"
