from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Max, Avg
from django.utils import timezone
from django.core.cache import cache
import re

from .models import ThreeMonthsShortVolume, ThreeMonthsRegSHO
from .forms import FileUploadForm

import pandas as pd
import requests
from io import StringIO
from datetime import datetime, timedelta
import pandas_market_calendars as mcal
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor
import logging
from django.http import JsonResponse
from .models import StockSymbolData, StockPriceData
from .stock_data import fetch_and_save_stock_data, fetch_data_for_symbols
from .stock_charts import generateCharts
from .stock_charts_view import handle_cached_charts_view

from plotly.subplots import make_subplots
import plotly.graph_objects as go
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from .models import NewsSymbolData, NewsData
from datetime import datetime, timedelta
import pandas as pd
from .stock_data import check_news_each_day
from .models import TickerSplit

import pandas as pd
from datetime import datetime, timedelta
from django.http import JsonResponse
from .stock_data import get_news_for_symbol

from .utils import stock_charts, single_stock_charts,stock_charts_hist_today
from .yscreener import y_most_active, y_tranding, y_top_gainers, y_top_losers

from .stock_day_info_second import stock_day_info

from django.contrib.auth.decorators import login_required


def get_non_healthcare_bought_tickers(user):
    """
    Fetches all "Buy" symbols for a given user excluding "Healthcare" sector.
    The symbols are ordered by date (latest first) and duplicates are removed while maintaining order.

    Args:
        user: The user object for which to fetch the tickers.

    Returns:
        list: A list of non-Healthcare "Buy" tickers for the user, or an empty list if the user is not authenticated.
    """
    if user.is_authenticated:
        non_healthcare_bought_tickers = BuyNSell.objects.filter(
            user=user, transaction_type="B"
        ).exclude(sector="Healthcare").order_by('-date').values_list('symbol', flat=True)
        # Remove duplicates while maintaining order
        non_healthcare_bought_tickers_list = list(dict.fromkeys(non_healthcare_bought_tickers))
    else:
        non_healthcare_bought_tickers_list = []  # No symbols if the user is not authenticated

    return non_healthcare_bought_tickers_list
def get_healthcare_bought_tickers(user):
    """
    Fetches all "Buy" symbols for a given user "Healthcare" sector.
    The symbols are ordered by date (latest first) and duplicates are removed while maintaining order.

    Args:
        user: The user object for which to fetch the tickers.

    Returns:
        list: A list of non-Healthcare "Buy" tickers for the user, or an empty list if the user is not authenticated.
    """
    # Fetch all "Healthcare" symbols for the logged-in user with transaction_type "B", ordered by date (latest first), and remove duplicates
    if  user.is_authenticated:
        healthcare_bought_tickers = BuyNSell.objects.filter(
            user=user, sector="Healthcare", transaction_type="B"
        ).order_by('-date').values_list('symbol', flat=True)
        # Remove duplicates while maintaining order
        healthcare_bought_tickers_list = list(dict.fromkeys(healthcare_bought_tickers))
    else:
        healthcare_bought_tickers_list = []  # No symbols if the user is not authenticated
    return healthcare_bought_tickers_list

def index(request):
    # Fetch all watch lists from the database
    #all_watch_lists = WatchList.objects.all()
    if request.user.is_authenticated:
        all_watch_lists = WatchList.objects.filter(user=request.user).order_by('order')
    else:
        all_watch_lists = []
    
    # Get the selected watch list name from the request (default to 'next_earning')
    #watch_list_name = request.GET.get('watch_list', 'next_earning')
    
    # Filter to get the specific watch list based on the provided name
    #watch_list = WatchList.objects.filter(name=watch_list_name).first()

    # Print for debugging
    #print(watch_list)
    #print(all_watch_lists)
    def format_big_number(number):
        return format(number, ",") if number is not None else None
            # Utility function to format percentages
    def format_percentage(value):
        return f"{value * 100:.1f}" if value is not None else 0
    

            


    # Filter stocks based on user's watchlist symbols
    stocks = StockSymbolInfo.objects.all().values(
        'symbol', 'company_name','volume', 'averageVolume3months', 'averageVolume10days',
        'marketCap', 'fiftyTwoWeekLow', 'fiftyTwoWeekHigh', 'fiftyDayAverage',
        'floatShares', 'sharesOutstanding', 'sharesShort', 'sharesShortPriorMonth',
        'sharesShortPreviousMonthDate', 'dateShortInterest', 'shortPercentOfFloat',
        'heldPercentInsiders', 'heldPercentInstitutions', 'lastSplitFactor',
        'lastSplitDate', 'total_revenue', 'net_income', 'total_assets', 'total_liabilities', 'total_equity'
    )

    # Format the stock data for display
    formatted_stocks = []
    for stock in stocks:
        last_split_factor = stock['lastSplitFactor']

        # Format lastSplitFactor into "1:x" or "x:1"
        if last_split_factor is not None:
            if last_split_factor < 1:
                last_split_factor = f"1:{int(1 / last_split_factor)}"
            else:
                last_split_factor = f"{int(last_split_factor)}:1"

        # Add formatted stock data
        formatted_stocks.append({
            'symbol': stock['symbol'],
            'company_name': stock['company_name'],
            'volume': format_big_number(stock['volume']),
            'averageVolume3months': format_big_number(stock['averageVolume3months']),
            'averageVolume10days': format_big_number(stock['averageVolume10days']),
            'marketCap': format_big_number(stock['marketCap']),
            'fiftyTwoWeekLow': format_big_number(stock['fiftyTwoWeekLow']),
            'fiftyTwoWeekHigh': format_big_number(stock['fiftyTwoWeekHigh']),
            'fiftyDayAverage': format_big_number(stock['fiftyDayAverage']),
            'floatShares': format_big_number(stock['floatShares']),
            'sharesOutstanding': format_big_number(stock['sharesOutstanding']),
            'sharesShort': format_big_number(stock['sharesShort']),
            'sharesShortPriorMonth': format_big_number(stock['sharesShortPriorMonth']),
            'sharesShortPreviousMonthDate': stock['sharesShortPreviousMonthDate'],  # Dates don't need formatting
            'dateShortInterest': stock['dateShortInterest'],  # Dates don't need formatting
            
            'shortPercentOfFloat': format_percentage(stock['shortPercentOfFloat']),
            'heldPercentInsiders': format_percentage(stock['heldPercentInsiders']),
            'heldPercentInstitutions': format_percentage(stock['heldPercentInstitutions']),

            'lastSplitFactor': last_split_factor,
            'lastSplitDate': stock['lastSplitDate'],  # Dates don't need formatting
            'total_revenue': format_big_number(stock['total_revenue']),
            'net_income': format_big_number(stock['net_income']),
            'total_assets': format_big_number(stock['total_assets']),
            'total_liabilities': format_big_number(stock['total_liabilities']),
            'total_equity': format_big_number(stock['total_equity']),
        })

    non_healthcare_bought_tickers_list          = get_non_healthcare_bought_tickers(request.user)
    healthcare_bought_tickers_list              = get_healthcare_bought_tickers(request.user)

    # Pass all watch lists and the selected watch list to the template
    return render(request, 'auth-page.html', {
        'all_watch_lists': all_watch_lists,
        'length_of_non_healthcare_bought_tickers': len(non_healthcare_bought_tickers_list),
        'length_of_healthcare_bought_tickers_list': len(healthcare_bought_tickers_list),
        'stocks': formatted_stocks
        
    })

def charts_page(request):
    # Fetch all watch lists from the database
    #all_watch_lists = WatchList.objects.all()
    if request.user.is_authenticated:
        all_watch_lists = WatchList.objects.filter(user=request.user).order_by('order')
    else:
        all_watch_lists = []
    
    # Pass all watch lists and the selected watch list to the template
    return render(request, 'charts-home.html', {
        'all_watch_lists': all_watch_lists,
        
    })

def daily_info_page(request):
    if request.user.is_authenticated:
        # Fetch user watchlists
        user_watchlists = WatchList.objects.filter(user=request.user)

        # Get all symbols from the user's watchlists
        watchlist_symbols = WatchListSymbol.objects.filter(watch_list__in=user_watchlists).values_list('symbol', flat=True)

        formatted_day_stocks = stock_day_info(watchlist_symbols)
        all_watch_lists = WatchList.objects.filter(user=request.user).order_by('order')
    else:
        formatted_day_stocks = []
        all_watch_lists = []

    msg = 'Watch Lists'
    # Pass all watch lists and the selected watch list to the template
    return render(request, 'daily-info-home.html', {
        'day_stocks': formatted_day_stocks,
        'all_watch_lists': all_watch_lists,
        'nav_text': msg
    })
def get_previous_trading_day(date):
    """Return the last trading day before a given date."""
    nasdaq = mcal.get_calendar('NASDAQ')
    # Look back up to 10 days to find the last trading day
    valid_days = nasdaq.valid_days(start_date=date - timedelta(days=10), end_date=date - timedelta(days=1))
    
    if not valid_days.empty:
        return valid_days.max().date()  # Returns the last valid trading day before the given date
    
    # If no valid trading days are found in the range, this is a fallback.
    # It should not occur in practice with a 10-day buffer.
    return date.date() - timedelta(days=1)
from datetime import datetime
from django.db import transaction
from datetime import timedelta
import pandas_market_calendars as mcal

from datetime import datetime

def check_stock_data_and_process_symbols(symbols):
    """Check whether each symbol exists, and process accordingly."""
    # Current date
    today = datetime.today().date()

    # Go through each symbol
    for symbol in symbols:
        print(f"Checking symbol: {symbol}")
        
        # Check if symbol exists in StockSymbolData
        stock_symbol = StockSymbolData.objects.filter(symbol=symbol).first()

        if stock_symbol:
            # If symbol exists, check the latest date
            latest_entry = StockPriceData.objects.filter(stock_symbol=stock_symbol).order_by('-timestamp').first()

            if latest_entry:
                # Get the last timestamp (latest entry) and check if it matches today's date or previous trading day
                latest_timestamp = latest_entry.timestamp
                previous_trading_day = get_previous_trading_day(today)

                # If the latest timestamp does not match today or previous trading day, fetch and save new data
                if latest_timestamp != today and latest_timestamp != previous_trading_day:
                    print(f"Data for {symbol} is outdated, fetching and saving new data.")
                    fetch_and_save_stock_data([symbol])
                else:
                    print(f"Data for {symbol} is up to date (matches today or previous trading day). No action needed.")

            else:
                # If there's no data for this symbol in StockPriceData, fetch and save new data
                print(f"No data for {symbol}, fetching and saving new data.")
                fetch_and_save_stock_data([symbol])

        else:
            # If the symbol doesn't exist in StockSymbolData, fetch and save new data
            print(f"Symbol {symbol} does not exist in the database, fetching and saving new data.")
            fetch_and_save_stock_data([symbol])
from django.http import JsonResponse
import os
import json

def stock_data_tickers():
    # Construct the file path
    file_path = os.path.join(settings.BASE_DIR, "data", "symbols.json")
    
    try:
        # Attempt to open and read the JSON file
        with open(file_path, "r") as f:
            tickers = json.load(f)  # Parse JSON data into a Python list
            # Sort the tickers alphabetically before returning

            sorted_tickers = sorted(tickers)  

        return sorted_tickers  # Return tickers if successful
    
    except FileNotFoundError:
        # Return a dictionary indicating the file was not found
        return {"error": f"File not found at path: {file_path}"}
    except json.JSONDecodeError:
        # Return a dictionary if the file content is invalid
        return {"error": "Invalid JSON content in file."}
    
def get_current_regsho_symbols():
        # Get the latest date
    latest_date = ThreeMonthsRegSHO.objects.aggregate(Max('Date'))['Date__max']

    # Get all symbols with the latest date
    if latest_date:
        latest_symbols = list(
            ThreeMonthsRegSHO.objects.filter(Date=latest_date).values_list('Symbol', flat=True)
        )
        #print(latest_symbols)
    else:
        print("No data available.")
    
    # Filter the list to include only valid ticker symbols
    valid_symbols = [symbol for symbol in latest_symbols if is_valid_symbol(symbol)]
    return valid_symbols
    
def merge_watchlist_regsho_symbols():
        # Assuming you have these three lists
    valid_symbols = get_current_regsho_symbols()
    reg_sho_remove_symbols = reg_sho_remove_list()  # Call the function to get this list
    # Step 1: Get all watch lists for the specific user
    #user_watch_lists = WatchList.objects.filter(user=user)

    # Step 2: Get all the symbols associated with those watch lists
    #watchlist_symbols = WatchListSymbol.objects.filter(watch_list__in=user_watch_lists).values_list('symbol', flat=True)
    watchlist_symbols = WatchListSymbol.objects.all().values_list('symbol', flat=True)

    # Step 3: Convert to list if needed
    watchlist_symbols_list = list(watchlist_symbols)

    # Combine all three lists and ensure uniqueness using a set
    combined_unique_symbols = set(valid_symbols + reg_sho_remove_symbols + watchlist_symbols_list)

    # If you need it back as a list (optional)
    combined_unique_symbols_list = list(combined_unique_symbols)
    
    return combined_unique_symbols_list, watchlist_symbols_list

def show_agregate_watchlist_regSho_tickers(request):
    # Get tickers
    user = request.user
    tickers , watchlist_symbols_list = merge_watchlist_regsho_symbols()
    # Now `combined_unique_symbols_list` contains unique symbols from all three lists

    # Check if tickers is a dictionary
    if isinstance(tickers, dict):
        # Return the dictionary as a JSON response
        return JsonResponse(tickers)
    else:
        # Return the list as a JSON response with safe=False
        return JsonResponse(tickers, safe=False)

from django.http import JsonResponse


def top_sv_symbol_lists():
        #------------------Top 20 short volume list------------------#
    latest_date = ThreeMonthsShortVolume.objects.aggregate(latest=Max('Date'))['latest']
    # Calculate the start date (5 days before the latest date)
    consecutive_date = latest_date - timedelta(days=0)
    # Filter data for the last 5 days
    recent_volumes = ThreeMonthsShortVolume.objects.filter(Date__range=[consecutive_date, latest_date])
    # Calculate the average short volume for each symbol across these 5 days
    symbol_averages = recent_volumes.values('Symbol').annotate(avg_short_volume=Avg('ShortVolume')).order_by('-avg_short_volume')
    # Optionally, limit to the top 20 symbols based on average short volume
    top_symbols = symbol_averages[:20]
    # Create a list of only the symbols, preserving the order
    sv_symbols = [entry['Symbol'] for entry in top_symbols]
    #------------------Top 20 short volume list------------------#
    return sv_symbols

def regsho_watchlist_sv_tickers_not_in_stock_symbol_data(user):
    # Get tickers
    # 1. Get all symbols from StockSymbolData
    all_symbols = StockSymbolData.objects.values_list('symbol', flat=True)

    # 2. Retrieve the tickers list (assuming this function is available and provides the list of tickers)
    tickers, watchlist_symbols_list = merge_watchlist_regsho_symbols()


    sv_symbols = top_sv_symbol_lists()
    # 4. Convert to sets for easier comparison
    set_all_symbols = set(all_symbols)
    set_tickers = set(tickers)
    set_sv_symbols = set(sv_symbols)

    # 5. Check which tickers are missing from StockSymbolData
    missing_tickers = set_tickers - set_all_symbols
    sv_missing_tickers_in_stock_data = set_sv_symbols - set_all_symbols

    # Convert the sets of missing tickers to lists for JSON serialization
    missing_tickers_list = list(missing_tickers)
    sv_missing_tickers_list = list(sv_missing_tickers_in_stock_data)

    # Using set intersection to find common tickers between missing_tickers and watchlist_symbols_list
    set_watchlist_symbols = set(watchlist_symbols_list)
    watchlist_missing_in_stock_data = list(set_watchlist_symbols & missing_tickers)

    # Return the lists as a JSON response with safe=False
    return missing_tickers_list, watchlist_missing_in_stock_data, sv_missing_tickers_list


def show_regsho_watchlist_sv_tickers_not_in_stock_symbol_data(request):
    # Get tickers
    user = request.user
    missing_tickers_list,watchlist_missing_in_stock_data,sv_missing_tickers_list = regsho_watchlist_sv_tickers_not_in_stock_symbol_data(user)

    # Return the list as a JSON response with safe=False
    return JsonResponse(missing_tickers_list, safe=False)

   
def fetch_short_volume_data(date):
    """Fetch short volume data for a single date and return as a DataFrame."""
    base_url = "https://cdn.finra.org/equity/regsho/daily/CNMSshvol{}.txt"
    formatted_date = date.strftime("%Y%m%d")
    url = base_url.format(formatted_date)
    response = requests.get(url)

    if response.status_code == 200:
        data = StringIO(response.text)
        df = pd.read_csv(data, delimiter='|', on_bad_lines='skip')
        df['date'] = date
        return df
    return pd.DataFrame()  # Return empty DataFrame if fetch fails

def save_short_volume_data_old(df):
    """Save fetched short volume data to the database."""
    if not df.empty:
        models_to_create = []
        for _, row in df.iterrows():
            models_to_create.append(ThreeMonthsShortVolume(
                Date=row['date'],
                Symbol=row['Symbol'],
                ShortVolume=row.get('ShortVolume', 0),
                ShortExemptVolume=row.get('ShortExemptVolume', 0),
                TotalVolume=row.get('TotalVolume', 0),
                Market=row.get('Market', '')
            ))
        ThreeMonthsShortVolume.objects.bulk_create(models_to_create, ignore_conflicts=True)
        
def save_short_volume_data(df):
    """Save fetched short volume data to the database."""
    if not df.empty:
        # Replace NaN values with appropriate defaults
        df.fillna({
            'ShortVolume': 0,
            'ShortExemptVolume': 0,
            'TotalVolume': 0,
            'Market': ''
        }, inplace=True)
        
        models_to_create = []
        for _, row in df.iterrows():
            models_to_create.append(ThreeMonthsShortVolume(
                Date=row['date'],
                Symbol=row['Symbol'],
                ShortVolume=row['ShortVolume'],
                ShortExemptVolume=row['ShortExemptVolume'],
                TotalVolume=row['TotalVolume'],
                Market=row['Market']
            ))
        ThreeMonthsShortVolume.objects.bulk_create(models_to_create, ignore_conflicts=True)

@login_required
def display_three_months_short_volume_data(request, start_date_str):
    start_date = datetime.strptime(start_date_str, "%Y%m%d")
    start_date = get_previous_trading_day(start_date)
    end_date = start_date - timedelta(days=89)  # Last 90 trading days

    # Get all existing dates in the database for the range
    existing_dates = set(
        ThreeMonthsShortVolume.objects.filter(Date__range=[end_date, start_date]).values_list('Date', flat=True)
    )

    # Generate a list of missing dates (business days only)
    date_range = pd.date_range(end_date, start_date, freq='B')
    missing_dates = [single_date for single_date in date_range if single_date.date() not in existing_dates]

    if missing_dates:
        with ThreadPoolExecutor(max_workers=5) as executor:
            results = executor.map(fetch_short_volume_data, missing_dates)
        for result in results:
            save_short_volume_data(result)

    # Fetch and display the data in the range
    data = ThreeMonthsShortVolume.objects.filter(Date__range=[end_date, start_date]).order_by('-Date')[:30]

    if request.user.is_authenticated:
        all_watch_lists = WatchList.objects.filter(user=request.user).order_by('order')
    else:
        all_watch_lists = []

    return render(request, 'months-short-volume-data.html', {'data': data,'all_watch_lists': all_watch_lists})




@login_required
def upload_short_volume_file(request):
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file_in_memory = request.FILES['file'].read()
            data = StringIO(file_in_memory.decode('utf-8'))
            try:
                # Use tab as the delimiter
                df = pd.read_csv(data, delimiter='\t', on_bad_lines='skip')
                print(df.head())  # Debug: Print the first few rows to confirm correct reading
            except Exception as e:
                messages.error(request, f"Failed to read file: {e}")
                return render(request, 'upload_file.html', {'form': form})

            if 'Date' not in df.columns:
                messages.error(request, "Missing 'Date' column in the uploaded file.")
                return render(request, 'upload_file.html', {'form': form})

            for index, row in df.iterrows():
                try:
                    ThreeMonthsShortVolume.objects.update_or_create(
                        Date=pd.to_datetime(row['Date'], format='%Y%m%d'),
                        Symbol=row['Symbol'],
                        defaults={
                            'ShortVolume': row.get('ShortVolume', 0),
                            'ShortExemptVolume': row.get('ShortExemptVolume', 0),
                            'TotalVolume': row.get('TotalVolume', 0),
                            'Market': row.get('Market', '')
                        }
                    )
                except Exception as e:
                    messages.error(request, f"Error processing row {index}: {e}")
            messages.success(request, "File uploaded and processed successfully.")
            return redirect('upload_file')
    else:
        form = FileUploadForm()
    return render(request, 'upload_file.html', {'form': form})


# Last 3 month data Reg sho view


# Function to fetch data for a specific date
def fetch_data_for_date(date):
    """Fetch and return data for a given date if the URL is valid."""
    formatted_date = date.strftime("%Y%m%d")
    url = f"https://www.nasdaqtrader.com/dynamic/symdir/regsho/nasdaqth{formatted_date}.txt"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = StringIO(response.text)
        df = pd.read_csv(data, delimiter='|', on_bad_lines='skip')
        return df
    return pd.DataFrame()  # Return empty DataFrame if request fails


# Function to check for missing dates and bulk fetch and save missing data
@login_required
def display_three_months_reg_sho_data(request, start_date_str):
    start_date = datetime.strptime(start_date_str, "%Y%m%d")
    start_date = get_previous_trading_day(start_date)
    end_date = start_date - timedelta(days=89)  # Last 90 trading days

    # Get all existing dates in the database for the range
    existing_dates = set(
        ThreeMonthsRegSHO.objects.filter(Date__range=[end_date, start_date]).values_list('Date', flat=True)
    )

    # Generate a list of missing dates (business days only)
    date_range = pd.date_range(end_date, start_date, freq='B')
    missing_dates = [single_date for single_date in date_range if single_date.date() not in existing_dates]

    # Define a helper function to process a single date
    def process_single_date(single_date):
        df = fetch_data_for_date(single_date)
        records = []
        for index, row in df.iterrows():
            records.append(
                ThreeMonthsRegSHO(
                    Date=single_date,
                    Symbol=row.get('Symbol', ''),
                    security_name=row.get('Security Name', ''),
                    market_category=row.get('Market Category', ''),
                    reg_sho_threshold_flag=row.get('Reg SHO Threshold Flag', ''),
                    rule_3210=row.get('Rule 3210', '')
                )
            )
        return records

    # Use ThreadPoolExecutor to fetch data in parallel for missing dates
    all_records = []
    with ThreadPoolExecutor(max_workers=10) as executor:  # Adjust number of workers based on your needs
        results = executor.map(process_single_date, missing_dates)
        for result in results:
            all_records.extend(result)

    # Bulk create records in one go (faster than creating one-by-one)
    if all_records:
        ThreeMonthsRegSHO.objects.bulk_create(all_records, ignore_conflicts=True)

    # Fetch and display the data in the range
    data = ThreeMonthsRegSHO.objects.filter(Date__range=[end_date, start_date]).order_by('-Date')[:30]
    #all_watch_lists = WatchList.objects.all()

    if request.user.is_authenticated:
        all_watch_lists = WatchList.objects.filter(user=request.user).order_by('order')
    else:
        all_watch_lists = []

    

    return render(request, 'months-reg-sho-data.html', {'data': data,'all_watch_lists': all_watch_lists})

#------------------------------------------------------------------------------------------------------------------

#----------------------------------- Reg sho data list, newly added and deleted ---------------------

def is_valid_symbol(s):
    """ Ensure the symbol contains at least one alphabetic character """
    return any(c.isalpha() for c in s)

from .ticker_lists import reg_sho_symbols

def reg_sho_symbols_view(request):

    # Prepare lists for display, sorted independently
    #current_list_data = [{'symbol': s, 'name': symbol_to_name[s]} for s in final_current_symbols]
    #newly_added_data = sorted([(s, d, symbol_to_name[s]) for s, d in added_symbols.items()], key=lambda x: x[1], reverse=True)
    #deleted_data = sorted([(s, d, symbol_to_name[s]) for s, d in deleted_symbols.items()], key=lambda x: x[1], reverse=True)
    if request.user.is_authenticated:
        all_watch_lists = WatchList.objects.filter(user=request.user).order_by('order')
    else:
        all_watch_lists = []

    current_list_data,newly_added_data,deleted_data,latest_date = reg_sho_symbols()
    
    context = {
        'current_list_data': current_list_data,
        'newly_added_data': newly_added_data,
        'deleted_data': deleted_data,
        'all_watch_lists': all_watch_lists,
        'latest_date': latest_date.strftime("%Y-%m-%d")
    }
    return render(request, 'reg_sho_symbols.html', context)



def reg_sho_remove_list():
    # Find the latest date in the table
    reg_latest_date = ThreeMonthsRegSHO.objects.aggregate(latest=Max('Date'))['latest']
    end_date = reg_latest_date - timedelta(days=90)

   # Fetch data from Django models
    combined_sho_data = ThreeMonthsRegSHO.objects.filter(Date__range=[end_date, reg_latest_date]).order_by('-Date')


    # Convert to DataFrame
    combined_sho_df = pd.DataFrame(list(combined_sho_data.values()))

    # Function to check if a symbol has been removed before the most recent trading day
    def check_removed_symbols_trading_days(df):
        removed_symbols = []
        
        # Get the most recent trading date (latest date in the dataset)
        most_recent_trading_day = df['Date'].max()
        
        # Get unique symbols
        unique_symbols = df['Symbol'].unique()
        
        for symbol in unique_symbols:
            # Get all the data related to the specific symbol
            symbol_data = df[df['Symbol'] == symbol]
            first_appearance = symbol_data['Date'].min()
            last_appearance = symbol_data['Date'].max()
            
            # Check if the last appearance is not the most recent trading day
            if last_appearance != most_recent_trading_day:
                removed_symbols.append({
                    'Symbol': symbol,
                    'Added': first_appearance,
                    'RemovalDate': last_appearance
                })
        
        return removed_symbols

    # Apply the function to the combined DataFrame
    removed_symbols_list = check_removed_symbols_trading_days(combined_sho_df)

    # Convert to a DataFrame for easy viewing
    removed_symbols_df = pd.DataFrame(removed_symbols_list)
    #--------------------------------------------------------------------------------------------------------------------

    # Function to drop symbols that contain only digits
    def drop_digit_only_symbols(df):
        # Use a regular expression to keep symbols that contain any non-digit characters
        filtered_df = df[~df['Symbol'].str.isdigit()]  # Negate the condition to filter out only-digit symbols
        return filtered_df

    # Apply the function to the removed symbols DataFrame
    filtered_removed_symbols_df = drop_digit_only_symbols(removed_symbols_df)
    #---------------------------------------------------------------------------------------------------------------------
    # Function to extract symbols from the last 30 days without raising SettingWithCopyWarning
    def extract_last_few_days_symbols(df):
        # Make a copy of the DataFrame to avoid modifying the original slice
        df_copy = df.copy()
        
        # Get the current date
        today = datetime.now()
        
        # Calculate the date few days ago
        last_few_days = today - timedelta(days=15)
        
        # Convert 'Added' and 'RemovalDate' columns to datetime using .loc to avoid the warning
        df_copy.loc[:, 'Added'] = pd.to_datetime(df_copy['Added'])
        df_copy.loc[:, 'RemovalDate'] = pd.to_datetime(df_copy['RemovalDate'])
        
        # Filter rows where the 'Added' or 'RemovalDate' is within the last 30 days
        last_few_days_df = df_copy[(df_copy['Added'] >= last_few_days) | (df_copy['RemovalDate'] >= last_few_days)]
        
        # Extract the unique symbols from the filtered DataFrame
        last_few_days_symbols = last_few_days_df['Symbol'].unique().tolist()
        
        return last_few_days_symbols

    # Apply the function to the filtered removed symbols DataFrame
    last_few_days_symbols_list = extract_last_few_days_symbols(filtered_removed_symbols_df)

    # List of symbols to remove
    remove_symbols = [] # you can remove symbols as list i.e remove_symbols = ['VRAX', 'FFIE']

    # Filter the list to exclude specified symbols
    removed_reg_sho_threshold_list = [symbol for symbol in last_few_days_symbols_list if symbol not in remove_symbols]
    #print(removed_reg_sho_threshold_list)

    #custom_watch_list_1 = ['MULN', 'FFIE', 'HOLO','MAXN','MLGO','RR','LUMN','OPEN','UBXG','GCTS','IVDA','LASE']
 

#--------------------------------------------------------- Reg sho Symbol ordered by Short Volume --------------------------
    sv_latest_date = ThreeMonthsShortVolume.objects.aggregate(latest=Max('Date'))['latest']

    # Calculate the start date (5 days before the latest date)
    consecutive_date = sv_latest_date - timedelta(days=0)

    # Filter data for the last 5 days
    recent_volumes = ThreeMonthsShortVolume.objects.filter(Date__range=[consecutive_date, sv_latest_date])

    # Calculate the average short volume for each symbol across these 5 days
    symbol_averages = recent_volumes.values('Symbol').annotate(avg_short_volume=Avg('ShortVolume')).order_by('-avg_short_volume')

    # Convert the data to a DataFrame for filtering
    df_symbol_averages = pd.DataFrame(symbol_averages)


    # Filter only the rows where the 'Symbol' exists in the list_of_symbols
    filtered_symbol_averages = df_symbol_averages[df_symbol_averages['Symbol'].isin(removed_reg_sho_threshold_list)]
    
    # By defalult it is sorted by Short Volume
    symbols_to_search = filtered_symbol_averages['Symbol'].tolist()
    return symbols_to_search





#----------------------------------- end Custom Watch list --------------------------------------

import os
from django.conf import settings
from django.http import HttpResponse
import json

def get_cik(symbol):
    # Construct the file path within the function
    file_path = os.path.join(settings.BASE_DIR, "data", "company_tickers_exchange.json")
    
    # Print the file path to see where Django is looking (optional)
    print(f"Looking for file at: {file_path}")
    
    # Attempt to open the file and load ticker data
    try:
        with open(file_path, "r") as f:
            ticker_data = json.load(f)
    except FileNotFoundError:
        # Return a response indicating the file was not found
        return HttpResponse(f"File not found at path: {file_path}", status=404)

    # Find the index of 'ticker' and 'cik' fields
    try:
        ticker_index = ticker_data["fields"].index("ticker")
        cik_index = ticker_data["fields"].index("cik")
    except ValueError:
        return None
    
    # Search for the symbol in the data
    for company in ticker_data["data"]:
        if company[ticker_index].lower() == symbol.lower():
            return company[cik_index]  # Return the CIK number

    return None  # Symbol not found in the data


import requests
import pandas as pd
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def fetch_sec_data(cik, count=30):
    url = f"https://data.sec.gov/rss?cik={cik}&type=3,4,5&exclude=true&count={count}"
    headers = {
        "User-Agent": "Your Name (your.email@example.com)"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching RSS feed for CIK {cik}: {e}")
        return pd.DataFrame(columns=["FormType", "FormDescription", "FilingDate", "FilingHref", "DocumentURL"])
    
    root = ET.fromstring(response.content)
    namespaces = {'atom': 'http://www.w3.org/2005/Atom'}
    
    form_types, form_descriptions, filing_dates, filing_hrefs, document_urls = [], [], [], [], []
    
    for entry in root.findall('atom:entry', namespaces):
        form_type = entry.find('atom:category', namespaces).attrib.get('term', '') if entry.find('atom:category', namespaces) is not None else ''
        form_description = entry.find('atom:title', namespaces).text if entry.find('atom:title', namespaces) is not None else ''
        filing_date = entry.find('atom:content-type/atom:filing-date', namespaces).text if entry.find('atom:content-type/atom:filing-date', namespaces) is not None else ''
        #filing_href = entry.find('atom:link', namespaces).attrib.get('href', '') if entry.find('atom:link', namespaces) is not None else ''
        filing_href = entry.find('atom:content-type/atom:filing-href', namespaces).text if entry.find('atom:content-type/atom:filing-href', namespaces) is not None else ''
        # Corrected line to fetch filing_href
        #filing_href = entry.find('atom:content-type', namespaces).find('atom:filing-href', namespaces).text if entry.find('atom:content-type', namespaces).find('atom:filing-href', namespaces) is not None else ''
        
        form_types.append(form_type)
        form_descriptions.append(form_description)
        filing_dates.append(filing_date)
        filing_hrefs.append(filing_href)

        document_urls= filing_hrefs # avoiding extra links
  
    
    df = pd.DataFrame({
        "FormType": form_types,
        "FormDescription": form_descriptions,
        "FilingDate": filing_dates,
        "FilingHref": filing_hrefs,
        "DocumentURL": document_urls
    })
    
    return df



# faster
import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.conf import settings
from django.http import JsonResponse


def find_symbol_list(top_sv_symbol):
    latest_date = ThreeMonthsShortVolume.objects.aggregate(latest=Max('Date'))['latest']

    # Calculate the start date (5 days before the latest date)
    consecutive_date = latest_date - timedelta(days=5)

    # Filter data for the last 5 days
    recent_volumes = ThreeMonthsShortVolume.objects.filter(Date__range=[consecutive_date, latest_date])

    # Calculate the average short volume for each symbol across these 5 days
    symbol_averages = recent_volumes.values('Symbol').annotate(avg_total_volume=Avg('TotalVolume')).order_by('-avg_total_volume')

    # Optionally, limit to the top 20 symbols based on average short volume
    top_symbols = symbol_averages[:top_sv_symbol]

    # Create a list of only the symbols, preserving the order
    symbol_list = [entry['Symbol'] for entry in top_symbols]

    return symbol_list

def view_test_symbol(request):
    top_sv_symbol= 5000
    symbol_list = find_symbol_list(top_sv_symbol)
    return JsonResponse(symbol_list, safe=False)

def fetch_symbol_data(symbol):
    """Fetches data for a single symbol."""
    cik = get_cik(symbol)
    print(f"Symbol: {symbol}, CIK: {cik}")  # Debugging line
    if cik:
        df = fetch_sec_data(cik, count=20)
        return symbol, df.to_dict(orient="records")
    else:
        print(f"CIK for {symbol} not found.")
        return symbol, None

@login_required
def fetch_and_save_sec_symbols_list(request):
    #symbols = ['MAXN','FFIE', 'HOLO', 'NVDA', 'AAPL', 'TSLA', 'LASE']
    top_sv_symbol= 5000
    symbols = find_symbol_list(top_sv_symbol)
    
    all_data = {}

    # Use ThreadPoolExecutor to fetch data concurrently for each symbol
    with ThreadPoolExecutor(max_workers=5) as executor:
        # Schedule the data fetching tasks
        futures = {executor.submit(fetch_symbol_data, symbol): symbol for symbol in symbols}
        
        for future in as_completed(futures):
            symbol = futures[future]
            try:
                symbol, data = future.result()
                if data:
                    all_data[symbol] = data
            except Exception as e:
                print(f"Error fetching data for symbol {symbol}: {e}")

    # Define the output path in the Django data directory
    output_file = os.path.join(settings.BASE_DIR, "data", "sec_data_symbols.json")

    # Save the entire dictionary to a JSON file
    with open(output_file, "w") as f:
        json.dump(all_data, f, indent=2)

    print(f"Saved data for all symbols to {output_file}")
    
    # Return the data as JSON response directly
    return JsonResponse(all_data, safe=False)

@login_required
def watch_list_links_old(request,watch_list_str):
    
    # Generate a unique cache key for each watch_list_str
    cache_key = f"watch_list_links{watch_list_str}"
    cache_time = 3600 * 4
    all_watch_lists = WatchList.objects.all()
    watch_charts_with_symbols = cache.get(cache_key)
    if watch_charts_with_symbols is not None:
        return render(request, 'watch-lists.html', {'charts_with_symbols': watch_charts_with_symbols,'all_watch_lists': all_watch_lists})

    start_date = datetime.now()
    #end_date = start_date - timedelta(days=90)

    # Fetch the watch list from the database
    watch_list_name = request.GET.get('watch_list', watch_list_str)
    

    watch_list = WatchList.objects.filter(name=watch_list_name).first()
    symbols_to_search = []

    if watch_list:
        symbols_to_search = list(WatchListSymbol.objects.filter(watch_list=watch_list).values_list('symbol', flat=True))
          # Convert all symbols to uppercase
        symbols_to_search = [symbol.upper() for symbol in symbols_to_search]
        print("Symbols to search (uppercase):", symbols_to_search)
    sv_latest_date = ThreeMonthsShortVolume.objects.aggregate(latest=Max('Date'))['latest']
    consecutive_date = sv_latest_date - timedelta(days=0)

    recent_volumes = ThreeMonthsShortVolume.objects.filter(Date__range=[consecutive_date, sv_latest_date])
    symbol_averages = recent_volumes.values('Symbol').annotate(avg_short_volume=Avg('ShortVolume')).order_by('-avg_short_volume')
    df_symbol_averages = pd.DataFrame(symbol_averages)
    
    filtered_symbol_averages = df_symbol_averages[df_symbol_averages['Symbol'].isin(symbols_to_search)]
    # Correct way to print the DataFrame
    #print('Filtered Symbol Averages:\n', filtered_symbol_averages)
    symbols_to_search = filtered_symbol_averages['Symbol'].tolist()
    #print(symbols_to_search)
    #symbols_to_search = ['AQMS', 'QLGN', 'VCIG','TSLA']
    #watch_charts_with_symbols = stock_charts(symbols_to_search)
    # Check if symbols_to_search is still empty
    if not symbols_to_search:
        # Fallback to a default list if necessary or return an empty response
        print(f"No symbols found for watch list '{watch_list_name}'. Using default list.")
        #symbols_to_search = ['AQMS']  # You can change this to a default list or handle it as needed

    # Handle the case where stock_charts might fail
    try:
        #watch_charts_with_symbols,his_data,today_data = stock_charts(symbols_to_search)
        watch_charts_with_symbols = stock_charts(symbols_to_search)
    except Exception as e:
        print(f"Error generating charts: {e}")
        watch_charts_with_symbols = []

    cache.set(cache_key, watch_charts_with_symbols, cache_time)
    # Fetch all watch lists from the database

    return render(request, 'watch-lists.html', {
        'charts_with_symbols': watch_charts_with_symbols,
        'all_watch_lists': all_watch_lists
        })
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from django.db.models import Avg, Max
import pandas as pd
from datetime import datetime, timedelta
from .models import WatchList, WatchListSymbol, ThreeMonthsShortVolume
@login_required
def watch_list_links(request, watch_list_str):
    # Generate a unique cache key for each user and watch_list_str
    cache_key = f"watch_list_links_{request.user.id}_{watch_list_str}"
    cache_time = 3600 * 4

    # Check if the request is to clear the cache
    if request.GET.get('clear_cache') == 'true':
        cache.delete(cache_key)
        return render(request, 'cache-clear-charts.html', {
            'charts_with_symbols': [],
            'all_watch_lists': WatchList.objects.filter(user=request.user).order_by('order'),
            'watch_list_name': watch_list_str,
            'message': f'{watch_list_str}: Cache cleared successfully!'
        })

    # Filter watch lists to only those belonging to the logged-in user
    if request.user.is_authenticated:
        all_watch_lists = WatchList.objects.filter(user=request.user).order_by('order')
    else:
        all_watch_lists = []

    # Determine the watch list name
    watch_list_name = request.GET.get('watch_list', watch_list_str)
    
    # Check the cache for precomputed results
    watch_charts_with_symbols = cache.get(cache_key)
    if watch_charts_with_symbols is not None:
        return render(request, 'watch-lists.html', {
            'charts_with_symbols': watch_charts_with_symbols,
            'all_watch_lists': all_watch_lists,
            'watch_list_name': watch_list_name
        })

    # Fetch the watch list specific to the user
    watch_list = get_object_or_404(WatchList, name=watch_list_name, user=request.user)

    # Get symbols associated with the watch list
    symbols_to_search = list(WatchListSymbol.objects.filter(watch_list=watch_list).values_list('symbol', flat=True))
    symbols_to_search = [symbol.upper() for symbol in symbols_to_search]

    if not symbols_to_search:
        return render(request, 'watch-lists.html', {
            'charts_with_symbols': [],
            'all_watch_lists': all_watch_lists,
            'watch_list_name': watch_list_name,
        })

    # Fetch and filter symbol averages
    sv_latest_date = ThreeMonthsShortVolume.objects.aggregate(latest=Max('Date'))['latest']
    consecutive_date = sv_latest_date - timedelta(days=0)

    recent_volumes = ThreeMonthsShortVolume.objects.filter(Date__range=[consecutive_date, sv_latest_date])
    symbol_averages = recent_volumes.values('Symbol').annotate(avg_short_volume=Avg('ShortVolume')).order_by('-avg_short_volume')
    df_symbol_averages = pd.DataFrame(symbol_averages)

    filtered_symbol_averages = df_symbol_averages[df_symbol_averages['Symbol'].isin(symbols_to_search)]
    symbols_to_search = filtered_symbol_averages['Symbol'].tolist()

    if not symbols_to_search:
        return render(request, 'watch-lists.html', {
            'charts_with_symbols': [],
            'all_watch_lists': all_watch_lists,
            'watch_list_name': watch_list_name,
        })
    user_specific = request.user
    # Generate stock charts
    try:
        watch_charts_with_symbols = generateCharts(symbols_to_search,user_specific)
    except Exception as e:
        print(f"Error generating charts: {e}")
        watch_charts_with_symbols = []

    # Cache the result
    cache.set(cache_key, watch_charts_with_symbols, cache_time)
    
    return render(request, 'watch-lists.html', {
        'charts_with_symbols': watch_charts_with_symbols,
        'all_watch_lists': all_watch_lists,
        'watch_list_name': watch_list_name
    })

@login_required
def watch_list_links_old_2(request, watch_list_str):
    # Generate a unique cache key for each user and watch_list_str
    cache_key = f"watch_list_links_{request.user.id}_{watch_list_str}"
    cache_time = 3600 * 4

    # Filter watch lists to only those belonging to the logged-in user
    #all_watch_lists = WatchList.objects.filter(user=request.user)
    if request.user.is_authenticated:
        all_watch_lists = WatchList.objects.filter(user=request.user).order_by('order')
    else:
        all_watch_lists = []
    # Determine the watch list name
    watch_list_name = request.GET.get('watch_list', watch_list_str)

    # Check the cache for precomputed results
    watch_charts_with_symbols = cache.get(cache_key)
    if watch_charts_with_symbols is not None:
        return render(request, 'watch-lists.html', {
            'charts_with_symbols': watch_charts_with_symbols,
            'all_watch_lists': all_watch_lists,
            'watch_list_name': watch_list_name
        })



    # Fetch the watch list specific to the user
    watch_list = get_object_or_404(WatchList, name=watch_list_name, user=request.user)

    # Get symbols associated with the watch list
    symbols_to_search = list(WatchListSymbol.objects.filter(watch_list=watch_list).values_list('symbol', flat=True))
    symbols_to_search = [symbol.upper() for symbol in symbols_to_search]

    if not symbols_to_search:
        print(f"No symbols found for watch list '{watch_list_name}'.")
        return render(request, 'watch-lists.html', {
            'charts_with_symbols': [],
            'all_watch_lists': all_watch_lists,
        })

    # Fetch and filter symbol averages
    sv_latest_date = ThreeMonthsShortVolume.objects.aggregate(latest=Max('Date'))['latest']
    consecutive_date = sv_latest_date - timedelta(days=0)

    recent_volumes = ThreeMonthsShortVolume.objects.filter(Date__range=[consecutive_date, sv_latest_date])
    symbol_averages = recent_volumes.values('Symbol').annotate(avg_short_volume=Avg('ShortVolume')).order_by('-avg_short_volume')
    df_symbol_averages = pd.DataFrame(symbol_averages)

    filtered_symbol_averages = df_symbol_averages[df_symbol_averages['Symbol'].isin(symbols_to_search)]
    symbols_to_search = filtered_symbol_averages['Symbol'].tolist()

    if not symbols_to_search:
        print(f"No matching symbols found for averages in '{watch_list_name}'.")
        return render(request, 'watch-lists.html', {
            'charts_with_symbols': [],
            'all_watch_lists': all_watch_lists,
        })

    # Generate stock charts
    try:
        #watch_charts_with_symbols = stock_charts(symbols_to_search)
            # Fetch user watchlists
        #user_watchlists = WatchList.objects.filter(user=request.user)

        # Get all symbols from the user's watchlists
        #watchlist_symbols = WatchListSymbol.objects.filter(watch_list__in=user_watchlists).values_list('symbol', flat=True)
        #watchlist_symbols = ['HOLO','RR']
        # Filter stocks based on user's watchlist symbols
        user_specific = request.user
        watch_charts_with_symbols = generateCharts(symbols_to_search,user_specific)
        #watch_charts_with_symbols, historical_data, today_data  = stock_charts_hist_today(symbols_to_search)
        #watch_charts_with_symbols = StockCharts(symbols_to_search)
    except Exception as e:
        print(f"Error generating charts: {e}")
        watch_charts_with_symbols = []

    # Cache the result
    cache.set(cache_key, watch_charts_with_symbols, cache_time)
    user = request.user
    #print(f"Watch List Name: {watch_list_name}")
    #missing_tickers_list,watchlist_missing_in_stock_data,sv_missing_tickers_list,sv_missing_tickers_list = regsho_watchlist_sv_tickers_not_in_stock_symbol_data(user)
    return render(request, 'watch-lists.html', {
        'charts_with_symbols': watch_charts_with_symbols,
        'all_watch_lists': all_watch_lists,
        'watch_list_name': watch_list_name
    })


from django.shortcuts import render, redirect, get_object_or_404
from .models import WatchList, WatchListSymbol
from .forms import WatchListForm, WatchListSymbolForm
@login_required
def manage_watch_list_old(request):
    # Initialize forms
    watch_list_form = WatchListForm()
    symbol_form = WatchListSymbolForm()

    # Handle adding a new watch list
    if request.method == 'POST' and 'add_watch_list' in request.POST:
        watch_list_form = WatchListForm(request.POST)
        if watch_list_form.is_valid():
            watch_list_form.save()
            return redirect('manage_watch_list')

    # Handle adding a new symbol to an existing watch list
    if request.method == 'POST' and 'add_symbol' in request.POST:
        symbol_form = WatchListSymbolForm(request.POST)
        if symbol_form.is_valid():
            symbol = symbol_form.save(commit=False)
            symbol.symbol = symbol.symbol.upper()  # Convert symbol to uppercase
            watch_list_id = request.POST.get('watch_list_id')
            symbol.watch_list = get_object_or_404(WatchList, id=watch_list_id)
            symbol.save()
            return redirect('manage_watch_list')

    # Handle deleting a watch list
    if request.method == 'POST' and 'delete_watch_list' in request.POST:
        watch_list_id = request.POST.get('watch_list_id')
        watch_list = get_object_or_404(WatchList, id=watch_list_id)
        watch_list.delete()
        return redirect('manage_watch_list')

    # Handle deleting a symbol
    if request.method == 'POST' and 'delete_symbol' in request.POST:
        symbol_id = request.POST.get('symbol_id')
        symbol = get_object_or_404(WatchListSymbol, id=symbol_id)
        symbol.delete()
        return redirect('manage_watch_list')

    # Query all watch lists with their symbols
    watch_lists = WatchList.objects.all()

    return render(request, 'add_watch_list.html', {
        'watch_list_form': watch_list_form,
        'symbol_form': symbol_form,
        'watch_lists': watch_lists,
    })
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import WatchList, WatchListSymbol
from .forms import WatchListForm, WatchListSymbolForm

@login_required
def manage_watch_list(request):
    # Initialize forms
    watch_list_form = WatchListForm()
    symbol_form = WatchListSymbolForm()

    # Handle adding a new watch list
    if request.method == 'POST' and 'add_watch_list' in request.POST:
        watch_list_form = WatchListForm(request.POST)
        if watch_list_form.is_valid():
            new_watch_list = watch_list_form.save(commit=False)
            new_watch_list.user = request.user  # Set the current user as the owner
            new_watch_list.save()
            return redirect('manage_watch_list')

    # Handle adding a new symbol to an existing watch list
    if request.method == 'POST' and 'add_symbol' in request.POST:
        symbol_form = WatchListSymbolForm(request.POST)
        if symbol_form.is_valid():
            symbol = symbol_form.save(commit=False)
            symbol.symbol = symbol.symbol.upper()  # Convert symbol to uppercase
            watch_list_id = request.POST.get('watch_list_id')
            watch_list = get_object_or_404(WatchList, id=watch_list_id, user=request.user)
            symbol.watch_list = watch_list
            symbol.save()
            return redirect('manage_watch_list')

    # Handle deleting a watch list
    if request.method == 'POST' and 'delete_watch_list' in request.POST:
        watch_list_id = request.POST.get('watch_list_id')
        watch_list = get_object_or_404(WatchList, id=watch_list_id, user=request.user)
        watch_list.delete()
        return redirect('manage_watch_list')

    # Handle deleting a symbol
    if request.method == 'POST' and 'delete_symbol' in request.POST:
        symbol_id = request.POST.get('symbol_id')
        symbol = get_object_or_404(WatchListSymbol, id=symbol_id, watch_list__user=request.user)
        symbol.delete()
        return redirect('manage_watch_list')

    # Query only the watch lists belonging to the logged-in user
    watch_lists = WatchList.objects.filter(user=request.user)
    user =request.user
    #missing_tickers_list,watchlist_missing_in_stock_data,sv_missing_tickers_list = regsho_watchlist_sv_tickers_not_in_stock_symbol_data(user)
    return render(request, 'add_watch_list.html', {
        'watch_list_form': watch_list_form,
        'symbol_form': symbol_form,
        'watch_lists': watch_lists,
        #'missing_tickers_list': missing_tickers_list,
        #'watchlist_missing_in_stock_data': watchlist_missing_in_stock_data,
    })
   

from django.db.models import Max
#def find_all_symbols(request):
def find_all_symbols():
    
    # Step 1: Get the latest date from the table
    latest_date = ThreeMonthsShortVolume.objects.aggregate(Max('Date'))['Date__max']

    # Step 2: Filter records with the latest date
    latest_date_records = ThreeMonthsShortVolume.objects.filter(Date=latest_date)

    # Step 3: Extract the unique list of symbols for the latest date
    symbols = latest_date_records.values_list('Symbol', flat=True).distinct()

    # Step 4: Convert symbols to a list (optional)
    symbols_list = list(symbols)

    print(symbols_list)

    return symbols_list
    #return JsonResponse(symbols_list, safe=False)
#tickers = ['MAXN','FFIE', 'HOLO', 'NVDA', 'AAPL', 'TSLA', 'LASE']

import requests
from bs4 import BeautifulSoup
import pandas as pd
from django.http import JsonResponse

def view_test(request):
    # Yahoo Finance URL for most active stocks
    url = "https://finance.yahoo.com/markets/stocks/trending/"

    # Request the page content
    headers = {'User-Agent': 'Mozilla/5.0'}
    if url:
        response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    # Find the table and parse rows
    table = soup.find("table")
    rows = table.find_all("tr")[1:]  # Skip header row

    # Extract ticker, name, and volume
    data = []
    for row in rows[:20]:  # Limit to top 30
        columns = row.find_all("td")
        if len(columns) > 2:  # Ensure there are enough columns
            ticker = columns[0].text.strip()
            name = columns[1].text.strip()
            volume = columns[6].text.strip()
            data.append({"Ticker": ticker, "Name": name, "Volume": volume})

    # Convert to DataFrame
    df = pd.DataFrame(data)
    tickers_list = df['Ticker'].tolist()
    print(tickers_list)
    
    # Convert DataFrame to list of dictionaries for JSON response
    return JsonResponse(df.to_dict(orient='records'), safe=False)



@login_required
def missing_ticker_in_stock_data_view(request):
    user = request.user
    missing_tickers_list,watchlist_missing_in_stock_data,sv_missing_tickers_list = regsho_watchlist_sv_tickers_not_in_stock_symbol_data(user)
    
    if request.user.is_authenticated:
        all_watch_lists = WatchList.objects.filter(user=request.user).order_by('order')
    else:
        all_watch_lists = []
    return render(request, 'missing_ticker.html', {
        'all_watch_lists': all_watch_lists,
        'missing_tickers_list': missing_tickers_list,
        'watchlist_missing_in_stock_data': watchlist_missing_in_stock_data,
        'sv_missing_tickers_list': sv_missing_tickers_list
        
        })


def show_tickers(request):
    # Get tickers
    tickers = stock_data_tickers()

    # Check if tickers is a dictionary
    if isinstance(tickers, dict):
        # Return the dictionary as a JSON response
        return JsonResponse(tickers)
    else:
        # Return the list as a JSON response with safe=False
        return JsonResponse(tickers, safe=False)

from typing import List, Set

def unique_all_ytop_regsho_splits_tickers_function() -> List[str]:
    """
    Merges tickers from various sources and returns a unique list of tickers.

    Returns:
        List[str]: A list of unique tickers.
    """
    # Assuming these functions return lists of tickers
    y_most_active_tickers = y_most_active()  # Example: ['AAPL', 'MSFT', 'TSLA']
    y_trending_tickers = y_tranding()       # Example: ['GOOG', 'AAPL', 'AMZN']
    y_top_gainers_tickers = y_top_gainers() # Example: ['TSLA', 'NVDA', 'META']
    y_top_losers_tickers = y_top_losers()   # Example: ['AMZN', 'NFLX', 'TSLA']
    top_short_volume_symbols = top_sv_symbol_lists()
    reg_sho_remove_symbols = reg_sho_remove_list()
    current_regsho_symbols = get_current_regsho_symbols()

    # Fetch all unique stock split symbols from the database
    stock_splits_symbols_QuerySet = TickerSplit.objects.values_list('symbol', flat=True).distinct()
    stock_splits_symbols = list(stock_splits_symbols_QuerySet)

    # Merge all lists and remove duplicates using set
    unique_tickers: Set[str] = set(
        y_most_active_tickers +
        y_trending_tickers +
        y_top_gainers_tickers +
        y_top_losers_tickers +
        top_short_volume_symbols +
        current_regsho_symbols +
        reg_sho_remove_symbols +
        stock_splits_symbols
    )

    # Convert the set back to a list and return
    return list(unique_tickers)



# Print the total number of unique tickers and the tickers themselves
#print(f"Total number of unique tickers: {len(unique_all_ytop_regsho_splits_tickers)}")
#print(f"unique_all_ytop_regsho_splits_tickers: {unique_all_ytop_regsho_splits_tickers}")

def update_watchlist_regsho_symbol_stock_data_view(request):
    user = request.user
    #watchlist_regsho_symbols, watchlist_symbols_list = merge_watchlist_regsho_symbols()
    unique_all_ytop_regsho_splits_tickers = unique_all_ytop_regsho_splits_tickers_function()
    #top_sv_symbols = top_sv_symbol_lists()
    # Merge both lists
    #merged_symbols = watchlist_regsho_symbols + top_sv_symbols
    # Convert to set to remove duplicates and get unique symbols
    #unique_symbols = set(merged_symbols)
    # Optionally, convert back to a list if needed
    #watchlist_regsho_sv_symbols = list(unique_symbols)
    # Get all unique symbols from the user's watchlists

    user = request.user
    user_watchlists = WatchList.objects.filter(user=user)

    # Get all unique symbols from the user's watchlists
    watchlist_symbols = list(set(
        WatchListSymbol.objects.filter(watch_list__in=user_watchlists).values_list('symbol', flat=True)
    ))
    # Convert watchlist_symbols to a set before combining
    unique_watchlist_symbols = set(watchlist_symbols)
    # | Operator: Combines two sets into a new set that contains all unique elements from both.
    #unique_all_ytop_watchlist_regsho_splits_tickers = unique_all_ytop_regsho_splits_tickers | unique_watchlist_symbols
    #print(f"Total number of unique tickers: {len(unique_all_ytop_watchlist_regsho_splits_tickers)}")
    #print(f"unique_all_ytop_watchlist_regsho_splits_tickers: {unique_all_ytop_watchlist_regsho_splits_tickers}")
    unique_all_ytop_watchlist_regsho_splits_tickers = list(
    set(unique_all_ytop_regsho_splits_tickers) | set(unique_watchlist_symbols)
)

    try:
        # Call the function to fetch and save stock data
        #fetch_and_save_stock_data(watchlist_regsho_sv_symbols)
        fetch_and_save_stock_data(unique_all_ytop_watchlist_regsho_splits_tickers)

        # Retrieve the symbols that were updated or created
        #updated_symbols = StockSymbolData.objects.filter(symbol__in=watchlist_regsho_sv_symbols)
        updated_symbols = StockSymbolData.objects.filter(symbol__in=unique_all_ytop_watchlist_regsho_splits_tickers)
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

    return JsonResponse(response_data, safe=False, status=status)

from django.http import JsonResponse
from datetime import datetime, timedelta
import pandas as pd

def update_watchlist_news_data_view(request):
    user = request.user
    watchlist_regsho_symbols, watchlist_symbols_list = merge_watchlist_regsho_symbols()
    top_sv_symbols = top_sv_symbol_lists()

    # Merge both lists
    merged_symbols = watchlist_regsho_symbols + top_sv_symbols

    # Convert to set to remove duplicates and get unique symbols
    unique_symbols = set(merged_symbols)

    # Optionally, convert back to a list if needed
    watchlist_regsho_sv_symbols = list(unique_symbols)

    try:
        # Define the date range (last 90 days)
        start_date = datetime.today()
        end_date = start_date - timedelta(days=90)
        date_range = pd.date_range(start=end_date, end=start_date)

        # To store news for each symbol
        all_news_data = {}

        for ticker in watchlist_regsho_sv_symbols:
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

    return JsonResponse(response_data, status=status)


def update_watchlist_news_data_view_old(request):
    # Define the list of symbols to search
    #symbols_to_search = ['FFIE', 'HOLO', 'LASE']
    user = request.user
    watchlist_regsho_symbols, watchlist_symbols_list = merge_watchlist_regsho_symbols()
    #print(watchlist_symbols_list)  
    symbols_to_search =  watchlist_regsho_symbols
    # Define the date range (last 90 days)
    start_date = datetime.today()
    end_date = start_date - timedelta(days=90)
    date_range = pd.date_range(start=end_date, end=start_date)

    all_news_data = {}

    for ticker in symbols_to_search:
        # Call the check_news_each_day function to get the news data for each symbol
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

        # Store the news data for each ticker
        all_news_data[ticker] = news_list

    # Return the news data for all tickers as a JSON response
    return JsonResponse(all_news_data)

def save_stock_data_view_old(request):
    # List of symbols to fetch
    symbols_to_fetch = ['FFIE','HOLO', 'NVDA']
    
    try:
        # Call the function to fetch and save stock data
        fetch_and_save_stock_data(symbols_to_fetch)

        # Retrieve the symbols that were updated or created
        updated_symbols = StockSymbolData.objects.filter(symbol__in=symbols_to_fetch)
        response_data = {
            "message": "Stock data fetched and saved successfully.",
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

    return JsonResponse(response_data, safe=False, status=status)

# Function to fetch and return news data in JSON format for multiple tickers

def save_and_get_multiple_news_data_old(request):
    # Define the list of symbols to search
    symbols_to_search = ['FFIE', 'HOLO', 'LASE']
    tickers = stock_data_tickers()

    # Count the total number of tickers
    total_tickers = len(tickers)
    print(f"Total number of tickers: {total_tickers}")

    #symbols_to_search = tickers

    # Select the first 100 elements
    #symbols_to_search = symbols_to_search[:1000]
    # Skip indices 1 to 100
    #symbols_to_search = symbols_to_search[:0] + symbols_to_search[8270:]

    total_tickers = len(tickers)
    print(f"Total number of tickers: {total_tickers}")

    # Set the group size (1000 in this case)
    group_size = 1000

    # Loop through the tickers in chunks of 'group_size'
    for start in range(0, total_tickers, group_size):
        end = start + group_size
        chunk = tickers[start:end]
        print(f"Processing tickers from {start+1} to {min(end, total_tickers)}")

    # Do your processing with this chunk of tickers
    # Example: symbols_to_search = chunk
    # Process the chunk...

    
    # Define the date range (last 90 days)
    start_date = datetime.today()
    end_date = start_date - timedelta(days=90)
    date_range = pd.date_range(start=end_date, end=start_date)

    all_news_data = {}

    for ticker in symbols_to_search:
        # Call the check_news_each_day function to get the news data for each symbol
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

        # Store the news data for each ticker
        all_news_data[ticker] = news_list

    # Return the news data for all tickers as a JSON response
    return JsonResponse(all_news_data)


from django.http import JsonResponse
from django.shortcuts import render

def save_stock_data_view(request):
    if request.method == 'POST':
        # Determine which form was submitted
        form_type = request.POST.get('form_type')

        if form_type == 'ranges_form':
            # Process the range-based form
            ranges = request.POST.getlist('ranges')  # List of range strings (e.g., "1-1000")
            tickers = stock_data_tickers()  # Assume this function returns a list of tickers
            total_tickers = len(tickers)
            processed_tickers = []

            try:
                for range_str in ranges:
                    try:
                        start, end = map(int, range_str.split('-'))
                        start = max(0, start - 1)
                        end = min(total_tickers, end)
                        chunk = tickers[start:end]
                        processed_tickers.extend(chunk)
                        print(f"Processing tickers from {start+1} to {end}")
                        record_msg = fetch_and_save_stock_data(chunk)  # Function to fetch and save data only returns record_msg
                    except ValueError:
                        print(f"Invalid range: {range_str}")
                        continue

                response_data = {
                    "Total Tickers": total_tickers,
                    "Processed Tickers Range": f"Processing tickers from {start+1} to {end}",
                    "Processed Tickers": processed_tickers,
                    "message": record_msg
                }
                status = 200
            except Exception as e:
                response_data = {
                    "message": "An error occurred while processing range-based stock data.",
                    "error": str(e)
                }
                status = 500

            return JsonResponse(response_data, safe=False, status=status)

        elif form_type == 'tickers_form':
            # Process the specific tickers form
            specific_tickers_input = request.POST.get('tickers', '')
            specific_tickers = [ticker.strip().upper() for ticker in specific_tickers_input.split(',') if ticker.strip()]

            try:
                record_msg = fetch_and_save_stock_data(specific_tickers)  # Function to fetch and save data
                response_data = {
                    "Processed Tickers": specific_tickers,
                    "message": record_msg
                }
                status = 200
            except Exception as e:
                response_data = {
                    "message": "An error occurred while processing specific tickers.",
                    "error": str(e)
                }
                status = 500

            return JsonResponse(response_data, safe=False, status=status)
        else:
            return JsonResponse({"message": "Unknown form submission."}, status=400)

    else:
        # Handle GET request: calculate total_tickers for display
        tickers = stock_data_tickers()  # Assume this function returns a list of tickers
        total_tickers = len(tickers)
        all_watch_lists = WatchList.objects.filter(user=request.user).order_by('order') if request.user.is_authenticated else []
        return render(request, 'stock_data_form.html', {
            'all_watch_lists': all_watch_lists,
            'total_tickers': total_tickers,
        })

        


from django.http import JsonResponse
from django.shortcuts import render
from datetime import datetime, timedelta
import pandas as pd

def save_and_get_multiple_news_data(request):
    if request.method == 'POST':
        # Fetch the ranges from the POST data
        ranges = request.POST.getlist('ranges')  # List of range strings (e.g., "1-1000")
        
        # Get the list of all tickers
        tickers = stock_data_tickers()  # Assume this function returns a list of tickers
        total_tickers = len(tickers)
        print(f"Total number of tickers: {total_tickers}")

        # Initialize the final result dictionary
        all_news_data = {}

        # Loop through each range provided by the user
        for range_str in ranges:
            try:
                # Parse the start and end values from the range
                start, end = map(int, range_str.split('-'))
                # Adjust to Python's 0-based indexing
                start = max(0, start - 1)
                end = min(total_tickers, end)
                # Get the chunk of tickers
                chunk = tickers[start:end]
                print(f"Processing tickers from {start+1} to {end}")

                # Process each ticker in this chunk
                for ticker in chunk:
                    # Define the date range (last 90 days)
                    start_date = datetime.today()
                    end_date = start_date - timedelta(days=90)
                    date_range = pd.date_range(start=end_date, end=start_date)

                    # Call the function to get news data
                    news_data = check_news_each_day(ticker, date_range)  # Assume this returns a list of news objects
                    # Prepare the data for JSON response
                    news_list = []
                    for news_item in news_data:
                        news_list.append({
                            "Date": news_item.Date.strftime('%Y-%m-%d'),
                            "NewsTitle": news_item.NewsTitle,
                            "NewsLink": news_item.NewsLink,
                            "providerPublishTime": news_item.providerPublishTime.strftime('%Y-%m-%d %H:%M:%S')
                        })

                    # Store the news data for this ticker
                    all_news_data[ticker] = news_list
            except ValueError:
                print(f"Invalid range: {range_str}")
                continue

        # Prepare the response data
        response_data = {
            "Total Tickers": total_tickers,
            "Processed Tickers Range": f"Processing tickers from {start+1} to {end}",
            "message": "Stock data fetched and saved successfully.",
            "Processed Tickers": chunk,  # Include the list of all tickers
            #"news_data": all_news_data  # Include the detailed news data (if needed)
        }

        # Return the results as JSON
        return JsonResponse(response_data)
    else:
        # Handle GET request: calculate total_tickers for display
        tickers = stock_data_tickers()  # Assume this function returns a list of tickers
        total_tickers = len(tickers)
        # Render the input form for providing ranges
        if request.user.is_authenticated:
            all_watch_lists = WatchList.objects.filter(user=request.user).order_by('order')
        else:
            all_watch_lists = []
        return render(request, 'news_data_form.html', {
            'all_watch_lists': all_watch_lists,
            'total_tickers': total_tickers

            })



def view_data_for_symbols(request):
    # List of symbols to fetch (can also be dynamic, e.g., from GET params)
    symbols = ['HOLO','NVDA']

    # Fetch data for the symbols
    data = fetch_data_for_symbols(symbols)

    # Format the data to be JSON serializable
    formatted_data = {}
    for symbol, queryset in data.items():
        if queryset is not None:
            formatted_data[symbol] = [
                {
                    'Date': entry.timestamp.strftime('%Y-%m-%d'),
                    'Open': float(entry.open),
                    'High': float(entry.high),
                    'Low': float(entry.low),
                    'Close': float(entry.close),
                    'Adj Close': float(entry.adj_close),
                    'Volume': entry.volume
                }
                for entry in queryset
            ]
        else:
            formatted_data[symbol] = None  # No data for the symbol

    # Return the formatted data as JSON
    return JsonResponse(formatted_data, safe=False)










def view_stock_charts_for_whole_data(request):
    """View to display stock charts."""
    symbols = ['HOLO', 'NVDA']  # Example symbols; replace with user input or dynamic data
    charts = {}

    for symbol in symbols:
        # Fetch data from the database
        stock_symbol = StockSymbolData.objects.filter(symbol=symbol).first()
        if stock_symbol:
            stock_data = StockPriceData.objects.filter(stock_symbol=stock_symbol).order_by('timestamp')
            if stock_data.exists():
                # Convert data to a Pandas DataFrame
                df = pd.DataFrame(list(stock_data.values('timestamp', 'open', 'high', 'low', 'close', 'volume')))
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)

                # Generate a chart for the symbol
                chart_html = generateCharts(symbol, df)
                charts[symbol] = chart_html

    return render(request, 'stock_charts.html', {'charts': charts})

from datetime import timedelta, date
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import WatchList, WatchListSymbol, NewsData
import yfinance as yf

@login_required
def watchlist_news(request):
    # Get the logged-in user's watchlists
    user_watchlists = WatchList.objects.filter(user=request.user)
    
    # Get all symbols from the user's watchlists
    watchlist_symbols = WatchListSymbol.objects.filter(watch_list__in=user_watchlists).values_list('symbol', flat=True)
    
    # Get today's date
    today = date.today()
    # Get yesterday's date
    yesterday = today - timedelta(days=1)
    
    # Filter news for today and yesterday for the watchlist symbols
    news_today = NewsData.objects.filter(
        news_symbol__symbol__in=watchlist_symbols,
        Date=today
    ).order_by('-providerPublishTime')
    
    news_yesterday = NewsData.objects.filter(
        news_symbol__symbol__in=watchlist_symbols,
        Date=yesterday
    ).order_by('-providerPublishTime')
    
    # Get unique symbols from the news data
    unique_symbols = set(news.news_symbol.symbol for news in news_today) | \
                     set(news.news_symbol.symbol for news in news_yesterday)
    
    # Fetch long names only for the symbols in the news
    symbol_long_names = {}
    
    symbol_data = {}
    for symbol in unique_symbols:
        stock_info = yf.Ticker(symbol)
        symbol_long_name = stock_info.info.get("longName", "Name not found")
        
        # Fetch today's price and previous close for price change %
        try:
            price_data = stock_info.history(period="1d")  # Fetch today's data
            if not price_data.empty:
                current_price = price_data['Close'][-1]
                previous_close = stock_info.info.get("regularMarketPreviousClose", current_price)
                price_change_pct = ((current_price - previous_close) / previous_close) * 100
            else:
                price_change_pct = None
        except Exception as e:
            price_change_pct = None  # Handle API failures or missing data gracefully

        # Save symbol information
        symbol_data[symbol] = {
            "long_name": symbol_long_name,
            "price_change_pct": round(price_change_pct, 2) if price_change_pct is not None else "N/A"
        }
    for news in news_today:
        news.providerPublishTime = news.providerPublishTime + timedelta(hours=1)
        # Extract and assign date and time separately
        news.publish_date = news.providerPublishTime.date()  # Extract only the date
        news.publish_time = news.providerPublishTime.time()  # Extract only the time
        news.symbol_long_name = symbol_data.get(news.news_symbol.symbol, {}).get("long_name", "Name not found")
        news.price_change_pct = symbol_data.get(news.news_symbol.symbol, {}).get("price_change_pct", "N/A")

    for news in news_yesterday:
        news.providerPublishTime = news.providerPublishTime + timedelta(hours=1)
        # Extract and assign date and time separately
        news.publish_date = news.providerPublishTime.date()  # Extract only the date
        news.publish_time = news.providerPublishTime.time()  # Extract only the time
        news.symbol_long_name = symbol_data.get(news.news_symbol.symbol, {}).get("long_name", "Name not found")
        news.price_change_pct = symbol_data.get(news.news_symbol.symbol, {}).get("price_change_pct", "N/A")


    
    if request.user.is_authenticated:
        all_watch_lists = WatchList.objects.filter(user=request.user).order_by('order')
    else:
        all_watch_lists = []

    # Pass data to the template
    context = {
        'all_watch_lists': all_watch_lists,
        'news_today': news_today,
        'news_yesterday': news_yesterday,
    }
    return render(request, 'watchlist_news.html', context)




from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import WatchList, WatchListSymbol, NewsData
from datetime import timedelta, date
import yfinance as yf
@login_required
def watchlist_screener(request):
    # Get the logged-in user's watchlists
    user_watchlists = WatchList.objects.filter(user=request.user)

    # Get all symbols from the user's watchlists
    watchlist_symbols = WatchListSymbol.objects.filter(watch_list__in=user_watchlists).values_list('symbol', flat=True)
    # Convert to a set to ensure uniqueness, then back to a list
    watchlist_symbols = list(set(watchlist_symbols))
    # Collect data for each symbol
    screener_data = []
    for idx, symbol in enumerate(watchlist_symbols, start=1):
        try:
            # Fetch stock info
            stock_info = yf.Ticker(symbol)
            long_name = stock_info.info.get("longName", "Name not found")

            # Fetch today's price and previous close for price change %
            price_data = stock_info.history(period="1d")
            if not price_data.empty:
                current_price = price_data['Close'][-1]  # Current price
                previous_close = stock_info.info.get("regularMarketPreviousClose", current_price)
                price_change = current_price - previous_close
                price_change_pct = (price_change / previous_close) * 100 if previous_close else 0
                total_volume = price_data['Volume'][-1]
                volume_per_min = total_volume / (6.5 * 60)  # Assuming 6.5 hours of trading
            else:
                current_price = price_change = price_change_pct = total_volume = volume_per_min = 0

            # Round values to 2 decimal places
            price_change_pct = round(price_change_pct, 2)
            price_change = round(price_change, 2)
            volume_per_min = round(volume_per_min, 2)
            total_volume = round(total_volume)
            current_price = round(current_price, 2)  # Round current price to 2 decimal places
            # Get today's date
            today = date.today()
            # Get yesterday's date
            yesterday = today - timedelta(days=1)
            # Check for related news
            news = NewsData.objects.filter(news_symbol__symbol=symbol, Date=today).order_by('-providerPublishTime').first()
            news_title = news.NewsTitle if news else "No News Today"
            news_link = news.NewsLink if news else None
            news_publish_time = news.providerPublishTime if news else None
            # Extract the time and date in a shorthand way:
            news_publish_date = news_publish_time.date() if news_publish_time else None
            news_publish_time_only = news_publish_time.time() if news_publish_time else None


            screener_data.append({
                "id": idx,
                "symbol": symbol,
                "long_name": long_name,
                "price_change_pct": price_change_pct,
                "price_change": price_change,
                "volume_per_min": volume_per_min,
                "total_volume": total_volume,
                "current_price": current_price,  # Add the current price to the data
                "news_title": news_title,
                "news_link": news_link,
                "news_publish_date": news_publish_date,
                "news_publish_time_only": news_publish_time_only,
            })

        except Exception:
            # Handle failures gracefully
            screener_data.append({
                "id": idx,
                "symbol": symbol,
                "long_name": "Error fetching data",
                "price_change_pct": 0,
                "price_change": 0,
                "volume_per_min": 0,
                "total_volume": 0,
                "current_price": 0,  # Default value for current price if an error occurs
                "news_title": "N/A",
                "news_link": None,
                "news_publish_date": news_publish_date,
                "news_publish_time_only": news_publish_time_only,
            })

    # Initialize sorting parameters
    sort_field = request.GET.get('sort', 'price_change_pct')  # Default sorting field
    sort_direction = request.GET.get('direction', 'desc')  # Default sorting direction

    # Sort screener_data based on the selected column and direction
    reverse = sort_direction == 'desc'
    try:
        screener_data = sorted(
            screener_data,
            key=lambda x: x.get(sort_field, 0) if isinstance(x.get(sort_field, (int, float)), (int, float)) else 0,
            reverse=reverse
        )
    except KeyError:
        pass  # Handle invalid sort_field gracefully by skipping sorting

    # Pass data to the template
    if request.user.is_authenticated:
        all_watch_lists = WatchList.objects.filter(user=request.user).order_by('order')
    else:
        all_watch_lists = []

  
        
    context = {
        'all_watch_lists': all_watch_lists,
        "screener_data": screener_data,
        "current_sort": sort_field,
        "current_direction": sort_direction,
    }
    return render(request, "watchlist_screener.html", context)




import math

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





from django.http import JsonResponse
import yfinance as yf
from .models import StockSymbolInfo, WatchList, WatchListSymbol




def update_stock_info(request):

    unique_all_ytop_regsho_splits_tickers = unique_all_ytop_regsho_splits_tickers_function()
    user = request.user
    user_watchlists = WatchList.objects.filter(user=user)

    # Get all unique symbols from the user's watchlists
    watchlist_symbols = list(set(
        WatchListSymbol.objects.filter(watch_list__in=user_watchlists).values_list('symbol', flat=True)
    ))
    # Convert watchlist_symbols to a set before combining
    unique_watchlist_symbols = set(watchlist_symbols)
    # | Operator: Combines two sets into a new set that contains all unique elements from both.
    #unique_all_ytop_watchlist_regsho_splits_tickers = unique_all_ytop_regsho_splits_tickers | unique_watchlist_symbols
    #print(f"Total number of unique tickers: {len(unique_all_ytop_watchlist_regsho_splits_tickers)}")
    #print(f"unique_all_ytop_watchlist_regsho_splits_tickers: {unique_all_ytop_watchlist_regsho_splits_tickers}")
    unique_all_ytop_watchlist_regsho_splits_tickers = list(
    set(unique_all_ytop_regsho_splits_tickers) | set(unique_watchlist_symbols)
)
    #print(f"unique_all_ytop_watchlist_regsho_splits_tickers: {unique_all_ytop_watchlist_regsho_splits_tickers}")

    updated_symbols = []
    created_symbols = []
    stocks_to_create = []
    stocks_to_update = []



    try:
        # Loop through symbols and fetch/update stock data
        for symbol in unique_all_ytop_watchlist_regsho_splits_tickers:
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

    return JsonResponse(response_data, safe=False, status=status)




from django.shortcuts import render
from .models import StockSymbolInfo, WatchList, WatchListSymbol


def stock_info_view(request):
    # Utility function to format numbers for display
    def format_big_number(number):
        return format(number, ",") if number is not None else None
    
        # Utility function to format percentages
    def format_percentage(value):
        return f"{value * 100:.1f}" if value is not None else 0
    


    # Fetch user watchlists
    user_watchlists = WatchList.objects.filter(user=request.user)

    # Get all symbols from the user's watchlists
    watchlist_symbols = WatchListSymbol.objects.filter(watch_list__in=user_watchlists).values_list('symbol', flat=True)

    # Filter stocks based on user's watchlist symbols
    stocks = StockSymbolInfo.objects.filter(symbol__in=watchlist_symbols).values(
        'symbol', 'company_name', 'volume','averageVolume3months', 'averageVolume10days',
        'marketCap', 'fiftyTwoWeekLow', 'fiftyTwoWeekHigh', 'fiftyDayAverage',
        'floatShares', 'sharesOutstanding', 'sharesShort', 'sharesShortPriorMonth',
        'sharesShortPreviousMonthDate', 'dateShortInterest', 'shortPercentOfFloat',
        'heldPercentInsiders', 'heldPercentInstitutions', 'lastSplitFactor',
        'lastSplitDate', 'total_revenue', 'net_income', 'total_assets', 'total_liabilities', 'total_equity'
    )

    # Format the stock data for display
    formatted_stocks = []
    for stock in stocks:
        last_split_factor = stock['lastSplitFactor']

        # Format lastSplitFactor into "1:x" or "x:1"
        if last_split_factor is not None:
            if last_split_factor < 1:
                last_split_factor = f"1:{int(1 / last_split_factor)}"
            else:
                last_split_factor = f"{int(last_split_factor)}:1"

        # Add formatted stock data
        formatted_stocks.append({
            'symbol': stock['symbol'],
            'company_name': stock['company_name'],
            'volume': format_big_number(stock['volume']),
            'averageVolume3months': format_big_number(stock['averageVolume3months']),
            'averageVolume10days': format_big_number(stock['averageVolume10days']),
            'marketCap': format_big_number(stock['marketCap']),
            'fiftyTwoWeekLow': format_big_number(stock['fiftyTwoWeekLow']),
            'fiftyTwoWeekHigh': format_big_number(stock['fiftyTwoWeekHigh']),
            'fiftyDayAverage': format_big_number(stock['fiftyDayAverage']),
            'floatShares': format_big_number(stock['floatShares']),
            'sharesOutstanding': format_big_number(stock['sharesOutstanding']),
            'sharesShort': format_big_number(stock['sharesShort']),
            'sharesShortPriorMonth': format_big_number(stock['sharesShortPriorMonth']),
            'sharesShortPreviousMonthDate': stock['sharesShortPreviousMonthDate'],  # Dates don't need formatting
            'dateShortInterest': stock['dateShortInterest'],  # Dates don't need formatting

            'shortPercentOfFloat': format_percentage(stock['shortPercentOfFloat']),
            'heldPercentInsiders': format_percentage(stock['heldPercentInsiders']),
            'heldPercentInstitutions': format_percentage(stock['heldPercentInstitutions']),
            

            'lastSplitFactor': last_split_factor,
            'lastSplitDate': stock['lastSplitDate'],  # Dates don't need formatting
            'total_revenue': format_big_number(stock['total_revenue']),
            'net_income': format_big_number(stock['net_income']),
            'total_assets': format_big_number(stock['total_assets']),
            'total_liabilities': format_big_number(stock['total_liabilities']),
            'total_equity': format_big_number(stock['total_equity']),
        })
        #all_watch_lists = WatchList.objects.all()
    if request.user.is_authenticated:
        all_watch_lists = WatchList.objects.filter(user=request.user).order_by('order')
    else:
        all_watch_lists = []

    # Render the data into an HTML table
    return render(request, 'stock_info_table.html', {'stocks': formatted_stocks,'all_watch_lists': all_watch_lists})






from django.shortcuts import render





from django.http import JsonResponse
from datetime import datetime
import pandas as pd

def get_chart_data(request):
    # Define a list to store the data for each symbol
    symbols_data = []

    # Fetch user watchlists
    user_watchlists = WatchList.objects.filter(user=request.user)

    # Get the first 20 symbols from the user's watchlists
    watchlist_symbols = WatchListSymbol.objects.filter(watch_list__in=user_watchlists)[:20].values_list('symbol', flat=True)

    symbols_to_search = watchlist_symbols
    charts_html = []
    # Dates for querying data
    start_date = datetime.now()
    end_date = start_date - timedelta(days=90)
    # Generate datetime objects directly
    #dates = [start_date - timedelta(days=i) for i in range((start_date - end_date).days + 1)]

    def check_news_each_day(ticker, date_range):
        stock = yf.Ticker(ticker)
        news = stock.news
        news_links = []
        hover_texts = []  # To hold the news title for hover text

        for single_date in date_range:
            news_link = ""
            hover_text = ""
            for article in news:
                article_date = datetime.utcfromtimestamp(article['providerPublishTime']).date()
                if article_date == single_date.date():
                    # Link and title for hover text
                    news_link = f"<a href='{article['link']}' target='_blank'>N</a>"
                    hover_text = article['title']
                    break
            news_links.append(news_link or " ")
            hover_texts.append(hover_text or " ")
        return news_links, hover_texts


    def check_sec_filing_each_day(symbol, date_range):
        sec_links = []
        form_types = []  # To hold FormType for text display on top of the bars
        hover_texts = []  # To hold FormDescription for hover text display

        # Construct the file path within the function
        file_path = os.path.join(settings.BASE_DIR, "data", "sec_data_symbols.json")   
        # Print the file path to see where Django is looking (optional)
        #print(f"Looking for file at: {file_path}")
        
        # Attempt to open the file and load ticker data
        try:
            with open(file_path, "r") as f:
                sec_data_all_symbols = json.load(f)
        except FileNotFoundError:
            # Return a response indicating the file was not found
            return HttpResponse(f"File not found at path: {file_path}", status=404)
        
        filings = sec_data_all_symbols.get(symbol, [])  # Retrieve filings for the specific symbol

        for single_date in date_range:
            sec_link = ""
            form_type = ""
            hover_text = ""
            for filing in filings:
                filing_date = datetime.strptime(filing['FilingDate'], '%Y-%m-%d').date()
                if filing_date == single_date.date():
                    # Check for DocumentURL, fallback to FilingHref if not available
                    if 'DocumentURL' in filing and filing['DocumentURL']:
                        sec_link = f"<a href='{filing['DocumentURL']}' target='_blank'>{filing['FormType']}</a>"
                    else:
                        sec_link = f"<a href='{filing['FilingHref']}' target='_blank'>{filing['FormType']}</a>"
                    form_type = filing['FormType']
                    hover_text = filing['FormDescription']
                    break
            sec_links.append(sec_link or " ")
            form_types.append(form_type or " ")
            hover_texts.append(hover_text or " ")
        return sec_links, form_types, hover_texts
    
    # It will Check Reg show symbol dates
    def check_symbol_dates(df, symbol):
        symbol_data = df[df['Symbol'] == symbol]
        if symbol_data.empty:
            return None
        
        first_appearance = symbol_data['Date'].min()
        last_appearance = symbol_data['Date'].max()
        current_date = df['Date'].max()
        
        if last_appearance == current_date:
            return {
                'En.': first_appearance,
                'Con.': current_date
            }
        else:
            return {
                'En.': first_appearance,
                'Ex.': last_appearance
            }

   

    # Fetch data from Django models
    combined_sho_data = ThreeMonthsRegSHO.objects.filter(Date__range=[end_date, start_date]).order_by('-Date')
    combined_data = ThreeMonthsShortVolume.objects.filter(Date__range=[end_date, start_date]).order_by('-Date')

    # Convert to DataFrame
    combined_sho_df = pd.DataFrame(list(combined_sho_data.values()))
    combined_data_df = pd.DataFrame(list(combined_data.values()))

    # Ensure Date columns are timezone-naive UTC
    combined_sho_df['Date'] = pd.to_datetime(combined_sho_df['Date']).dt.tz_localize(None)
    combined_data_df['Date'] = pd.to_datetime(combined_data_df['Date']).dt.tz_localize(None)

    # Download data for '3mo' and if it fails due to a Error, it will try for '1mo'.
    def safe_download(symbol, period='3mo'):
        try:
            # Try fetching the data for the default period (3 months)
            data = yf.download(symbol, period=period, interval='1d')
            if data.empty:
                raise ValueError(f"No data returned for {symbol} using period {period}")
            return data
        except ValueError as e:
            # If there is an error or empty data, fall back to '1mo'
            if period == '3mo':
                print(f"Failed to download {symbol} data for '3mo': {e}, retrying with '1mo'")
                return yf.download(symbol, period='1mo', interval='1d')
            else:
                # If the fallback fails, propagate the exception
                raise

    # Iterate over each symbol to collect data
    for symbol in symbols_to_search:
        # Replace these placeholders with actual data fetching logic
        # Fetch stock info
        stock_info = yf.Ticker(symbol)
        float_shares = stock_info.info.get('floatShares', 0)
        formatted_fl_share = format(float_shares, ",")


        # Fetch summary data
        summary_info = stock_info.info
            
        # Summary
        days_range = (f"{summary_info.get('dayLow'):,}", f"{summary_info.get('dayHigh'):,}")
        fifty_two_week_range = (f"{summary_info.get('fiftyTwoWeekLow'):,}", f"{summary_info.get('fiftyTwoWeekHigh'):,}")
        market_capital = f"{summary_info.get('marketCap'):,}" if summary_info.get('marketCap') else None
        avg_volume_3m = f"{summary_info.get('averageVolume'):,}" if summary_info.get('averageVolume') else None
        avg_volume_10d = f"{summary_info.get('averageVolume10days'):,}" if summary_info.get('averageVolume10days') else None

        # Share Statistics
        outstanding_share = f"{summary_info.get('sharesOutstanding'):,}" if summary_info.get('sharesOutstanding') else None
        float_shares = f"{summary_info.get('floatShares'):,}" if summary_info.get('floatShares') else None
        held_by_insiders = f"{summary_info.get('heldPercentInsiders') * 100:.2f}%" if summary_info.get('heldPercentInsiders') else None
        held_by_institutions = f"{summary_info.get('heldPercentInstitutions') * 100:.2f}%" if summary_info.get('heldPercentInstitutions') else None
        shares_short = f"{summary_info.get('sharesShort'):,}" if summary_info.get('sharesShort') else None
        shares_short_date = summary_info.get('dateShortInterest')  # Assuming this is already a date format, no commas needed
        short_percent_float = f"{summary_info.get('shortPercentOfFloat') * 100:.2f}%" if summary_info.get('shortPercentOfFloat') else None

        # Financials
        financials = stock_info.financials
        balance_sheet = stock_info.balance_sheet
        
        # Use .iloc to safely extract values by index position
        try:
            revenue = f"{financials.loc['Total Revenue'].iloc[0]:,}" if 'Total Revenue' in financials.index and financials.loc['Total Revenue'].iloc[0] else "N/A"
            net_income = f"{financials.loc['Net Income'].iloc[0]:,}" if 'Net Income' in financials.index and financials.loc['Net Income'].iloc[0] else "N/A"
            total_assets = f"{balance_sheet.loc['Total Assets'].iloc[0]:,}" if 'Total Assets' in balance_sheet.index and balance_sheet.loc['Total Assets'].iloc[0] else "N/A"
            total_liabilities = f"{balance_sheet.loc['Total Liabilities Net Minority Interest'].iloc[0]:,}" if 'Total Liabilities Net Minority Interest' in balance_sheet.index and balance_sheet.loc['Total Liabilities Net Minority Interest'].iloc[0] else "N/A"
            total_equity = f"{balance_sheet.loc['Total Stockholder Equity'].iloc[0]:,}" if 'Total Stockholder Equity' in balance_sheet.index and balance_sheet.loc['Total Stockholder Equity'].iloc[0] else "N/A"
        except (KeyError, IndexError, AttributeError) as e:
            # If an error occurs, set all financials to 'N/A'
            revenue = net_income = total_assets = total_liabilities = total_equity = "N/A"

        # Get the earnings date with error handling
        try:
            earnings_date = stock_info.calendar.loc['Earnings Date'].iloc[0] if 'Earnings Date' in stock_info.calendar.index else "N/A"
        except (IndexError, KeyError, AttributeError):
            earnings_date = "N/A"

        # Fetch historical stock splits
        splits = stock_info.splits

        if not splits.empty:
            # Get the most recent split
            last_split_date = splits.index[-1]
            last_split_ratio = splits.iloc[-1]

            # Convert the split ratio to a "1:x" format
            split_ratio_formatted = f"1:{int(1 / last_split_ratio)}" if last_split_ratio < 1 else f"{int(last_split_ratio)}:1"

            #print(f"Last Split Date: {last_split_date}")
            #print(f"Last Split Ratio: {split_ratio_formatted}")

        else:
            split_ratio_formatted = None
            last_split_date = None

        # Prepare data
        combined_sho_df['Date'] = pd.to_datetime(combined_sho_df['Date'])
        symbol_sho_data = combined_sho_df[combined_sho_df['Symbol'] == symbol]

        combined_data_df['Date'] = pd.to_datetime(combined_data_df['Date'])
        symbol_short_volume = combined_data_df[combined_data_df['Symbol'] == symbol]

        # Fetch historical stock data
        stock_data = safe_download(symbol)
        stock_data.reset_index(inplace=True)
        stock_data['Date'] = pd.to_datetime(stock_data['Date']).dt.tz_localize(None)  # Standardize time zone for Yahoo data
        stock_data = stock_data.merge(symbol_short_volume[['Date', 'ShortVolume']], on='Date', how='left').set_index('Date')

        # Calculate colors and bar widths for the plot
        colors = ['green' if close > open else 'red' for open, close in zip(stock_data['Open'], stock_data['Close'])]
        dates = pd.to_datetime(stock_data.index)
        if len(dates) > 1:
            # Calculate the median time difference between consecutive dates
            date_diffs = (dates[1:] - dates[:-1]).median()
            bar_width = date_diffs.total_seconds() * 1000 * 0.8  # Convert to milliseconds and set width to 80% of interval
        else:
            # Default bar width if there is not enough data
            bar_width = 86400000 * 0.8  # Default to 80% of a day (in milliseconds) if there's not enough data


        # Fetch news data for the period
        news_labels, news_hover_texts = check_news_each_day(symbol, dates)
        sec_links, form_types, sec_hover_texts = check_sec_filing_each_day(symbol, dates)
 

        # Shift the 'Close' column by one day to get the previous day's close
        stock_data['PreviousClose'] = stock_data['Close'].shift(1)

        # Calculate the percentage change from previous close to current close
        stock_data['PriceChangePercent'] = ((stock_data['Close'] - stock_data['PreviousClose']) / stock_data['PreviousClose']) * 100

        # Format the text for annotations based on PriceChangePercent
        price_change_text = [
            f"{change:.2f}" if not pd.isna(change) else "" for change in stock_data['PriceChangePercent']
        ]

       # Calculate daily Open to High price change in %
        stock_data['OHPriceChangePercent'] = ((stock_data['High'] - stock_data['Open']) / stock_data['Open']) * 100
        O_H_price_change_text = [
        f"{change:.2f}" for change in stock_data['OHPriceChangePercent']
        ]

        # Calculate daily Previous close to High price change in %
        stock_data['PreCloseToHighPriceChangePercent'] = ((stock_data['High'] - stock_data['PreviousClose']) / stock_data['PreviousClose']) * 100
        Pre_C_H_price_change_text = [
        f"{change:.2f}" for change in stock_data['PreCloseToHighPriceChangePercent']
        ]


        # Add color for positive/negative change
        price_change_color = ['green' if change > 0 else 'red' for change in stock_data['PriceChangePercent'].fillna(0)]
        OH_price_change_color = ['green' if change > 0 else 'red' for change in stock_data['OHPriceChangePercent'].fillna(0)]
        PreCloseToHigh_price_change_color = ['green' if change > 0 else 'red' for change in stock_data['PreCloseToHighPriceChangePercent'].fillna(0)]
        

        # Prepare data for JSON response
        symbol_data = {
            'symbol': symbol,
            'stock_data': stock_data.to_dict(orient='records') if isinstance(stock_data, pd.DataFrame) else None,
            'combined_sho_data': combined_sho_df.to_dict(orient='records') if isinstance(combined_sho_df, pd.DataFrame) else None,
            'splits': splits.to_dict(orient='records') if isinstance(splits, pd.DataFrame) else None,
            'days_range': days_range,
            'fifty_two_week_range': fifty_two_week_range,
            'market_capital': market_capital,
            'avg_volume_3m': avg_volume_3m,
            'avg_volume_10d': avg_volume_10d,
            'split_ratio_formatted': split_ratio_formatted,
            'last_split_date': last_split_date.strftime('%Y-%m-%d') if isinstance(last_split_date, datetime) else last_split_date,
            'outstanding_share': outstanding_share,
            'float_shares': float_shares,
            'held_by_insiders': held_by_insiders,
            'held_by_institutions': held_by_institutions,
            'shares_short': shares_short,
            'short_percent_float': short_percent_float,
            'revenue': revenue,
            'net_income': net_income,
            'total_assets': total_assets,
            'total_liabilities': total_liabilities,
            'total_equity': total_equity,
            'earnings_date': earnings_date,
            'dates': dates.to_dict(orient='records') if isinstance(dates, pd.DataFrame) else None,
            'price_change_text': price_change_text,
            'price_change_color': price_change_color,
            'OH_price_change_color': OH_price_change_color,
            'O_H_price_change_text': O_H_price_change_text,
            'PreCloseToHigh_price_change_color': PreCloseToHigh_price_change_color,
            'Pre_C_H_price_change_text': Pre_C_H_price_change_text,
            'colors': colors,
            'sec_links': sec_links,
            'sec_hover_texts': sec_hover_texts,
            'bar_width': bar_width,
            'news_hover_texts': news_hover_texts,
            'news_labels': news_labels,
        }

        # Append the data for this symbol to the list
        symbols_data.append(symbol_data)

    # Return all collected data as a JSON response
    return JsonResponse({'data': symbols_data})


def check_sec_filing_each_day(symbol, date_range):
    sec_links = []
    form_types = []  # To hold FormType for text display on top of the bars
    hover_texts = []  # To hold FormDescription for hover text display

    # Construct the file path within the function
    file_path = os.path.join(settings.BASE_DIR, "data", "sec_data_symbols.json")   
    # Print the file path to see where Django is looking (optional)
    #print(f"Looking for file at: {file_path}")
    
    # Attempt to open the file and load ticker data
    try:
        with open(file_path, "r") as f:
            sec_data_all_symbols = json.load(f)
    except FileNotFoundError:
        # Return a response indicating the file was not found
        return HttpResponse(f"File not found at path: {file_path}", status=404)
    
    filings = sec_data_all_symbols.get(symbol, [])  # Retrieve filings for the specific symbol

    for single_date in date_range:
        sec_link = ""
        form_type = ""
        hover_text = ""
        for filing in filings:
            filing_date = datetime.strptime(filing['FilingDate'], '%Y-%m-%d').date()
            if filing_date == single_date.date():
                # Check for DocumentURL, fallback to FilingHref if not available
                if 'DocumentURL' in filing and filing['DocumentURL']:
                    sec_link = f"<a href='{filing['DocumentURL']}' target='_blank'>{filing['FormType']}</a>"
                else:
                    sec_link = f"<a href='{filing['FilingHref']}' target='_blank'>{filing['FormType']}</a>"
                form_type = filing['FormType']
                hover_text = filing['FormDescription']
                break
        sec_links.append(sec_link or " ")
        form_types.append(form_type or " ")
        hover_texts.append(hover_text or " ")
    return sec_links, form_types, hover_texts

def check_symbol_dates(df, symbol):
    symbol_data = df[df['Symbol'] == symbol]
    if symbol_data.empty:
        return None
    
    first_appearance = symbol_data['Date'].min()
    last_appearance = symbol_data['Date'].max()
    current_date = df['Date'].max()
    
    if last_appearance == current_date:
        return {
            'En.': first_appearance,
            'Con.': current_date
        }
    else:
        return {
            'En.': first_appearance,
            'Ex.': last_appearance
        }


from datetime import datetime, timedelta
from django.http import JsonResponse
import pandas as pd
from .models import WatchList, WatchListSymbol, StockSymbolInfo, StockSymbolData, StockPriceData, ThreeMonthsRegSHO, ThreeMonthsShortVolume

def get_chart_data_db(request):
    # Utility function to format numbers for display
    def format_big_number(number):
        return format(number, ",") if number is not None else None
    
    # Utility function to format percentages
    def format_percentage(value):
        return f"{value * 100:.1f}" if value is not None else 0

    # Fetch user watchlists
    user_watchlists = WatchList.objects.filter(user=request.user)

    # Get all symbols from the user's watchlists
    watchlist_symbols = WatchListSymbol.objects.filter(watch_list__in=user_watchlists).values_list('symbol', flat=True)

    # Filter stocks based on user's watchlist symbols
    stocks = StockSymbolInfo.objects.filter(symbol__in=watchlist_symbols).values(
        'symbol', 'company_name', 'volume', 'averageVolume3months', 'averageVolume10days',
        'marketCap', 'fiftyTwoWeekLow', 'fiftyTwoWeekHigh', 'fiftyDayAverage',
        'floatShares', 'sharesOutstanding', 'sharesShort', 'sharesShortPriorMonth',
        'sharesShortPreviousMonthDate', 'dateShortInterest', 'shortPercentOfFloat',
        'heldPercentInsiders', 'heldPercentInstitutions', 'lastSplitFactor',
        'lastSplitDate', 'total_revenue', 'net_income', 'total_assets', 'total_liabilities', 'total_equity'
    )

    # Dates for querying data
    start_date = datetime.now()
    end_date = start_date - timedelta(days=90)

    # Format the stock data for display
    formatted_stocks = []
    for stock in stocks:
        last_split_factor = stock['lastSplitFactor']

        # Format lastSplitFactor into "1:x" or "x:1"
        if last_split_factor is not None:
            if last_split_factor < 1:
                last_split_factor = f"1:{int(1 / last_split_factor)}"
            else:
                last_split_factor = f"{int(last_split_factor)}:1"

        # Fetch the latest 90 stock price data
        stock_symbol = StockSymbolData.objects.filter(symbol=stock['symbol']).first()
        stock_data = []
        if stock_symbol:
            # Get the latest 90 records ordered by 'timestamp' in descending order
            stock_data = StockPriceData.objects.filter(stock_symbol=stock_symbol).order_by('-timestamp')[:90]

        # Extract the stock price data into a DataFrame
        stock_prices = []
        if stock_data.exists():
            df = pd.DataFrame(list(stock_data.values('timestamp', 'open', 'high', 'low', 'close', 'volume','ShortVolume','ShortExemptVolume')))
            df.rename(columns={'timestamp': 'Date'}, inplace=True)
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)

            # Convert DataFrame to dictionary, including 'Date' as a column
            stock_prices = df.reset_index().to_dict(orient='records')  # Reset index to include 'Date'

        
        # Convert stock prices with short volume to dictionary
        stock_prices_with_short_volume = stock_prices
                # Prepare data
        dates_info = check_symbol_dates(combined_sho_df, stock_symbol)

        dates = pd.to_datetime(df.index)
        #print(dates)
        #sec_links, form_types, sec_hover_texts = check_sec_filing_each_day(stock_symbol, dates)
        #print(sec_links)
        # Ensure dates is a Pandas Series for apply functionality
        dates_series = pd.Series(dates)
        #print(dates_series)
        news_presence = dates_series.apply(
            lambda d: '<br>'.join(
                f"<a href='{news['NewsLink']}' target='_blank'>N</a>"
                for news in NewsData.objects.filter(
                    news_symbol__symbol=stock_symbol, Date=d.date()
                ).values('NewsLink')
            ) if NewsData.objects.filter(
                news_symbol__symbol=stock_symbol, Date=d.date()
            ).exists() else ''
        )
        news_hovertext = df.index.map(
            lambda d: '<br>'.join(
                f"Title: {news['NewsTitle']}<br>Publish Time: {news['providerPublishTime']}"
                for news in NewsData.objects.filter(
                    news_symbol__symbol=stock_symbol, Date=d.date()
                ).values('NewsTitle', 'providerPublishTime')
            ) if NewsData.objects.filter(news_symbol__symbol=stock_symbol, Date=d.date()).exists() else ''
        )
        #print(news_presence)
        # Add formatted stock data including stock prices and short volume
        formatted_stocks.append({
            'symbol': stock['symbol'],
            'company_name': stock['company_name'],
            'volume': format_big_number(stock['volume']),
            'averageVolume3months': format_big_number(stock['averageVolume3months']),
            'averageVolume10days': format_big_number(stock['averageVolume10days']),
            'marketCap': format_big_number(stock['marketCap']),
            'fiftyTwoWeekLow': format_big_number(stock['fiftyTwoWeekLow']),
            'fiftyTwoWeekHigh': format_big_number(stock['fiftyTwoWeekHigh']),
            'fiftyDayAverage': format_big_number(stock['fiftyDayAverage']),
            'floatShares': format_big_number(stock['floatShares']),
            'sharesOutstanding': format_big_number(stock['sharesOutstanding']),
            'sharesShort': format_big_number(stock['sharesShort']),
            'sharesShortPriorMonth': format_big_number(stock['sharesShortPriorMonth']),
            'sharesShortPreviousMonthDate': stock['sharesShortPreviousMonthDate'],
            'dateShortInterest': stock['dateShortInterest'],
            'shortPercentOfFloat': format_percentage(stock['shortPercentOfFloat']),
            'heldPercentInsiders': format_percentage(stock['heldPercentInsiders']),
            'heldPercentInstitutions': format_percentage(stock['heldPercentInstitutions']),
            'lastSplitFactor': last_split_factor,
            'lastSplitDate': stock['lastSplitDate'],
            'total_revenue': format_big_number(stock['total_revenue']),
            'net_income': format_big_number(stock['net_income']),
            'total_assets': format_big_number(stock['total_assets']),
            'total_liabilities': format_big_number(stock['total_liabilities']),
            'total_equity': format_big_number(stock['total_equity']),
            'stock_prices': stock_prices_with_short_volume,  # Include stock price data with short volume
            #'combined_sho_df': combined_sho_df.to_dict(orient='records')  # Include combined short data
        })

    # Return all collected data as a JSON response
    return JsonResponse({'data': formatted_stocks})

def get_chart_data_db(request):
    # Utility function to format numbers for display
    def format_big_number(number):
        return format(number, ",") if number is not None else None
    
    # Utility function to format percentages
    def format_percentage(value):
        return f"{value * 100:.1f}" if value is not None else 0

    # Fetch user watchlists
    user_watchlists = WatchList.objects.filter(user=request.user)

    # Get all symbols from the user's watchlists
    watchlist_symbols = WatchListSymbol.objects.filter(watch_list__in=user_watchlists).values_list('symbol', flat=True)

    # Filter stocks based on user's watchlist symbols
    stocks = StockSymbolInfo.objects.filter(symbol__in=watchlist_symbols).values(
        'symbol', 'company_name', 'volume', 'averageVolume3months', 'averageVolume10days',
        'marketCap', 'fiftyTwoWeekLow', 'fiftyTwoWeekHigh', 'fiftyDayAverage',
        'floatShares', 'sharesOutstanding', 'sharesShort', 'sharesShortPriorMonth',
        'sharesShortPreviousMonthDate', 'dateShortInterest', 'shortPercentOfFloat',
        'heldPercentInsiders', 'heldPercentInstitutions', 'lastSplitFactor',
        'lastSplitDate', 'total_revenue', 'net_income', 'total_assets', 'total_liabilities', 'total_equity'
    )

    # Dates for querying data
    start_date = datetime.now()
    end_date = start_date - timedelta(days=90)

    # Format the stock data for display
    formatted_stocks = []
    for stock in stocks:
        last_split_factor = stock['lastSplitFactor']

        # Format lastSplitFactor into "1:x" or "x:1"
        if last_split_factor is not None:
            if last_split_factor < 1:
                last_split_factor = f"1:{int(1 / last_split_factor)}"
            else:
                last_split_factor = f"{int(last_split_factor)}:1"

        # Fetch the latest 90 stock price data
        stock_symbol = StockSymbolData.objects.filter(symbol=stock['symbol']).first()
        stock_data = []
        if stock_symbol:
            # Get the latest 90 records ordered by 'timestamp' in descending order
            stock_data = StockPriceData.objects.filter(stock_symbol=stock_symbol).order_by('-timestamp')[:90]

        # Extract the stock price data into a DataFrame
        stock_prices = []
        if stock_data.exists():
            df = pd.DataFrame(list(stock_data.values('timestamp', 'open', 'high', 'low', 'close', 'volume','ShortVolume','ShortExemptVolume')))
            df.rename(columns={'timestamp': 'Date'}, inplace=True)
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)

            # Convert DataFrame to dictionary, including 'Date' as a column
            stock_prices = df.reset_index().to_dict(orient='records')  # Reset index to include 'Date'

        print(stock_prices)
        # Convert stock prices with short volume to dictionary
        stock_prices_with_short_volume = stock_prices
                # Prepare data
        dates_info = check_symbol_dates(combined_sho_df, stock_symbol)

        dates = pd.to_datetime(df.index)
        #print(dates)
        #sec_links, form_types, sec_hover_texts = check_sec_filing_each_day(stock_symbol, dates)
        #print(sec_links)
        # Ensure dates is a Pandas Series for apply functionality
        dates_series = pd.Series(dates)
        #print(dates_series)
        news_presence = dates_series.apply(
            lambda d: '<br>'.join(
                f"<a href='{news['NewsLink']}' target='_blank'>N</a>"
                for news in NewsData.objects.filter(
                    news_symbol__symbol=stock_symbol, Date=d.date()
                ).values('NewsLink')
            ) if NewsData.objects.filter(
                news_symbol__symbol=stock_symbol, Date=d.date()
            ).exists() else ''
        )
        news_hovertext = df.index.map(
            lambda d: '<br>'.join(
                f"Title: {news['NewsTitle']}<br>Publish Time: {news['providerPublishTime']}"
                for news in NewsData.objects.filter(
                    news_symbol__symbol=stock_symbol, Date=d.date()
                ).values('NewsTitle', 'providerPublishTime')
            ) if NewsData.objects.filter(news_symbol__symbol=stock_symbol, Date=d.date()).exists() else ''
        )
        #print(news_presence)
        # Add formatted stock data including stock prices and short volume
        formatted_stocks.append({
            'symbol': stock['symbol'],
            'company_name': stock['company_name'],
            'volume': format_big_number(stock['volume']),
            'averageVolume3months': format_big_number(stock['averageVolume3months']),
            'averageVolume10days': format_big_number(stock['averageVolume10days']),
            'marketCap': format_big_number(stock['marketCap']),
            'fiftyTwoWeekLow': format_big_number(stock['fiftyTwoWeekLow']),
            'fiftyTwoWeekHigh': format_big_number(stock['fiftyTwoWeekHigh']),
            'fiftyDayAverage': format_big_number(stock['fiftyDayAverage']),
            'floatShares': format_big_number(stock['floatShares']),
            'sharesOutstanding': format_big_number(stock['sharesOutstanding']),
            'sharesShort': format_big_number(stock['sharesShort']),
            'sharesShortPriorMonth': format_big_number(stock['sharesShortPriorMonth']),
            'sharesShortPreviousMonthDate': stock['sharesShortPreviousMonthDate'],
            'dateShortInterest': stock['dateShortInterest'],
            'shortPercentOfFloat': format_percentage(stock['shortPercentOfFloat']),
            'heldPercentInsiders': format_percentage(stock['heldPercentInsiders']),
            'heldPercentInstitutions': format_percentage(stock['heldPercentInstitutions']),
            'lastSplitFactor': last_split_factor,
            'lastSplitDate': stock['lastSplitDate'],
            'total_revenue': format_big_number(stock['total_revenue']),
            'net_income': format_big_number(stock['net_income']),
            'total_assets': format_big_number(stock['total_assets']),
            'total_liabilities': format_big_number(stock['total_liabilities']),
            'total_equity': format_big_number(stock['total_equity']),
            'stock_prices': stock_prices_with_short_volume,  # Include stock price data with short volume
            #'combined_sho_df': combined_sho_df.to_dict(orient='records')  # Include combined short data
            
        })

    # Return all collected data as a JSON response
    return JsonResponse({'data': formatted_stocks})

symbols = ['MAXN','FFIE','HOLO', 'NVDA']  # Example symbols; replace with user input or dynamic data
from decimal import Decimal
def view_stock_charts(request):

    # Fetch user watchlists
    user_watchlists = WatchList.objects.filter(user=request.user)

    # Get all symbols from the user's watchlists
    watchlist_symbols = WatchListSymbol.objects.filter(watch_list__in=user_watchlists).values_list('symbol', flat=True)
    #watchlist_symbols = ['HOLO','RR']
    # Filter stocks based on user's watchlist symbols
    user_specific = request.user
    charts_with_symbol = generateCharts(symbols,user_specific)
                
    return render(request, 'stock_charts.html', {'charts_with_symbols': charts_with_symbol})

@login_required
def update_data_page(request):


    #all_watch_lists = WatchList.objects.all()
    if request.user.is_authenticated:
        all_watch_lists = WatchList.objects.filter(user=request.user).order_by('order')
    else:
        all_watch_lists = []        
    return render(request, 'update-data.html', {'all_watch_lists': all_watch_lists})



from django.http import JsonResponse
from django.db import transaction
import pandas as pd
from datetime import datetime



def update_missing_short_volume_data(request):
    """
    Updates missing ShortVolume and ShortExemptVolume fields in StockPriceData
    for a list of stock symbols based on data from ThreeMonthsShortVolume.
    """

    # Fetch user watchlists
    #user_watchlists = WatchList.objects.filter(user=request.user)

    # Get all symbols from the user's watchlists
    #watchlist_symbols = WatchListSymbol.objects.filter(watch_list__in=user_watchlists).values_list('symbol', flat=True)
    #symbols_to_update = ["AAPL", "MSFT", "GOOGL", "HOLO", "NVDA", "UBXG"]
    #symbols_to_update = watchlist_symbols
    
    #user = request.user
    #watchlist_regsho_symbols, watchlist_symbols_list = merge_watchlist_regsho_symbols()
    #top_sv_symbols = top_sv_symbol_lists()

    # Merge both lists
    #merged_symbols = watchlist_regsho_symbols + top_sv_symbols

    # Convert to set to remove duplicates and get unique symbols
    #unique_symbols = set(merged_symbols)

    # Optionally, convert back to a list if needed
    #watchlist_regsho_sv_symbols = list(unique_symbols)
    unique_all_ytop_regsho_splits_tickers = unique_all_ytop_regsho_splits_tickers_function()
    user = request.user
    user_watchlists = WatchList.objects.filter(user=user)

    # Get all unique symbols from the user's watchlists
    watchlist_symbols = list(set(
        WatchListSymbol.objects.filter(watch_list__in=user_watchlists).values_list('symbol', flat=True)
    ))
    # Convert watchlist_symbols to a set before combining
    unique_watchlist_symbols = set(watchlist_symbols)
    # | Operator: Combines two sets into a new set that contains all unique elements from both.
    #unique_all_ytop_watchlist_regsho_splits_tickers = unique_all_ytop_regsho_splits_tickers | unique_watchlist_symbols
    unique_all_ytop_watchlist_regsho_splits_tickers = list(
    set(unique_all_ytop_regsho_splits_tickers) | set(unique_watchlist_symbols)
    )
    
    results = []

    try:
        for stock_symbol in unique_all_ytop_watchlist_regsho_splits_tickers:
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

        return JsonResponse({'results': results}, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



@login_required
def setting_page(request):


    #all_watch_lists = WatchList.objects.all()
    if request.user.is_authenticated:
        all_watch_lists = WatchList.objects.filter(user=request.user).order_by('order')
    else:
        all_watch_lists = []        
    return render(request, 'account/settings.html', {'all_watch_lists': all_watch_lists})



import yfinance as yf
from django.shortcuts import render, redirect, get_object_or_404
from .models import TickerSplit
from .forms import TickerSplitForm
from datetime import date

def ticker_splits_view(request):
    if request.method == 'POST':
        form = TickerSplitForm(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            try:
                stock_info = yf.Ticker(instance.symbol)
                instance.name = stock_info.info.get('shortName', 'Unknown Name')
                instance.sector = stock_info.info.get('sector', 'Unknown Name')
            except Exception as e:
                instance.name = 'Unknown Name'
                instance.sector = 'Unknown Name'
            instance.save()
            return redirect('ticker_splits_view')
    else:
        form = TickerSplitForm()

    last_splits = TickerSplit.objects.filter(date__lt=date.today()).order_by('-date')
    next_splits = TickerSplit.objects.filter(date__gte=date.today()).order_by('date')
    #all_watch_lists = WatchList.objects.all()
    if request.user.is_authenticated:
        all_watch_lists = WatchList.objects.filter(user=request.user).order_by('order')
    else:
        all_watch_lists = []    
    return render(request, 'ticker-splits.html', {
        'form': form,
        'last_splits': last_splits,
        'next_splits': next_splits,
        'all_watch_lists': all_watch_lists
    })

def delete_split(request, pk):
    split = get_object_or_404(TickerSplit, pk=pk)
    split.delete()
    return redirect('ticker_splits_view')

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import BuyNSell
from .forms import BuySellForm
import yfinance as yf

@login_required
def buy_sell_view_old(request):
    """
    Handles the addition of new BuyNSell records and displays buy and sell transactions
    specific to the logged-in user.
    """
    if request.method == 'POST':
        form = BuySellForm(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = request.user  # Associate transaction with the logged-in user
            try:
                stock_info = yf.Ticker(instance.symbol)
                instance.name = stock_info.info.get('shortName', 'Unknown Name')
                instance.sector = stock_info.info.get('sector', 'Unknown Name')
            except Exception as e:
                instance.name = 'Unknown Name'
                instance.sector = 'Unknown Name'
            instance.save()
            return redirect('buy_sell_view')
    else:
        form = BuySellForm()

    # Filter transactions for the logged-in user
    buy_records = BuyNSell.objects.filter(user=request.user, transaction_type__in=['B', 'O']).order_by('-date')
    sell_records = BuyNSell.objects.filter(user=request.user, transaction_type='S').order_by('-date')

    # Handle watch lists if applicable
    if request.user.is_authenticated:
        all_watch_lists = WatchList.objects.filter(user=request.user).order_by('order')
    else:
        all_watch_lists = []

    return render(request, 'buy-sell.html', {
        'form': form,
        'buy_records': buy_records,
        'sell_records': sell_records,
        'all_watch_lists': all_watch_lists
    })

@login_required
def buy_sell_view(request):
    """
    Handles the addition of new BuyNSell records and displays buy and sell transactions
    specific to the logged-in user.
    """
    if request.method == 'POST':
        form = BuySellForm(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = request.user  # Associate transaction with the logged-in user
            
            # Generate order ID for buy transactions
            if instance.transaction_type == 'B':
                existing_orders = BuyNSell.objects.filter(user=request.user,symbol=instance.symbol, transaction_type='B').count()
                instance.order_id = f"{instance.symbol}-{existing_orders + 1:02d}"

            # Handle Sell transactions
            elif instance.transaction_type == 'S':
                # Ensure the selected `order_id` from the form is saved
                selected_order_id = request.POST.get('order_id', None)
                if selected_order_id:
                    instance.order_id = selected_order_id
            # Fetch stock info
            try:
                stock_info = yf.Ticker(instance.symbol)
                instance.name = stock_info.info.get('shortName', 'Unknown Name')
                instance.sector = stock_info.info.get('sector', 'Unknown Name')
            except Exception as e:
                instance.name = 'Unknown Name'
                instance.sector = 'Unknown Name'
            
            instance.save()
            return redirect('buy_sell_view')
    else:
        form = BuySellForm()

    # Filter transactions for the logged-in user
    buy_records = BuyNSell.objects.filter(user=request.user, transaction_type__in=['B', 'O']).order_by('-date')
    sell_records = BuyNSell.objects.filter(user=request.user, transaction_type='S').order_by('-date')

    # Handle watch lists if applicable
    if request.user.is_authenticated:
        all_watch_lists = WatchList.objects.filter(user=request.user).order_by('order')
    else:
        all_watch_lists = []

    return render(request, 'buy-sell.html', {
        'form': form,
        'buy_records': buy_records,
        'sell_records': sell_records,
        'all_watch_lists': all_watch_lists
    })

@login_required
def delete_transaction(request, pk):
    """
    Deletes a specific BuyNSell transaction if it belongs to the logged-in user.
    """
    transaction = get_object_or_404(BuyNSell, pk=pk, user=request.user)  # Ensure only the owner can delete
    transaction.delete()
    return redirect('buy_sell_view')

from django.http import JsonResponse

@login_required
def get_order_ids(request):
    symbol = request.GET.get('symbol', None)
    if symbol:
        order_ids = BuyNSell.objects.filter(user=request.user, symbol=symbol, transaction_type='B').values_list('order_id', flat=True)
        return JsonResponse({"order_ids": list(order_ids)})
    return JsonResponse({"order_ids": []})



def get_regsho_orderBy_SV_list_func():
    """
    Retrieves a filtered list of symbols ordered by short volume based on the latest data.

    Returns:
        list: A list of filtered symbols sorted by average short volume.
    """
    # Step 1: Find the latest date in the ThreeMonthsRegSHO model
    latest_date = ThreeMonthsRegSHO.objects.aggregate(latest=Max('Date'))['latest']
    # Step 2: Filter by the latest date and extract symbols
    top_symbols_query = ThreeMonthsRegSHO.objects.filter(Date=latest_date).order_by('Symbol')
    reg_symbols_to_search = [
        entry.Symbol for entry in top_symbols_query
        if not re.fullmatch(r'\d+', entry.Symbol)
    ]
    # Step 3: Find the latest date in the ThreeMonthsShortVolume model
    sv_latest_date = ThreeMonthsShortVolume.objects.aggregate(latest=Max('Date'))['latest']
    consecutive_date = sv_latest_date - timedelta(days=0)
    # Step 4: Calculate the average short volume for each symbol in the last 5 days
    recent_volumes = ThreeMonthsShortVolume.objects.filter(Date__range=[consecutive_date, sv_latest_date])
    symbol_averages = recent_volumes.values('Symbol').annotate(avg_short_volume=Avg('ShortVolume')).order_by('-avg_short_volume')
    # Step 5: Convert to DataFrame for filtering
    df_symbol_averages = pd.DataFrame(symbol_averages)
    # Step 6: Filter the DataFrame to only include symbols from reg_symbols_to_search
    filtered_symbol_averages = df_symbol_averages[df_symbol_averages['Symbol'].isin(reg_symbols_to_search)]
    # Step 7: Convert to a list and return
    return filtered_symbol_averages['Symbol'].tolist()

@login_required
def top_average_short_volume_charts(request):
    return handle_cached_charts_view(
        request=request,
        cache_key="top_average_short_volume_charts",
        cache_time=3600 * 8,  # 8 hours
        title_text="Top Short Volume Tickers ",
        page_path="/charts/top-average-short-volume-charts/",
        symbols_to_search_func=top_sv_symbol_lists,
        charts_with_symbols_func=generateCharts,
        heading_text_func=lambda count: f"Top Short Volume {count} Tickers - Ordered by 1D Avg Top Short Volume"
    )

@login_required
def as_of_reg_sho_charts_view(request):
    return handle_cached_charts_view(
        request=request,
        cache_key="as_of_reg_sho_charts_view",
        cache_time=3600 * 8,  # 8 hours
        title_text="Current Regsho Security Charts",
        page_path="/charts/reg-sho-charts/",
        symbols_to_search_func=get_regsho_orderBy_SV_list_func,
        charts_with_symbols_func=generateCharts,
        heading_text_func=lambda count: f"Current {count} RegSho Listed Tickers - Ordered by 1D Avg Top Short Volume"
    )

@login_required
def reg_sho_remove_list_view(request):
    return handle_cached_charts_view(
        request=request,
        cache_key="reg_sho_remove_list_view",
        cache_time=3600 * 8,  # 8 hours
        title_text="Reg Sho Removed Tickers",
        page_path="/charts/reg-sho-removed-charts/",
        symbols_to_search_func=reg_sho_remove_list,
        charts_with_symbols_func=generateCharts,
        heading_text_func=lambda count: f"Reg Sho Removed {count} Tickers - Ordered by 1D Avg Top Short Volume"
    )


@login_required
def y_most_active_view(request):
    return handle_cached_charts_view(
        request=request,
        cache_key="y_most_active_view",
        cache_time=3600 * 8,  # 8 hours
        title_text="Most Active Tickers Today",
        page_path="/charts/most-active/",
        symbols_to_search_func=y_most_active,
        charts_with_symbols_func=stock_charts,
        heading_text_func=lambda count: f"Most Active {count} Tickers Today - Ordered by 1D Avg Top Short Volume"
    )

@login_required
def y_tranding_view(request):
    return handle_cached_charts_view(
        request=request,
        cache_key="y_tranding_view",
        cache_time=3600 * 8,  # 8 hours
        title_text="Most Tranding Tickers Today",
        page_path="/charts/tranding/",
        symbols_to_search_func=y_tranding,
        charts_with_symbols_func=stock_charts,
        heading_text_func=lambda count: f"Most Traning {count} Tickers Today - Ordered by 1D Avg Top Short Volume"
    )

@login_required
def y_top_gainers_view(request):
    return handle_cached_charts_view(
        request=request,
        cache_key="y_top_gainers_view",
        cache_time=3600 * 8,  # 8 hours
        title_text="Top Gainer Tickers Today",
        page_path="/charts/gainers/",
        symbols_to_search_func=y_top_gainers,
        charts_with_symbols_func=stock_charts,
        heading_text_func=lambda count: f"Top Gainer {count} Tickers Today - Ordered by 1D Avg Top Short Volume"
    )


@login_required
def y_top_losers_view(request):
    return handle_cached_charts_view(
        request=request,
        cache_key="y_top_losers_view",
        cache_time=3600 * 8,  # 8 hours
        title_text="Top Loser Tickers Today",
        page_path="/charts/losers/",
        symbols_to_search_func=y_top_losers,
        charts_with_symbols_func=stock_charts,
        heading_text_func=lambda count: f"Top Loser {count} Tickers Today - Ordered by 1D Avg Top Short Volume"
    )

from datetime import date
from .models import TickerSplit

def get_filtered_symbols_excluding_healthcare():
    """
    Fetches and filters symbols from TickerSplit, excluding those in the Healthcare sector.
    Returns:
        list: A list of symbols excluding those in the Healthcare sector, maintaining order.
    """
    # Fetch all TickerSplit objects before today, ordered by date
    last_splits = TickerSplit.objects.filter(date__lt=date.today()).order_by('-date')
    all_last_symbols = [split.symbol for split in last_splits]
    # Fetch TickerSplit objects related to the Healthcare sector before today, ordered by date
    last_splits_healthcare = TickerSplit.objects.filter(date__lt=date.today(), sector="Healthcare").order_by('-date')
    healthcare_symbols = [split.symbol for split in last_splits_healthcare]
    # Remove Healthcare symbols while maintaining order
    filtered_symbols = [symbol for symbol in all_last_symbols if symbol not in healthcare_symbols]
    return filtered_symbols

def get_filtered_symbols_healthcare():
    # Fetch TickerSplit objects related to the healthcare sector
    last_splits_healthcare = TickerSplit.objects.filter(date__lt=date.today(), sector="Healthcare").order_by('-date')
    healthcare_symbols = [split.symbol for split in last_splits_healthcare]
    return healthcare_symbols

@login_required
def last_splits_charts_view(request):
    return handle_cached_charts_view(
        request=request,
        cache_key="last_splits_charts_view",
        cache_time=3600 * 8,  # 8 hours
        title_text="Last Splits",
        page_path="/charts/last-splits-charts/",
        symbols_to_search_func=get_filtered_symbols_excluding_healthcare,
        charts_with_symbols_func=generateCharts,
        heading_text_func=lambda count: f"Last Splits {count} Tickers - Tickers (Excluding Healthcare Sector)",
        number_of_tickers=30  # Limit to 30 tickers(optional)
    )

@login_required
def last_splits_healthcare_charts_view(request):
    return handle_cached_charts_view(
        request=request,
        cache_key="last_splits_healthcare_charts_view",
        cache_time=3600 * 8,  # 8 hours
        title_text="Last Splits - Healthcare Sector",
        page_path="/charts/last-splits-healthcare-sector-charts/",
        symbols_to_search_func=get_filtered_symbols_healthcare,
        charts_with_symbols_func=generateCharts,
        heading_text_func=lambda count: f"Last Splits {count} Tickers - Healthcare Sector",
        number_of_tickers=30  # Limit to 30 tickers(optional)
    )


@login_required
def bought_excluding_healthcare_charts_view(request):
    
    return handle_cached_charts_view(
        request=request,
        cache_key="bought_excluding_healthcare_charts_view",
        cache_time=3600 * 8,  # 8 hours
        title_text="All Bought - Excluding Healthcare Sector",
        page_path="/charts/bought-excluding-healthcare-sector-charts/",
        symbols_to_search_func=lambda: get_non_healthcare_bought_tickers(request.user),
        charts_with_symbols_func=generateCharts,
        heading_text_func=lambda count: f"ALL Bought {count} Tickers - Excluding Healthcare Sector",
        number_of_tickers=30  # Limit to 30 tickers(optional)
    )


@login_required
def bought_healthcare_charts_view(request):
    
    return handle_cached_charts_view(
        request=request,
        cache_key="bought_healthcare_charts_view",
        cache_time=3600 * 8,  # 8 hours
        title_text="Bought - Healthcare Sector",
        page_path="/charts/bought-healthcare-sector-charts/",
        symbols_to_search_func=lambda: get_healthcare_bought_tickers(request.user),
        charts_with_symbols_func=generateCharts,
        heading_text_func=lambda count: f"Bought {count} Tickers - Healthcare Sector",
        number_of_tickers=30  # Limit to 30 tickers(optional)
    )

from .stock_earning_update import update_multiple_tickers_earnings
from .models import EarningsData
from django.views.decorators.csrf import csrf_exempt
import json

@login_required
def earnings_update_view(request):
    results = None
    if request.method == 'POST':
        tickers = request.POST.get('tickers', '')
        event_name = request.POST.get('event_name', '')
        earning_call_time = request.POST.get('earning_call_time', '')

        if tickers:
            results = update_multiple_tickers_earnings(
                tickers, 
                event_name=event_name if event_name else None,
                earning_call_time=earning_call_time if earning_call_time else None
            )

    return render(request, 'earnings_update_form.html', {
        'results': results,
        'title_msg': 'Update Earnings Data',
        'EVENT_CHOICES': EarningsData.EVENT_CHOICES,
        'TIME_CHOICES': EarningsData.TIME_CHOICES,
    })
def get_business_days(start_date, num_days):
    # Simplified business day calculation (skipping weekends)
    days = []
    curr = start_date
    while len(days) < num_days:
        if curr.weekday() < 5: # 0-4 is Mon-Fri
            days.append(curr)
        curr += timedelta(days=1)
    return days

@login_required
def earnings_calendar_view(request):
    # Date navigation: 2 past, today, 5 future
    today = datetime.now().date()
    
    # Get 2 previous business days
    past_dates = []
    d = today - timedelta(days=1)
    while len(past_dates) < 2:
        if d.weekday() < 5:
            past_dates.append(d)
        d -= timedelta(days=1)
    past_dates.reverse()

    # Get 5 next business days
    future_dates = []
    d = today + timedelta(days=1)
    while len(future_dates) < 5:
        if d.weekday() < 5:
            future_dates.append(d)
        d += timedelta(days=1)
        
    dates = past_dates + [today] + future_dates
    
    selected_date_str = request.GET.get('date')
    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = today
    else:
        selected_date = today
        
    # Fetch tickers having earnings on the selected date in Slot 1
    earnings_on_date = EarningsData.objects.filter(earnings_date_1=selected_date)
    
    return render(request, 'earnings_calendar.html', {
        'dates': dates, 
        'selected_date': selected_date,
        'stocks_data': earnings_on_date,
        'EVENT_CHOICES': EarningsData.EVENT_CHOICES,
        'TIME_CHOICES': EarningsData.TIME_CHOICES,
        'today': today
    })

@csrf_exempt
@require_http_methods(["POST"])
def update_earnings_field_ajax(request):
    try:
        data = json.loads(request.body)
        earnings_id = data.get('id')
        field = data.get('field') # e.g. 'event_name_1'
        value = data.get('value')
        
        entry = EarningsData.objects.get(id=earnings_id)
        # Check if the field is one of the valid slot fields
        valid_fields = []
        for i in range(1, 5):
            valid_fields.append(f'event_name_{i}')
            valid_fields.append(f'earning_call_time_{i}')
            
        if field in valid_fields:
            setattr(entry, field, value)
            entry.save()
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error', 'message': 'Invalid field'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    


from django.shortcuts import render, get_object_or_404
from .models import EarningsData, WatchList, WatchListSymbol
from django.utils.timezone import now

def big_earnings_calendar_view(request):
    user = request.user
    watchlist_name = "BigEarnings"  # you can make this dynamic later

    # Get the specific watchlist
    watchlist = get_object_or_404(
        WatchList,
        user=user,
        name=watchlist_name
    )

    # Get symbols from that watchlist
    symbols = WatchListSymbol.objects.filter(
        watch_list=watchlist
    ).values_list('symbol', flat=True).distinct()

    today = now().date()
    # Filter earnings data
    # Only upcoming (today + future)
    earnings_on_date = EarningsData.objects.filter(
        symbol__in=symbols,
        earnings_date_1__gte=today
    ).order_by('earnings_date_1')

    return render(request, 'earnings_big_calendar.html', {
        'stocks_data': earnings_on_date,
        'watchlist_name': watchlist.name,
        'EVENT_CHOICES': EarningsData.EVENT_CHOICES,
        'TIME_CHOICES': EarningsData.TIME_CHOICES,
    })

from django.db.models import Q

def recent_big_earnings_calendar_view(request):
    user = request.user
    watchlist_name = "BigEarnings"  # you can make this dynamic later

    # Get the specific watchlist
    watchlist = get_object_or_404(
        WatchList,
        user=user,
        name=watchlist_name
    )

    # Get symbols from that watchlist
    symbols = WatchListSymbol.objects.filter(
        watch_list=watchlist
    ).values_list('symbol', flat=True).distinct()


    today = now().date()

    # Filter earnings data
    # Include past dates OR NULL dates
    earnings_on_date = EarningsData.objects.filter(
        symbol__in=symbols
    ).filter(
        Q(earnings_date_1__lt=today) | Q(earnings_date_1__isnull=True)
    ).order_by('-earnings_date_1')

    return render(request, 'earnings_recent_big_calendar.html', {
        'stocks_data': earnings_on_date,
        'watchlist_name': watchlist.name,
        'EVENT_CHOICES': EarningsData.EVENT_CHOICES,
        'TIME_CHOICES': EarningsData.TIME_CHOICES,
    })
