import yfinance as yf
from datetime import timedelta
from django.db import transaction
from .models import StockSymbolData, StockPriceData

from django.utils.timezone import make_aware
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
from typing import List, Tuple
from .models import NewsSymbolData, NewsData

def fetch_stock_data_with_fallback(symbol, periods, start_date=None):
    """Fetch stock data, trying multiple periods if the preferred one fails."""
    # First try fetching from start_date if provided
    if start_date:
        try:
            print(f"DEBUG: Trying to fetch {symbol} starting from {start_date}")
            # If start_date is provided, yfinance recommends not using period
            stock_data = yf.download(symbol, start=start_date, interval="1d")
            print(f"DEBUG: Fetched data length for {symbol} from start_date: {len(stock_data) if stock_data is not None else 0}")
            if stock_data is not None and not stock_data.empty:
                return stock_data
        except Exception as e:
            print(f"DEBUG: Failed to fetch {symbol} from start_date {start_date}. Error: {e}")

    # Fallback to predefined periods
    for period in periods:
        try:
            print(f"DEBUG: Trying to fetch {symbol} for period: {period}")
            stock_data = yf.download(symbol, period=period, interval="1d")
            print(f"DEBUG: Fetched data length for {symbol} for period {period}: {len(stock_data) if stock_data is not None else 0}")
            if stock_data is not None and not stock_data.empty:
                return stock_data
        except Exception as e:
            print(f"DEBUG: Failed to fetch {symbol} for period {period}. Error: {e}")
    
    print(f"DEBUG: All attempts failed for {symbol}.")
    return None

def save_stock_data_to_db_old(symbol, dataframe):
    """Save the stock data from a DataFrame into the database."""
    with transaction.atomic():
        # Get or create the stock symbol in the database
        stock_symbol, created = StockSymbolData.objects.get_or_create(symbol=symbol)
        if created:
            print(f"Created new StockSymbolData for symbol: {symbol}")

         # Sort the DataFrame by the timestamp in descending order
        dataframe = dataframe.sort_values(by="timestamp", ascending=False)  

        # Iterate through the DataFrame rows and save them to the database
        for _, row in dataframe.iterrows():
            # Create or update stock price data
            _, created = StockPriceData.objects.update_or_create(
                stock_symbol=stock_symbol,
                timestamp=row['timestamp'].date(),
                defaults={
                    "open": row['open'],
                    "high": row['high'],
                    "low": row['low'],
                    "close": row['close'],
                    "adj_close": row.get('Adj Close', row['close']),  # Use 'Adj Close' if available
                    "volume": row['volume']
                }
            )
            if created:
                print(f"Inserted data for {symbol} on {row['timestamp'].date()}")
            else:
                print(f"Updated data for {symbol} on {row['timestamp'].date()}")
from datetime import date
from django.db import transaction

def save_stock_data_to_db(symbol, dataframe):
    """Save the stock data from a DataFrame into the database using bulk_create for efficiency."""
    with transaction.atomic():
        # Get or create the stock symbol in the database
        stock_symbol, created = StockSymbolData.objects.get_or_create(symbol=symbol)
        if created:
            print(f"Created new StockSymbolData for symbol: {symbol}")

        # Sort the DataFrame by the timestamp in descending order
        dataframe = dataframe.sort_values(by="timestamp", ascending=False)

        # Prepare a list of StockPriceData instances for bulk_create
        new_records = []
        existing_timestamps = set(
            StockPriceData.objects.filter(stock_symbol=stock_symbol)
            .values_list('timestamp', flat=True)
        )

        for _, row in dataframe.iterrows():
            timestamp_date = row['timestamp'].date()
            # Only add new records if the timestamp doesn't already exist
            if timestamp_date not in existing_timestamps:
                new_records.append(
                    StockPriceData(
                        stock_symbol=stock_symbol,
                        timestamp=timestamp_date,
                        open=row['open'],
                        high=row['high'],
                        low=row['low'],
                        close=row['close'],
                        adj_close=row.get('Adj Close', row['close']),  # Use 'Adj Close' if available
                        volume=row['volume']
                    )
                )
                #print(f"Prepared new data for {symbol} on {timestamp_date}")

        # Use bulk_create to insert all new records at once
        if new_records:
            StockPriceData.objects.bulk_create(new_records)
            record_msg =f"Inserted {len(new_records)} new records for {symbol}"
            print(record_msg)
        else:
            record_msg = f"No new records to insert for {symbol}"
            print(record_msg)
    return record_msg

def fetch_and_save_stock_data(symbols):
    """Fetch and save stock data for a list of symbols into the database."""
    periods = ['5y', 'ytd', '1y', '6mo','3mo','1mo','5d','1d']   
    #periods = ['5y', 'ytd', '1y', '6mo'] 
    #periods = ['6mo'] 
    
    record_msg = "No symbols processed."
    for symbol in symbols:
        print(f"Processing symbol: {symbol}")
        
        # Check the latest date in the database for this symbol
        stock_symbol = StockSymbolData.objects.filter(symbol=symbol).first()
        if stock_symbol:
            latest_entry = StockPriceData.objects.filter(stock_symbol=stock_symbol).order_by('-timestamp').first()
            start_date = latest_entry.timestamp + timedelta(days=1) if latest_entry else None
            print(f"DEBUG: start date for {symbol}: {start_date}")
        else:
            start_date = None
        
        # Fetch the stock data
        new_data = fetch_stock_data_with_fallback(symbol, periods, start_date=start_date)

        if new_data is None or new_data.empty:
            print(f"DEBUG: No data fetched for {symbol} in fetch_and_save_stock_data.")
            continue

        # Format the data
        if isinstance(new_data.columns, pd.MultiIndex):
            new_data.columns = new_data.columns.get_level_values(0)
            
        new_data.reset_index(inplace=True)
        new_data = new_data.rename(columns={
            "Date": "timestamp",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Adj Close": "adj_close",
            "Volume": "volume"
        })

        # Save the data into the database
        record_msg = save_stock_data_to_db(symbol, new_data) # it only returns records message
        
    return record_msg




from .models import StockSymbolData, StockPriceData

def fetch_data_for_symbols(symbols):
    """
    Fetch data for the specified symbols from the database.

    Args:
    symbols (list): List of symbols to fetch data for.

    Returns:
    dict: Dictionary with symbols as keys and querysets as values.
    """
    data = {}
    for symbol in symbols:
        # Find the StockSymbolData entry for the symbol
        stock_symbol = StockSymbolData.objects.filter(symbol=symbol).first()
        if stock_symbol:
            # Fetch related StockPriceData entries
            prices = StockPriceData.objects.filter(stock_symbol=stock_symbol).order_by('-timestamp')
            data[symbol] = prices
        else:
            data[symbol] = None  # No data available for this symbol
    return data






def fetch_news_for_date_range(ticker, date_range):
    """Fetch news data for a specific ticker and date range using yfinance."""
    stock = yf.Ticker(ticker)
    news = stock.news or []  # Default to empty list if news is None
    news_data = []

    for article in news:
        try:
            # Handle new yfinance news structure
            content = article.get('content', {})
            if not content:
                # Fallback for old structure if it still exists in some cases
                pub_time = article.get('providerPublishTime')
                if pub_time:
                    article_date = datetime.utcfromtimestamp(pub_time).date()
                    pub_time_str = datetime.utcfromtimestamp(pub_time).strftime('%Y-%m-%d %H:%M:%S')
                    title = article.get('title')
                    link = article.get('link')
                else:
                    continue
            else:
                # New structure
                pub_date_str = content.get('pubDate')
                if not pub_date_str:
                    continue
                # Parse ISO 8601 string: '2026-03-27T21:39:21Z'
                dt = datetime.strptime(pub_date_str, '%Y-%m-%dT%H:%M:%SZ')
                article_date = dt.date()
                pub_time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                title = content.get('title')
                link = content.get('canonicalUrl', {}).get('url') or content.get('clickThroughUrl', {}).get('url')

            # Check if article_date matches any date in date_range
            if any(single_date.date() == article_date for single_date in date_range):
                news_data.append({
                    "Date": article_date.strftime('%Y-%m-%d'),
                    "NewsTitle": title,
                    "NewsLink": link,
                    "providerPublishTime": pub_time_str
                })
        except Exception as e:
            print(f"DEBUG: Error parsing news article for {ticker}: {e}")
            continue
            
    return news_data




def check_news_each_day(ticker, date_range):
    """Check and update news data for a given ticker, storing in the NewsData model."""
    # Retrieve or create the NewsSymbolData object
    news_symbol, created = NewsSymbolData.objects.get_or_create(symbol=ticker)

    # Define default date range (last 90 days)
    start_date = datetime.today()
    end_date = start_date - timedelta(days=90)
    date_range = pd.date_range(start=end_date, end=start_date)

    # Get existing news data from the database for the given symbol and date range
    existing_data = NewsData.objects.filter(news_symbol=news_symbol, Date__in=date_range)

    # Find missing dates
    existing_dates = existing_data.values_list('Date', flat=True)
    missing_dates = [date for date in date_range if date.date() not in existing_dates]

    if missing_dates:
        # Fetch news for missing dates
        new_news = fetch_news_for_date_range(ticker, missing_dates)
        if new_news:
            # Convert the new news into NewsData objects
            news_objects = []
            for article in new_news:
                news_objects.append(
                    NewsData(
                        news_symbol=news_symbol,
                        Date=article['Date'],
                        NewsTitle=article['NewsTitle'],
                        NewsLink=article['NewsLink'],
                        providerPublishTime=make_aware(datetime.strptime(article['providerPublishTime'], '%Y-%m-%d %H:%M:%S'))
                    )
                )
            
            # Sort news_objects by providerPublishTime to save the latest news first
            news_objects.sort(key=lambda x: x.providerPublishTime, reverse=True)
            
            # Bulk create news entries in the database
            NewsData.objects.bulk_create(news_objects)
            print(f"Successfully added news for {ticker} from missing dates.")
        else:
            print(f"No new news found for {ticker}.")
    else:
        print(f"All news for {ticker} is up-to-date.")
    
    # Return the updated data sorted by providerPublishTime (latest first)
    return NewsData.objects.filter(news_symbol=news_symbol, Date__in=date_range).order_by('-providerPublishTime')



def get_news_for_symbol(symbol: str, date_range: pd.DatetimeIndex) -> Tuple[List[str], List[str], List[str]]:
    """
    Fetch news data (titles, links, and publish times) for a given symbol and date range.

    Args:
        symbol (str): The stock symbol to fetch news for.
        date_range (pd.DatetimeIndex): The date range to filter news.

    Returns:
        Tuple[List[str], List[str], List[str]]: 
            A tuple containing three lists:
            - News titles
            - News links
            - Provider publish times as strings
    """
    try:
        # Get the symbol data
        news_symbol = NewsSymbolData.objects.get(symbol=symbol)
        
        # Convert date range to a list of dates for filtering
        date_list = [date.date() for date in date_range]
        
        # Query news data for the symbol within the date range
        news_data = NewsData.objects.filter(news_symbol=news_symbol, Date__in=date_list).order_by('-providerPublishTime')
        
        # Extract information from the queried data
        titles = [news.NewsTitle for news in news_data]
        links = [news.NewsLink for news in news_data]
        publish_times = [news.providerPublishTime.strftime('%Y-%m-%d %H:%M:%S') for news in news_data]
        
        return titles, links, publish_times

    except NewsSymbolData.DoesNotExist:
        print(f"Symbol '{symbol}' not found in the database.")
        return [], [], []
    