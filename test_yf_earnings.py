import yfinance as yf
import pandas as pd

def test_ticker(symbol):
    ticker = yf.Ticker(symbol)
    print(f"\n--- Testing {symbol} ---")
    
    print("\n1. ticker.calendar:")
    try:
        cal = ticker.calendar
        print(cal)
        print("Type:", type(cal))
    except Exception as e:
        print("Error:", e)

    print("\n2. ticker.get_calendar():")
    try:
        cal2 = ticker.get_calendar()
        print(cal2)
    except Exception as e:
        print("Error:", e)

    print("\n3. ticker.earnings_history:")
    try:
        hist = ticker.get_earnings_history()
        print(hist.head())
        print("Columns:", hist.columns.tolist())
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_ticker("NVDA")
