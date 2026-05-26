#!/usr/bin/env python3
"""Quick syntax verification"""
import sys
import os
sys.path.insert(0, r'd:\AIProject')

# Monkeypatch streamlit session state before import
import streamlit as st

class MockSessionState(dict):
    def __getattr__(self, name):
        if name == "chart_ticker":
            return "RELIANCE.NS"
        if name == "chart_period":
            return "3mo"
        if name == "messages":
            return []
        if name == "watchlist":
            return ["RELIANCE.NS", "TCS.NS"]
        if name == "portfolio":
            return []
        return None
    def __setattr__(self, name, value):
        self[name] = value

# Apply monkeypatch
st.session_state = MockSessionState()

try:
    print("Attempting to import app module...")
    # Just import to check for syntax errors
    import app
    print("[OK] Module imported successfully - no syntax errors")
    
    # Check that the new method exists
    if hasattr(app.TechnicalIndicators, 'calculate_rsi_series'):
        print("[OK] calculate_rsi_series method exists")
    else:
        print("[ERROR] calculate_rsi_series method not found")
        sys.exit(1)
    
    # Quick test with dummy data
    import numpy as np
    test_prices = np.array([100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115])
    result = app.TechnicalIndicators.calculate_rsi_series(test_prices, 14)
    
    print(f"[OK] Method executed without errors")
    print(f"  Input size: {len(test_prices)}")
    print(f"  Output size: {len(result)}")
    print(f"  First None values: {sum(1 for x in result if x is None)}")
    print(f"  RSI values: {sum(1 for x in result if x is not None)}")
    
    if len(result) == len(test_prices):
        print("[OK] Output length matches input length")
    else:
        print(f"[ERROR] Output length mismatch: {len(result)} vs {len(test_prices)}")
        sys.exit(1)
        
except SyntaxError as e:
    print(f"[ERROR] Syntax error: {e}")
    sys.exit(1)
except ImportError as e:
    print(f"[ERROR] Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n[OK] All verification checks passed successfully!")
