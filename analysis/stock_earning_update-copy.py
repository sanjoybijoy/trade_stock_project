import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from .models import EarningsData, SP500Ticker
from django.db import transaction

def nan_to_none(value):
    """Converts numpy.nan to None, which is compatible with database fields."""
    if pd.isna(value) or value is np.nan:
        return None
    return value

def fetch_and_save_earnings(symbol):
    """
    Fetches earnings data and stock metrics for a symbol.
    Saves/updates a SINGLE record per symbol with 4 slots (1 upcoming, 3 past).
    Uses ticker.earnings_dates and handles NaN values.
    """
    ticker = yf.Ticker(symbol)
    
    # 1. Fetch Basic Info & Metrics
    try:
        info = ticker.info
    except Exception:
        info = {}
        
    company_name = nan_to_none(info.get("longName"))
    
    # Extract Stock Metrics
    metrics = {
        "volume": nan_to_none(info.get("volume")),
        "averageVolume10days": nan_to_none(info.get("averageVolume10days")),
        "averageVolume3months": nan_to_none(info.get("averageVolume")),
        "marketCap": nan_to_none(info.get("marketCap")),
        "fiftyDayAverage": nan_to_none(info.get("fiftyDayAverage")),
        "fiftyTwoWeekLow": nan_to_none(info.get("fiftyTwoWeekLow")),
        "fiftyTwoWeekHigh": nan_to_none(info.get("fiftyTwoWeekHigh")),
        "sharesOutstanding": nan_to_none(info.get("sharesOutstanding")),
    }

    upcoming_event = {}
    historical_events = []

    try:
        df = ticker.earnings_dates
        if df is not None and not df.empty:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df.index = pd.to_datetime(df.index).tz_localize(None)
            
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            upcoming_df = df[df.index >= today].sort_index(ascending=True)
            if not upcoming_df.empty:
                row = upcoming_df.iloc[0]
                upcoming_event = {
                    "date": upcoming_df.index[0].date(),
                    "eps_estimate": nan_to_none(row.get("EPS Estimate")),
                    "reported_eps": nan_to_none(row.get("Reported EPS")),
                    "surprise": nan_to_none(row.get("Surprise(%)"))
                }
            
            past_df = df[df.index < today].sort_index(ascending=False)
            for timestamp, row in past_df.iterrows():
                if len(historical_events) >= 3: break
                historical_events.append({
                    "date": timestamp.date(),
                    "eps_estimate": nan_to_none(row.get("EPS Estimate")),
                    "reported_eps": nan_to_none(row.get("Reported EPS")),
                    "surprise": nan_to_none(row.get("Surprise(%)"))
                })
    except Exception as e:
        print(f"Error fetching earnings_dates for {symbol}: {e}")

    # Consolidate into a single model update
    defaults = { "company_name": company_name, **metrics }

    for i in range(1, 5):
        defaults.update({
            f"earnings_date_{i}": None,
            f"eps_estimate_{i}": None,
            f"reported_eps_{i}": None,
            f"surprise_pct_{i}": None,
        })

    if upcoming_event:
        defaults.update({
            "earnings_date_1": upcoming_event["date"],
            "eps_estimate_1": upcoming_event["eps_estimate"],
            "reported_eps_1": upcoming_event["reported_eps"],
            "surprise_pct_1": upcoming_event["surprise"],
        })

    for i, event in enumerate(historical_events):
        slot_num = i + 2
        defaults.update({
            f"earnings_date_{slot_num}": event["date"],
            f"eps_estimate_{slot_num}": event["eps_estimate"],
            f"reported_eps_{slot_num}": event["reported_eps"],
            f"surprise_pct_{slot_num}": event["surprise"],
        })

    # Check if the ticker is in the S&P 500 and set stock_index
    if SP500Ticker.objects.filter(symbol=symbol).exists():
        defaults['stock_index'] = 'SNP500'
    else:
        defaults['stock_index'] = 'No'

    obj, created = EarningsData.objects.update_or_create(symbol=symbol, defaults=defaults)
    return f"{symbol}: {'Created' if created else 'Updated'}"

def update_multiple_tickers_earnings(tickers_string):
    tickers = [t.strip().upper() for t in tickers_string.split(',') if t.strip()]
    summary = []
    for symbol in tickers:
        try:
            msg = fetch_and_save_earnings(symbol)
            summary.append(msg)
        except Exception as e:
            summary.append(f"Failed {symbol}: {str(e)}")
    return summary
