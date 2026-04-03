

from datetime import datetime, timedelta
import pandas as pd
from .stock_data import check_news_each_day,fetch_and_save_stock_data 
from .models import DayStockSymbolInfo,StockSymbolInfo,StockSymbolData,StockPriceData,ThreeMonthsShortVolume
from django.db import transaction
import yfinance as yf
import math


def update_news_for_tickers(ticker_lists):

    try:
        # Define the date range (last 90 days)
        start_date = datetime.today()
        end_date = start_date - timedelta(days=90)
        date_range = pd.date_range(start=end_date, end=start_date)

        # To store news for each symbol
        all_news_data = {}

        for ticker in ticker_lists:
            # Fetch news data for each symbol
            news_data = check_news_each_day(ticker, date_range)
            # Prepare the data for JSON response
            news_list = []
            for news_item in news_data:
                news_list.append({
                    "Date": news_item.Date.strftime('%Y-%m-%d'),
                    "NewsTitle": news_item.NewsTitle,
                    "NewsLink": news_item.NewsLink,
                    "providerPublishTime": news_item.providerPublishTime.strftime('%Y-%m-%d %H:%M:%S')
                })
            
            # Store data for this ticker
            all_news_data[ticker] = news_list

        # Return response in the desired format
        response_data = {
            "message": "Watchlist news data fetched successfully.",
            "updated_symbols": list(all_news_data.keys())
        }
        status = 200

    except Exception as e:
        # Handle errors
        response_data = {
            "message": "An error occurred while fetching watchlist news data.",
            "error": str(e)
        }
        status = 500

    return response_data, status

def safe_number(value, default=None):
    """
    Ensures the value is a valid number (float), otherwise returns the default.
    Handles NaN values explicitly.
    """
    try:
        number = float(value)
        if math.isnan(number):  # Check for NaN
            return default
        return number
    except (ValueError, TypeError):
        return default



def parse_date(value):
    """Convert Unix timestamp, ISO string, or datetime to a valid date or return a default date."""
    from datetime import datetime, date
    if isinstance(value, (int, float)):  # Handle Unix timestamp
        try:
            return datetime.utcfromtimestamp(int(value)).date()
        except (ValueError, OSError):
            print(f"Invalid Unix timestamp: {value}")
            return date.min  # Default to the earliest valid date
    elif isinstance(value, str):  # Handle ISO 8601 string
        try:
            return datetime.fromisoformat(value).date()
        except ValueError:
            print(f"Invalid date string: {value}")
            return date.min
    elif isinstance(value, datetime):  # Already a datetime object
        return value.date()
    elif value is None:
        return date.min  # Default to the earliest valid date
    else:
        print(f"Unsupported date format: {value}")
        return date.min


def update_tickers_day_stock_info(ticker_lists):
 
 
    updated_symbols = []
    created_symbols = []
    stocks_to_create = []
    stocks_to_update = []

    try:
        for symbol in ticker_lists:
            stock_info = yf.Ticker(symbol)
            summary_info = stock_info.info
            print(f"Updating Day Info for Ticker: {symbol}")

            # Fetch or create stock entry
            stock_entry = DayStockSymbolInfo.objects.filter(symbol=symbol).first()

            if not stock_entry:
                # Create a new stock entry
                stock_entry = DayStockSymbolInfo(
                    symbol=symbol,
                    company_name=summary_info.get('longName', ''),
                    previousClose=safe_number(summary_info.get('previousClose')),
                    open=safe_number(summary_info.get('open')),
                    currentPrice=safe_number(summary_info.get('currentPrice')),
                    dayLow=safe_number(summary_info.get('dayLow')),
                    dayHigh=safe_number(summary_info.get('dayHigh')),
                    volume=safe_number(summary_info.get('volume')),
                    averageVolume3months=safe_number(summary_info.get('averageVolume')),
                    averageVolume10days=safe_number(summary_info.get('averageVolume10days')),
                    marketCap=safe_number(summary_info.get('marketCap')),
                )
                stocks_to_create.append(stock_entry)
                created_symbols.append(symbol)
            else:
                # Update existing stock entry
                stock_entry.company_name = summary_info.get('longName', stock_entry.company_name)
                stock_entry.previousClose = safe_number(summary_info.get('previousClose')) or stock_entry.previousClose
                stock_entry.open = safe_number(summary_info.get('open')) or stock_entry.open
                stock_entry.currentPrice = safe_number(summary_info.get('currentPrice')) or stock_entry.currentPrice
                stock_entry.dayLow = safe_number(summary_info.get('dayLow')) or stock_entry.dayLow
                stock_entry.dayHigh = safe_number(summary_info.get('dayHigh')) or stock_entry.dayHigh
                stock_entry.volume = safe_number(summary_info.get('volume')) or stock_entry.volume
                stock_entry.averageVolume3months = safe_number(summary_info.get('averageVolume')) or stock_entry.averageVolume3months
                stock_entry.averageVolume10days = safe_number(summary_info.get('averageVolume10days')) or stock_entry.averageVolume10days
                stock_entry.marketCap = safe_number(summary_info.get('marketCap')) or stock_entry.marketCap

                stocks_to_update.append(stock_entry)
                updated_symbols.append(symbol)

        # Bulk create and update
        DayStockSymbolInfo.objects.bulk_create(stocks_to_create, ignore_conflicts=True)
        DayStockSymbolInfo.objects.bulk_update(stocks_to_update, fields=[
            'company_name','previousClose', 'open', 'currentPrice', 'dayLow', 'dayHigh', 'volume',
            'averageVolume3months', 'averageVolume10days', 'marketCap'
        ])

        # Prepare response
        response_data = {
            "message": "Stock info data fetched and saved successfully.",
            "updated_symbols_count": len(updated_symbols),
            "created_symbols_count": len(created_symbols),
            "updated_symbols": updated_symbols,
            "created_symbols": created_symbols,
        }
        status = 200

    except Exception as e:
        response_data = {
            "message": "An error occurred while fetching stock data.",
            "error": str(e)
        }
        status = 500

    return response_data, status

def update_tickers_stock_info(ticker_lists):

    updated_symbols = []
    created_symbols = []
    stocks_to_create = []
    stocks_to_update = []



    try:
        # Loop through symbols and fetch/update stock data
        for symbol in ticker_lists:
            stock_info = yf.Ticker(symbol)
            summary_info = stock_info.info
            print(f"updating: {symbol}")
            # Financial data
            income_statement_info = stock_info.financials
            balance_sheet_info = stock_info.balance_sheet

            total_revenue = safe_number(
                income_statement_info.loc['Total Revenue'].iloc[0]) if 'Total Revenue' in income_statement_info.index else None
            net_income = safe_number(
                income_statement_info.loc['Net Income'].iloc[0]) if 'Net Income' in income_statement_info.index else None

            total_assets = safe_number(
                balance_sheet_info.loc['Total Assets'].iloc[0]) if 'Total Assets' in balance_sheet_info.index else None
            total_liabilities = safe_number(
                balance_sheet_info.loc['Total Liabilities Net Minority Interest'].iloc[0]) if 'Total Liabilities Net Minority Interest' in balance_sheet_info.index else None
            total_equity = safe_number(
                balance_sheet_info.loc['Stockholder Equity'].iloc[0]) if 'Stockholder Equity' in balance_sheet_info.index else None

            # Fetch or create stock entry
            stock_entry = StockSymbolInfo.objects.filter(symbol=symbol).first()

            if not stock_entry:
                # Create a new stock entry
                stock_entry = StockSymbolInfo(
                    symbol=symbol,
                    company_name=summary_info.get('longName', ''),
                    volume=safe_number(summary_info.get('volume')),
                    averageVolume3months=safe_number(summary_info.get('averageVolume')),
                    averageVolume10days=safe_number(summary_info.get('averageVolume10days')),
                    marketCap=safe_number(summary_info.get('marketCap')),
                    fiftyTwoWeekLow=safe_number(summary_info.get('fiftyTwoWeekLow')),
                    fiftyTwoWeekHigh=safe_number(summary_info.get('fiftyTwoWeekHigh')),
                    fiftyDayAverage=safe_number(summary_info.get('fiftyDayAverage')),
                    floatShares=safe_number(summary_info.get('floatShares')),
                    sharesOutstanding=safe_number(summary_info.get('sharesOutstanding')),
                    sharesShort=safe_number(summary_info.get('sharesShort')),
                    sharesShortPriorMonth=safe_number(summary_info.get('sharesShortPriorMonth')),
                    sharesShortPreviousMonthDate=parse_date(summary_info.get('sharesShortPreviousMonthDate')),
                    dateShortInterest=parse_date(summary_info.get('dateShortInterest')),
                    shortPercentOfFloat=safe_number(summary_info.get('shortPercentOfFloat')),
                    heldPercentInsiders=safe_number(summary_info.get('heldPercentInsiders')),
                    heldPercentInstitutions=safe_number(summary_info.get('heldPercentInstitutions')),
                    total_revenue=total_revenue,
                    net_income=net_income,
                    total_assets=total_assets,
                    total_liabilities=total_liabilities,
                    total_equity=total_equity
                )
                stocks_to_create.append(stock_entry)
                created_symbols.append(symbol)
            else:
                # Update the existing stock entry
                stock_entry.company_name = summary_info.get('longName', stock_entry.company_name)
                stock_entry.volume = safe_number(summary_info.get('volume')) or stock_entry.volume
                stock_entry.averageVolume3months = safe_number(summary_info.get('averageVolume')) or stock_entry.averageVolume3months
                stock_entry.averageVolume10days = safe_number(summary_info.get('averageVolume10days')) or stock_entry.averageVolume10days
                stock_entry.marketCap = safe_number(summary_info.get('marketCap')) or stock_entry.marketCap
                stock_entry.fiftyTwoWeekLow = safe_number(summary_info.get('fiftyTwoWeekLow')) or stock_entry.fiftyTwoWeekLow
                stock_entry.fiftyTwoWeekHigh = safe_number(summary_info.get('fiftyTwoWeekHigh')) or stock_entry.fiftyTwoWeekHigh
                stock_entry.fiftyDayAverage = safe_number(summary_info.get('fiftyDayAverage')) or stock_entry.fiftyDayAverage
                stock_entry.floatShares = safe_number(summary_info.get('floatShares')) or stock_entry.floatShares
                stock_entry.sharesOutstanding = safe_number(summary_info.get('sharesOutstanding')) or stock_entry.sharesOutstanding
                stock_entry.sharesShort = safe_number(summary_info.get('sharesShort')) or stock_entry.sharesShort
                stock_entry.sharesShortPriorMonth = safe_number(summary_info.get('sharesShortPriorMonth')) or stock_entry.sharesShortPriorMonth
                stock_entry.sharesShortPreviousMonthDate = parse_date(
                    summary_info.get('sharesShortPreviousMonthDate')) or stock_entry.sharesShortPreviousMonthDate
                stock_entry.dateShortInterest = parse_date(
                    summary_info.get('dateShortInterest')) or stock_entry.dateShortInterest
                stock_entry.shortPercentOfFloat = safe_number(
                    summary_info.get('shortPercentOfFloat')) or stock_entry.shortPercentOfFloat
                stock_entry.heldPercentInsiders = safe_number(
                    summary_info.get('heldPercentInsiders')) or stock_entry.heldPercentInsiders
                stock_entry.heldPercentInstitutions = safe_number(
                    summary_info.get('heldPercentInstitutions')) or stock_entry.heldPercentInstitutions
                stock_entry.total_revenue = total_revenue or stock_entry.total_revenue
                stock_entry.net_income = net_income or stock_entry.net_income
                stock_entry.total_assets = total_assets or stock_entry.total_assets
                stock_entry.total_liabilities = total_liabilities or stock_entry.total_liabilities
                stock_entry.total_equity = total_equity or stock_entry.total_equity

                stocks_to_update.append(stock_entry)
                updated_symbols.append(symbol)

            # Handle splits
            splits = stock_info.splits
            if not splits.empty:
                stock_entry.lastSplitDate = parse_date(splits.index[-1].timestamp() if splits.index[-1] else None)
                stock_entry.lastSplitFactor = splits.iloc[-1]

        # Bulk create and update
        StockSymbolInfo.objects.bulk_create(stocks_to_create, ignore_conflicts=True)
        StockSymbolInfo.objects.bulk_update(stocks_to_update, fields=[
            'company_name','volume', 'averageVolume3months', 'averageVolume10days', 'marketCap', 'fiftyTwoWeekLow',
            'fiftyTwoWeekHigh', 'fiftyDayAverage', 'floatShares', 'sharesOutstanding', 'sharesShort',
            'sharesShortPriorMonth', 'sharesShortPreviousMonthDate', 'dateShortInterest', 'shortPercentOfFloat',
            'heldPercentInsiders', 'heldPercentInstitutions', 'lastSplitDate', 'lastSplitFactor', 'total_revenue',
            'net_income', 'total_assets', 'total_liabilities', 'total_equity'
        ])

        # Prepare response
        response_data = {
            "message": "Stock info data fetched and saved successfully.",
            "updated_symbols_count": len(updated_symbols),
            "created_symbols_count": len(created_symbols),
            "updated_symbols": updated_symbols,
            "created_symbols": created_symbols
            #"query_symbols": watchlist_symbols
        }
        status = 200

    except Exception as e:
        response_data = {
            "message": "An error occurred while fetching stock data.",
            "error": str(e)
        }
        status = 500

    return response_data, status

def update_and_merge_missing_short_volume_data(ticker_lists):
    results = []

    try:
        for stock_symbol in ticker_lists:
            # Get the stock symbol object
            stock_symbol_obj = StockSymbolData.objects.filter(symbol=stock_symbol).first()
            if not stock_symbol_obj:
                results.append({'symbol': stock_symbol, 'message': 'Stock symbol not found'})
                continue

            # Fetch stock price data for the given symbol
            stock_price_data = StockPriceData.objects.filter(
                stock_symbol=stock_symbol_obj,
                ShortVolume__isnull=True  # Only update records with missing ShortVolume
            )

            # Fetch all relevant short volume data for the stock symbol
            short_volume_data = ThreeMonthsShortVolume.objects.filter(Symbol=stock_symbol)

            if not stock_price_data.exists() or not short_volume_data.exists():
                results.append({'symbol': stock_symbol, 'message': 'No missing data to update or no relevant short volume data found'})
                continue

            # Convert short volume data to DataFrame
            short_volume_df = pd.DataFrame(list(short_volume_data.values()))

            # Ensure Date columns are timezone-naive UTC
            short_volume_df['Date'] = pd.to_datetime(short_volume_df['Date']).dt.tz_localize(None)

            # Prepare a DataFrame for stock price data
            stock_price_df = pd.DataFrame(list(stock_price_data.values()))
            stock_price_df['timestamp'] = pd.to_datetime(stock_price_df['timestamp'])

            # Merge the short volume data into the stock price data
            merged_df = stock_price_df.merge(
                short_volume_df[['Date', 'ShortVolume', 'ShortExemptVolume']],
                left_on='timestamp', right_on='Date',
                how='left'
            )

            # Filter only the rows where ShortVolume or ShortExemptVolume needs updating
            merged_df = merged_df.loc[
                merged_df['ShortVolume_y'].notnull(),  # Check if there's matching short volume data
            ]

            # Prepare data for bulk update
            updated_records = []
            for _, row in merged_df.iterrows():
                updated_records.append(
                    StockPriceData(
                        id=row['id'],  # Use existing ID to update
                        stock_symbol=stock_symbol_obj,
                        timestamp=row['timestamp'],
                        open=row['open'],
                        high=row['high'],
                        low=row['low'],
                        close=row['close'],
                        adj_close=row['adj_close'],
                        volume=row['volume'],
                        ShortVolume=row['ShortVolume_y'],  # Use merged ShortVolume
                        ShortExemptVolume=row['ShortExemptVolume_y']  # Use merged ShortExemptVolume
                    )
                )

            # Bulk update records
            with transaction.atomic():
                StockPriceData.objects.bulk_update(
                    updated_records,
                    ['ShortVolume', 'ShortExemptVolume']
                )

            results.append({'symbol': stock_symbol, 'message': 'Missing short volume data successfully updated'})

        response_data = {
            "results": results
        }
        status = 200
    except Exception as e:
        # Handle any errors
        response_data = {
            "message": "An error occurred while processing stock data.",
            "error": str(e),
            "results": results
        }
        status = 500

    return response_data, status


def update_tickers_stock_data(ticker_lists): 

    try:
        # Call the function to fetch and save stock data
        fetch_and_save_stock_data(ticker_lists)

        # Retrieve the symbols that were updated or created
        updated_symbols = StockSymbolData.objects.filter(symbol__in=ticker_lists)
        response_data = {
            "message": "Watched List Symbol Stock data fetched and saved successfully.",
            "updated_symbols": [symbol.symbol for symbol in updated_symbols]
        }
        status = 200
    except Exception as e:
        # Handle any errors
        response_data = {
            "message": "An error occurred while fetching stock data.",
            "error": str(e)
        }
        status = 500

    return response_data ,status
