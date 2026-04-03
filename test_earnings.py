import yfinance as yf
import pandas as pd

ticker = yf.Ticker("NVDA")

print("--- Calendar ---")
try:
    cal = ticker.get_calendar()
    print(type(cal))
    print(cal)
except Exception as e:
    print(f"Calendar Error: {e}")

print("\n--- Earnings History ---")
try:
    hist = ticker.get_earnings_history()
    print(type(hist))
    print(hist.head())
except Exception as e:
    print(f"History Error: {e}")

print("\n--- Earnings Dates ---")
try:
    ed = ticker.earnings_dates
    print(type(ed))
    print(ed.head())
except Exception as e:
    print(f"Earnings Dates Error: {e}")
