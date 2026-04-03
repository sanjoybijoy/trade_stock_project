from datetime import datetime, timedelta
from analysis.models import ThreeMonthsRegSHO

def preparedRegSho_df():
    start_date = datetime.now()
    end_date = start_date - timedelta(days=90)
    combined_sho_data = ThreeMonthsRegSHO.objects.filter(Date__range=[end_date, start_date]).order_by('-Date')
    # Convert to DataFrames
    combined_sho_df = pd.DataFrame(list(combined_sho_data.values()))
    # Ensure Date columns are timezone-naive UTC
    combined_sho_df['Date'] = pd.to_datetime(combined_sho_df['Date']).dt.tz_localize(None)
    # Add vertical lines if dates info (Reg sho symbol) is found
    combined_sho_df['Date'] = pd.to_datetime(combined_sho_df['Date'])
    return combined_sho_df



import pandas as pd
import pandas_market_calendars as mcal

def check_symbol_dates(df, symbol):
    # Ensure 'Date' column is in datetime format
    if 'Date' not in df or 'Symbol' not in df:
        raise ValueError("DataFrame must have 'Date' and 'Symbol' columns.")

    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')  # Convert to datetime
    symbol_data = df[df['Symbol'] == symbol].sort_values(by='Date')  # Filter and sort by Date

    if symbol_data.empty:
        return None  # No data for the given symbol

    # Reset index to ensure sequential indexing
    symbol_data = symbol_data.reset_index(drop=True)

    # Get NASDAQ trading calendar
    nasdaq_calendar = mcal.get_calendar('NASDAQ')
    trading_schedule = nasdaq_calendar.schedule(
        start_date=df['Date'].min(),
        end_date=df['Date'].max()
    )
    all_trading_days = trading_schedule.index  # Get all valid trading days

    # Initialize list for events
    event_dates = []

    # Find entry and exit points
    for idx in range(len(symbol_data)):
        current_date = symbol_data.at[idx, 'Date']
        previous_date = symbol_data.at[idx - 1, 'Date'] if idx > 0 else None

        if previous_date is None or current_date not in all_trading_days:
            # New entry detected
            event_dates.append({'type': 'EN.', 'date': current_date})
        elif (current_date - previous_date).days > 1:
            # Check if the gap includes trading days
            trading_gap = all_trading_days[(all_trading_days > previous_date) & (all_trading_days < current_date)]
            if not trading_gap.empty:
                event_dates.append({'type': 'EN.', 'date': current_date})

    # Add exit dates for gaps
    for i in range(len(event_dates) - 1):
        entry_date = event_dates[i]['date']
        next_entry_date = event_dates[i + 1]['date']

        # Find the last date before the next entry
        gap_data = symbol_data[(symbol_data['Date'] > entry_date) & (symbol_data['Date'] < next_entry_date)]
        if not gap_data.empty:
            last_date = gap_data['Date'].iloc[-1]
            if last_date != entry_date:
                event_dates.insert(i + 1, {'type': 'EX.', 'date': last_date})

    # Handle the last exit if there's no 'Con.'
    last_event = event_dates[-1] if event_dates else None
    last_appearance = symbol_data['Date'].max()
    dataset_latest_date = df['Date'].max()

    if last_event and last_event['type'] == 'EN.' and last_appearance != dataset_latest_date:
        # Add exit if the last event is an entry and no continue is present
        event_dates.append({'type': 'EX.', 'date': last_appearance})
    elif last_appearance == dataset_latest_date:
        # Add a "continue" if the last appearance matches the dataset's latest date
        event_dates.append({'type': 'CON.', 'date': dataset_latest_date})

    return event_dates

