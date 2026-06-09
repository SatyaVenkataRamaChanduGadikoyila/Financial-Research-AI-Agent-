from fpdf import FPDF
from datetime import datetime
import pandas as pd
import numpy as np
import re
import os

# Default font used; may be replaced at runtime if a Unicode TTF is available
FONT_NAME = 'helvetica'


def try_register_unicode_font(pdf: FPDF):
    """Attempt to register a Unicode TTF font (DejaVu or Noto) for FPDF output.
    If found, registers it as 'DejaVu' and updates FONT_NAME to use it.
    """
    global FONT_NAME
    candidates = [
        './fonts/DejaVuSans.ttf',
        './fonts/NotoSans-Regular.ttf',
        'C:\\Windows\\Fonts\\DejaVuSans.ttf',
        'C:\\Windows\\Fonts\\NotoSans-Regular.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf',
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                pdf.add_font('DejaVu', '', p, uni=True)
                FONT_NAME = 'DejaVu'
                return
            except Exception:
                continue
    # If no TTF found, leave FONT_NAME as helvetica

class StockReportPDF(FPDF):
    def header(self):
        # Top banner background
        self.set_fill_color(30, 41, 59)  # deep slate
        self.rect(0, 0, 210, 32, 'F')
        
        # White text for title
        self.set_text_color(255, 255, 255)
        self.set_font(FONT_NAME, 'B', 16)
        self.set_y(6)
        self.cell(0, 8, 'STOCKBOT INDIA - RESEARCH REPORT', ln=1, align='C')
        
        # Subtitle
        self.set_font(FONT_NAME, 'I', 10)
        self.cell(0, 6, f'Generated on {datetime.now().strftime("%d %B %Y, %I:%M %p IST")}', ln=1, align='C')
        self.ln(12)
        
    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        self.set_font(FONT_NAME, 'I', 8)
        self.set_text_color(128, 128, 128)
        
        # Draw a line above footer
        self.set_draw_color(200, 200, 200)
        self.line(10, 280, 200, 280)
        
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}  |  StockBot India Financial AI Research Assistant  |  Confidential & Proprietary', align='C')

    def chapter_title(self, label):
        self.set_font(FONT_NAME, 'B', 12)
        self.set_text_color(30, 41, 59)
        self.set_fill_color(241, 245, 249) # light gray background
        self.cell(0, 8, f"  {label}", ln=1, fill=True)
        self.ln(3)

    def section_header(self, label):
        self.set_font(FONT_NAME, 'B', 10)
        self.set_text_color(71, 85, 105)
        self.cell(0, 6, label, ln=1)
        self.ln(1)

def format_inr_pdf(val):
    if val is None or str(val) == 'N/A':
        return "N/A"
    try:
        val = float(val)
        is_neg = val < 0
        val = abs(val)
        s = f"{val:.2f}"
        parts = s.split('.')
        integer = parts[0]
        decimal = parts[1]
        
        if len(integer) <= 3:
            result = integer
        else:
            last_three = integer[-3:]
            remaining = integer[:-3]
            groups = []
            while len(remaining) > 0:
                groups.append(remaining[-2:])
                remaining = remaining[:-2]
            groups.reverse()
            result = ",".join(groups) + "," + last_three
            
        return ("-" if is_neg else "") + "Rs. " + result + "." + decimal
    except Exception:
        return f"Rs. {val}"


# Remove characters unsupported by default PDF font (e.g., emojis).
_EMOJI_PATTERN = re.compile('[\U00010000-\U0010FFFF]', flags=re.UNICODE)

def sanitize_text(s: str) -> str:
    """Normalize text for PDF fonts: replace common typographic Unicode with ASCII and strip emojis."""
    if s is None:
        return ""
    if not isinstance(s, str):
        s = str(s)
    # Normalize common punctuation to ASCII equivalents
    replacements = {
        '\u2014': '-',  # em dash
        '\u2013': '-',  # en dash
        '\u2018': "'", '\u2019': "'", '\u201c': '"', '\u201d': '"',
        '\u2026': '...', '\u2010': '-', '\u2012': '-',
    }
    for k, v in replacements.items():
        s = s.replace(k, v)
    # Remove emoji / unsupported high-plane characters
    s = _EMOJI_PATTERN.sub('', s)
    return s


def generate_pdf_report(ticker, info, rsi_val, rsi_interpretation, mas, sentiment):
    """
    Generate a highly professional PDF research report for a stock.
    Returns: Bytes of the PDF
    """
    pdf = StockReportPDF()
    pdf.alias_nb_pages()
    # Try to register a Unicode TTF font; if available, FONT_NAME will be updated
    try_register_unicode_font(pdf)
    pdf.add_page()
    
    # ----------------------------------------------------
    # SECTION 1: Company Profile & Core Metrics
    # ----------------------------------------------------
    name = info.get("longName") or info.get("shortName") or ticker
    sector = info.get("sector", "N/A")
    industry = info.get("industry", "N/A")
    currency = info.get("currency", "INR")
    price = info.get("currentPrice") or info.get("regularMarketPrice", 0)
    prev_close = info.get("previousClose", price)
    day_change = price - prev_close
    day_change_pct = (day_change / prev_close * 100) if prev_close else 0
    
    # Sanitize incoming text to avoid emoji/font issues
    name = sanitize_text(name)
    sector = sanitize_text(sector)
    industry = sanitize_text(industry)
    exchange = sanitize_text(info.get('exchange', 'N/A'))
    website = sanitize_text(info.get('website', 'N/A'))
    
    pdf.chapter_title(f"1. Executive Overview: {name} ({ticker})")
    
    # Grid of details
    pdf.set_font(FONT_NAME, '', 10)
    pdf.set_text_color(51, 65, 85)
    
    # Left column
    pdf.cell(95, 6, f"Sector: {sector}", ln=0)
    pdf.cell(95, 6, f"Current Price: {format_inr_pdf(price) if currency == 'INR' else f'{currency} {price:,.2f}'}", ln=1)
    
    pdf.cell(95, 6, f"Industry: {industry}", ln=0)
    pdf.cell(95, 6, f"Daily Change: {day_change_pct:+.2f}% ({format_inr_pdf(day_change) if currency == 'INR' else f'{currency} {day_change:,.2f}'})", ln=1)
    
    pdf.cell(95, 6, f"Exchange: {exchange}", ln=0)
    high_val = info.get('fiftyTwoWeekHigh')
    high_text = format_inr_pdf(high_val) if currency == 'INR' else (f"{currency} {high_val:,.2f}" if high_val else "N/A")
    pdf.cell(95, 6, f"52-Week High: {high_text}", ln=1)
    
    pdf.cell(95, 6, f"Website: {website}", ln=0)
    low_val = info.get('fiftyTwoWeekLow')
    low_text = format_inr_pdf(low_val) if currency == 'INR' else (f"{currency} {low_val:,.2f}" if low_val else "N/A")
    pdf.cell(95, 6, f"52-Week Low: {low_text}", ln=1)
    
    pdf.ln(4)
    
    # ----------------------------------------------------
    # SECTION 2: Fundamental Valuation
    # ----------------------------------------------------
    pdf.chapter_title("2. Fundamental Analysis & Valuation")
    
    mkt_cap = info.get('marketCap')
    if mkt_cap:
        mkt_cap_crores = mkt_cap / 10000000 if currency == 'INR' else mkt_cap / 1e9
        mkt_cap_label = f"Market Cap: {mkt_cap_crores:,.2f} Crores (INR)" if currency == 'INR' else f"Market Cap: ${mkt_cap_crores:,.2f} Billion"
    else:
        mkt_cap_label = "Market Cap: N/A"
        
    pe_ratio = info.get('trailingPE', 'N/A')
    fwd_pe = info.get('forwardPE', 'N/A')
    pb_ratio = info.get('priceToBook', 'N/A')
    div_yield = info.get('dividendYield', 0) * 100
    roe = info.get('returnOnEquity', 'N/A')
    if isinstance(roe, (float, int)):
        roe = f"{roe*100:.2f}%"
    debt_equity = info.get('debtToEquity', 'N/A')
    
    pdf.cell(95, 6, mkt_cap_label, ln=0)
    pdf.cell(95, 6, f"Return on Equity (ROE): {roe}", ln=1)
    
    pdf.cell(95, 6, f"Trailing P/E Ratio: {pe_ratio}", ln=0)
    pdf.cell(95, 6, f"Debt-to-Equity Ratio: {debt_equity}", ln=1)
    
    pdf.cell(95, 6, f"Forward P/E Ratio: {fwd_pe}", ln=0)
    pdf.cell(95, 6, f"Dividend Yield: {div_yield:.2f}%", ln=1)
    
    pdf.cell(95, 6, f"Price-to-Book (P/B): {pb_ratio}", ln=0)
    pdf.cell(95, 6, f"Current Ratio: {info.get('currentRatio', 'N/A')}", ln=1)
    
    pdf.ln(6)
    
    # ----------------------------------------------------
    # SECTION 3: Technical Indicators
    # ----------------------------------------------------
    pdf.chapter_title("3. Technical Indicator Status")
    
    pdf.set_font(FONT_NAME, 'B', 10)
    pdf.cell(60, 6, "Indicator", border=1, align='C', ln=0)
    pdf.cell(65, 6, "Value", border=1, align='C', ln=0)
    pdf.cell(65, 6, "Signal / Interpretation", border=1, align='C', ln=1)
    
    pdf.set_font(FONT_NAME, '', 9)
    # RSI row
    rsi_str = f"{rsi_val:.2f}" if rsi_val is not None else "N/A"
    pdf.cell(60, 6, "Relative Strength Index (RSI 14)", border=1, align='C', ln=0)
    pdf.cell(65, 6, rsi_str, border=1, align='C', ln=0)
    rsi_text = sanitize_text(rsi_interpretation or "N/A")
    pdf.cell(65, 6, rsi_text, border=1, align='C', ln=1)
    
    # MA rows
    for ma_name, ma_val in mas.items():
        ma_label = ma_name.upper().replace('MA', 'Moving Average ')
        val_str = format_inr_pdf(ma_val) if currency == 'INR' else f"{ma_val:,.2f}" if ma_val else "N/A"
        
        signal = "N/A"
        if ma_val and price:
            signal = "Above Average" if price > ma_val else "Below Average"
        
        pdf.cell(60, 6, ma_label, border=1, align='C', ln=0)
        pdf.cell(65, 6, val_str, border=1, align='C', ln=0)
        pdf.cell(65, 6, signal, border=1, align='C', ln=1)
        
    pdf.ln(6)
    
    # ----------------------------------------------------
    # SECTION 4: News & Sentiment Trends
    # ----------------------------------------------------
    pdf.chapter_title("4. Sentiment & News Catalyst Analysis")
    
    status = sentiment.get("status")
    if status == "success":
        overall = sanitize_text(sentiment.get("overall_sentiment", "NEUTRAL")).upper()
        polarity = sentiment.get("avg_polarity", 0)
        
        pdf.set_font(FONT_NAME, '', 10)
        pdf.cell(95, 6, f"Overall News Catalyst Sentiment: {overall}", ln=0)
        pdf.cell(95, 6, f"Average Polarity Score (-1 to 1): {polarity:+.3f}", ln=1)
        pdf.ln(3)
        
        pdf.set_font(FONT_NAME, 'B', 9)
        pdf.cell(0, 5, "Analyzed Headlines:", ln=1)
        pdf.set_font(FONT_NAME, '', 8.5)
        
        for idx, art in enumerate(sentiment.get("articles", [])[:4], 1):
            title = sanitize_text(art.get("title", "No Title"))
            source = sanitize_text(art.get("source", "Unknown Source"))
            sent = sanitize_text(art.get("sentiment", "NEUTRAL")).upper()
            pol = art.get("polarity", 0)
            
            pdf.multi_cell(0, 4.5, sanitize_text(f"{idx}. [{sent} | {pol:+.2f}] {title} (Source: {source})"))
            pdf.ln(1)
    else:
        pdf.set_font(FONT_NAME, 'I', 10)
        pdf.cell(0, 6, "Live News Sentiment is currently in Demo mode or NewsAPI is unconfigured.", ln=1)
        
    pdf.ln(8)
    
    # ----------------------------------------------------
    # SECTION 5: Compliance & Investment Disclaimer
    # ----------------------------------------------------
    pdf.chapter_title("5. Regulatory Compliance & Disclaimer")
    
    pdf.set_font(FONT_NAME, 'I', 8)
    pdf.set_text_color(100, 116, 139)
    
    disclaimer_text = (
        "This report is generated automatically by an AI-powered financial assistant for informational and research "
        "purposes only. It does not constitute financial, investment, legal, or tax advice. Stock trading involves substantial "
        "risk of loss and is not suitable for every investor. The historical data and indicators provided herein do not guarantee "
        "future performance or returns. You are solely responsible for evaluating the merits and risks associated with the use "
        "of any information in this report before making decisions. Please consult with a SEBI-registered investment advisor "
        "or professional financial planner before making any investment commitments."
    )
    pdf.multi_cell(0, 4, disclaimer_text)
    
    # Output bytes
    return pdf.output()
