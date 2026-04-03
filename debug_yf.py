import yfinance as yf
import pandas as pd

def debug_ticker(symbol):
    ticker = yf.Ticker(symbol)
    print(f"\n--- {symbol} ---")
    
    print("\n1. earnings_dates:")
    try:
        df = ticker.earnings_dates
        if df is not None:
            print("Columns:", df.columns.tolist())
            print("Index type:", type(df.index))
            print("Head:")
            print(df.head())
        else:
            print("earnings_dates is None")
    except Exception as e:
        print("Error:", e)

    print("\n2. calendar:")
    try:
        cal = ticker.calendar
        print("Type:", type(cal))
        print(cal)
    except Exception as e:
        print("Error:", e)

    print("\n3. earnings_history:")
    try:
        hist = ticker.get_earnings_history()
        if hist is not None:
            print("Columns:", hist.columns.tolist())
            print("Head:")
            print(hist.head())
        else:
            print("earnings_history is None")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    debug_ticker("NVDA")
