from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import StockSymbolData, StockPriceData
from .models import DayStockSymbolInfo, WatchList, WatchListSymbol
from .models import DayStockSymbolInfo
from django.http import JsonResponse
import yfinance as yf
from .models import StockSymbolInfo, WatchList, WatchListSymbol
from .models import TickerSplit
from datetime import date
from .models import BuyNSell
from .views import top_sv_symbol_lists, get_current_regsho_symbols, reg_sho_remove_list

from .yscreener import y_most_active,y_tranding,y_top_gainers,y_top_losers
from django.shortcuts import get_object_or_404
import math

from .stock_day_info_second import stock_day_info

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




# Assuming these functions return lists of tickers
y_most_active_tickers = y_most_active()  # Example: ['AAPL', 'MSFT', 'TSLA']
y_trending_tickers = y_tranding()       # Example: ['GOOG', 'AAPL', 'AMZN']
y_top_gainers_tickers = y_top_gainers() # Example: ['TSLA', 'NVDA', 'META']
y_top_losers_tickers = y_top_losers()   # Example: ['AMZN', 'NFLX', 'TSLA']
#watchlist_regsho_symbols, watchlist_symbols_list = merge_watchlist_regsho_symbols()
top_short_volume_symbols = top_sv_symbol_lists()
reg_sho_remove_symbols = reg_sho_remove_list() 
current_regsho_symbols = get_current_regsho_symbols()
# Merging all ticker lists and ensuring uniqueness using set()

# Fetch all unique stock split symbols from the database
stock_splits_symbols_QuerySet = TickerSplit.objects.values_list('symbol', flat=True).distinct()
stock_splits_symbols = list(stock_splits_symbols_QuerySet)

unique_all_ytop_regsho_splits_tickers = set(
    y_most_active_tickers + 
    y_trending_tickers + 
    y_top_gainers_tickers + 
    y_top_losers_tickers +
    top_short_volume_symbols +
    current_regsho_symbols +
    reg_sho_remove_symbols+
    stock_splits_symbols
)

# The `unique_tickers` set now contains all unique tickers
# Printing all the lists and sets
#print(f"y_most_active_tickers: {y_most_active_tickers}")
#print(f"y_trending_tickers: {y_trending_tickers}")
#print(f"y_top_gainers_tickers: {y_top_gainers_tickers}")
#print(f"y_top_losers_tickers: {y_top_losers_tickers}")
# Uncomment and adjust the next line when `merge_watchlist_regsho_symbols` is defined
# print(f"watchlist_regsho_symbols: {watchlist_regsho_symbols}")
# print(f"watchlist_symbols_list: {watchlist_symbols_list}")
#print(f"top_short_volume_symbols: {top_short_volume_symbols}")
#print(f"reg_sho_remove_symbols: {reg_sho_remove_symbols}")
#print(f"current_regsho_symbols: {current_regsho_symbols}")
#print(f"unique_all_ytop_regsho_tickers: {unique_all_ytop_regsho_tickers}")


def update_day_stock_info(request):
    #symbols_to_update = ["AAPL", "MSFT", "GOOGL","HOLO","NVDA","UBXG"]  # Replace with the relevant symbols
        # Fetch the user's watchlists
    user = request.user
    user_watchlists = WatchList.objects.filter(user=user)

    # Get all unique symbols from the user's watchlists
    watchlist_symbols = list(set(
        WatchListSymbol.objects.filter(watch_list__in=user_watchlists).values_list('symbol', flat=True)
    ))
    # Convert watchlist_symbols to a set before combining
    unique_watchlist_symbols = set(watchlist_symbols)
    # | Operator: Combines two sets into a new set that contains all unique elements from both.
    unique_all_ytop_watchlist_regsho_tickers = unique_all_ytop_regsho_splits_tickers | unique_watchlist_symbols


    #print(watchlist_regsho_symbols)
    
    updated_symbols = []
    created_symbols = []
    stocks_to_create = []
    stocks_to_update = []

    try:
        for symbol in unique_all_ytop_watchlist_regsho_tickers:
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

    return JsonResponse(response_data, safe=False, status=status)


def stock_day_info_watchList_view(request):
    # Utility function to format numbers for display
    

    # Fetch user watchlists
    user_watchlists = WatchList.objects.filter(user=request.user)

    # Get all symbols from the user's watchlists
    watchlist_symbols = WatchListSymbol.objects.filter(watch_list__in=user_watchlists).values_list('symbol', flat=True)

    formatted_day_stocks = stock_day_info(watchlist_symbols)
    # Fetch all watchlists for authenticated user
    if request.user.is_authenticated:
        all_watch_lists = WatchList.objects.filter(user=request.user).order_by('order')
    else:
        all_watch_lists = []

    msg = 'Watch Lists'
    # Render the data into an HTML table
    return render(request, 'stock_day_info_table.html', {
        'day_stocks': formatted_day_stocks,
        'all_watch_lists': all_watch_lists,
        'nav_text': msg
    })

def stock_day_info_watchList_info_homepage_view(request):
    # Utility function to format numbers for display
    

    # Fetch user watchlists
    user_watchlists = WatchList.objects.filter(user=request.user)

    # Get all symbols from the user's watchlists
    watchlist_symbols = WatchListSymbol.objects.filter(watch_list__in=user_watchlists).values_list('symbol', flat=True)

    formatted_day_stocks = stock_day_info(watchlist_symbols)
    # Fetch all watchlists for authenticated user
    if request.user.is_authenticated:
        all_watch_lists = WatchList.objects.filter(user=request.user).order_by('order')
    else:
        all_watch_lists = []

    msg = 'Watch Lists'
    # Render the data into an HTML table
    return render(request, 'stock-day-info-table-watch-list-info.html', {
        'day_stocks': formatted_day_stocks,
        'all_watch_lists': all_watch_lists,
        'nav_text': msg
    })



def stock_day_info_most_active_view(request):

    # Fetch user watchlists
    y_most_active_tickers = y_most_active()

    formatted_day_stocks = stock_day_info(y_most_active_tickers)

    # Fetch all watchlists for authenticated user
    if request.user.is_authenticated:
        all_watch_lists = WatchList.objects.filter(user=request.user).order_by('order')
    else:
        all_watch_lists = []
    msg = 'Most Active'
    # Render the data into an HTML table
    return render(request, 'stock_day_info_table.html', {
        'day_stocks': formatted_day_stocks,
        'all_watch_lists': all_watch_lists,
        'nav_text': msg
    })


def stock_day_info_tranding_view(request):

    # Fetch user watchlists
    y_tranding_tickers = y_tranding()

    formatted_day_stocks = stock_day_info(y_tranding_tickers)

    # Fetch all watchlists for authenticated user
    if request.user.is_authenticated:
        all_watch_lists = WatchList.objects.filter(user=request.user).order_by('order')
    else:
        all_watch_lists = []

    msg = 'Tranding'
    # Render the data into an HTML table
    return render(request, 'stock_day_info_table.html', {
        'day_stocks': formatted_day_stocks,
        'all_watch_lists': all_watch_lists,
        'nav_text': msg
    })


def stock_day_info_top_gainers_view(request):

    # Fetch user watchlists
    y_top_gainers_tickers = y_top_gainers()

    formatted_day_stocks = stock_day_info(y_top_gainers_tickers)

    # Fetch all watchlists for authenticated user
    if request.user.is_authenticated:
        all_watch_lists = WatchList.objects.filter(user=request.user).order_by('order')
    else:
        all_watch_lists = []

    msg = 'Top Gainers'
    # Render the data into an HTML table
    return render(request, 'stock_day_info_table.html', {
        'day_stocks': formatted_day_stocks,
        'all_watch_lists': all_watch_lists,
        'nav_text': msg
    })

def stock_day_info_top_losers_view(request):

    # Fetch user watchlists
    y_top_losers_tickers = y_top_losers()

    formatted_day_stocks = stock_day_info(y_top_losers_tickers)

    # Fetch all watchlists for authenticated user
    if request.user.is_authenticated:
        all_watch_lists = WatchList.objects.filter(user=request.user).order_by('order')
    else:
        all_watch_lists = []

    msg = 'Top Losers'
    # Render the data into an HTML table
    return render(request, 'stock_day_info_table.html', {
        'day_stocks': formatted_day_stocks,
        'all_watch_lists': all_watch_lists,
        'nav_text': msg
    })

#print(top_short_volume_symbols)
def stock_day_info_top_SV_view(request):

    # Fetch user watchlists

    formatted_day_stocks = stock_day_info(top_short_volume_symbols)

    # Fetch all watchlists for authenticated user
    if request.user.is_authenticated:
        all_watch_lists = WatchList.objects.filter(user=request.user).order_by('order')
    else:
        all_watch_lists = []

    msg = 'Top Short Volume'
    # Render the data into an HTML table
    return render(request, 'stock_day_info_table.html', {
        'day_stocks': formatted_day_stocks,
        'all_watch_lists': all_watch_lists,
        'nav_text': msg
    })



def stock_day_info_reg_show_view(request):

    # Fetch user watchlists
    current_regsho_symbols = get_current_regsho_symbols()

    formatted_day_stocks = stock_day_info(current_regsho_symbols)

    # Fetch all watchlists for authenticated user
    if request.user.is_authenticated:
        all_watch_lists = WatchList.objects.filter(user=request.user).order_by('order')
    else:
        all_watch_lists = []

    msg = 'Reg Sho Tickers'
    # Render the data into an HTML table
    return render(request, 'stock_day_info_table.html', {
        'day_stocks': formatted_day_stocks,
        'all_watch_lists': all_watch_lists,
        'nav_text': msg
    })
def stock_day_info_reg_sho_remove_tickers_view(request):

    # Fetch user watchlists
    reg_sho_remove_symbols = reg_sho_remove_list() 

    formatted_day_stocks = stock_day_info(reg_sho_remove_symbols)

    # Fetch all watchlists for authenticated user
    if request.user.is_authenticated:
        all_watch_lists = WatchList.objects.filter(user=request.user).order_by('order')
    else:
        all_watch_lists = []

    msg = 'Reg Sho Removed Tickers'
    # Render the data into an HTML table
    return render(request, 'stock_day_info_table.html', {
        'day_stocks': formatted_day_stocks,
        'all_watch_lists': all_watch_lists,
        'nav_text': msg
    })

def stock_day_info_watchlists_tickers_view(request,watch_list_str):

    # Fetch user watchlists
    # Determine the watch list name
    watch_list_name = request.GET.get('watch_list', watch_list_str)
    
    # Fetch the watch list specific to the user
    watch_list = get_object_or_404(WatchList, name=watch_list_name, user=request.user)

    # Get symbols associated with the watch list
    symbols_to_search = list(WatchListSymbol.objects.filter(watch_list=watch_list).values_list('symbol', flat=True))
    symbols_to_search = [symbol.upper() for symbol in symbols_to_search]

    #print(f"watch list symbols{symbols_to_search}")

    formatted_day_stocks = stock_day_info(symbols_to_search)

    # Fetch all watchlists for authenticated user
    if request.user.is_authenticated:
        all_watch_lists = WatchList.objects.filter(user=request.user).order_by('order')
    else:
        all_watch_lists = []

    msg = watch_list_name
    # Render the data into an HTML table
    return render(request, 'stock_day_info_table.html', {
        'day_stocks': formatted_day_stocks,
        'all_watch_lists': all_watch_lists,
        'nav_text': msg
    })


def stock_day_info_splits_all_tickers(request):

    # Fetch all symbols as a list
    all_splits_tickers = TickerSplit.objects.values_list('symbol', flat=True)
    symbols_to_search=list(all_splits_tickers)
    #print(f"TickerSplit: {symbols_to_search}")

    formatted_day_stocks = stock_day_info(symbols_to_search)

    # Fetch all watchlists for authenticated user
    if request.user.is_authenticated:
        all_watch_lists = WatchList.objects.filter(user=request.user).order_by('order')
    else:
        all_watch_lists = []

    msg = 'Stock Splits Tickers'
    # Render the data into an HTML table
    return render(request, 'stock_day_info_table.html', {
        'day_stocks': formatted_day_stocks,
        'all_watch_lists': all_watch_lists,
        'nav_text': msg
    })

def stock_day_info_last_splits_tickers(request):

    # Fetch all symbols as a list
    last_splits = TickerSplit.objects.filter(date__lt=date.today()).order_by('-date')
    all_last_symbols = [split.symbol for split in last_splits]

    # Fetch TickerSplit objects related to the healthcare sector
    last_splits_healthcare = TickerSplit.objects.filter(date__lt=date.today(), sector="Healthcare").order_by('-date')
    healthcare_symbols = [split.symbol for split in last_splits_healthcare]

    # Remove healthcare symbols from the overall list
    #filtered_symbols = [symbol for symbol in all_last_symbols if symbol not in healthcare_symbols]
    # Remove healthcare symbols using set difference
    #filtered_symbols = list(set(all_last_symbols) - set(healthcare_symbols))
    # Remove healthcare symbols while maintaining order
    filtered_symbols = [symbol for symbol in all_last_symbols if symbol not in healthcare_symbols]

    # Get the first 30 symbols
    #first_30_symbols = filtered_symbols[:30]

    #print(f"first_30_symbols: {first_30_symbols}")
  
    #print(filtered_symbols)
    symbols_to_search = filtered_symbols
    #print(f"Ticker Last Split(Excluding healthcare): {symbols_to_search}")

    formatted_day_stocks = stock_day_info(symbols_to_search)

    # Fetch all watchlists for authenticated user
    if request.user.is_authenticated:
        all_watch_lists = WatchList.objects.filter(user=request.user).order_by('order')
    else:
        all_watch_lists = []

    msg = 'Last Splits Tickers(Excluding healthcare sector)'
    # Render the data into an HTML table
    return render(request, 'stock_day_info_table.html', {
        'day_stocks': formatted_day_stocks,
        'all_watch_lists': all_watch_lists,
        'nav_text': msg
    })

def stock_day_info_upcoming_splits_tickers(request):

    # Fetch all symbols as a list
    upcoming_splits = TickerSplit.objects.filter(date__gte=date.today())
    # Extract the tickers into a list
    symbols_to_search = [split.symbol for split in upcoming_splits] 
    
    #print(f"Ticker upcoming Split: {symbols_to_search}")

    formatted_day_stocks = stock_day_info(symbols_to_search)

    # Fetch all watchlists for authenticated user
    if request.user.is_authenticated:
        all_watch_lists = WatchList.objects.filter(user=request.user).order_by('order')
    else:
        all_watch_lists = []

    msg = 'Upcoming Splits Tickers'
    # Render the data into an HTML table
    return render(request, 'stock_day_info_table.html', {
        'day_stocks': formatted_day_stocks,
        'all_watch_lists': all_watch_lists,
        'nav_text': msg
    })

def stock_day_info_last_splits_healthcare_tickers(request):

    # Fetch TickerSplit objects with date < today and sector = "Healthcare"
    last_splits_healthcare = TickerSplit.objects.filter(date__lt=date.today(), sector="Healthcare").order_by('-date')
    # Extract the tickers into a list
    symbols_to_search = [split.symbol for split in last_splits_healthcare] 
    
    #print(f"Ticker Last Split Healthcare: {symbols_to_search}")

    formatted_day_stocks = stock_day_info(symbols_to_search)

    # Fetch all watchlists for authenticated user
    if request.user.is_authenticated:
        all_watch_lists = WatchList.objects.filter(user=request.user).order_by('order')
    else:
        all_watch_lists = []

    msg = 'Last Splits Healthcare Tickers'
    # Render the data into an HTML table
    return render(request, 'stock_day_info_table.html', {
        'day_stocks': formatted_day_stocks,
        'all_watch_lists': all_watch_lists,
        'nav_text': msg
    })

def stock_day_info_all_bought_tickers(request):

    # Fetch all "Buy" symbols for the logged-in user, ordered by date (latest first), and eliminate duplicates
    if request.user.is_authenticated:
        all_bought_tickers = BuyNSell.objects.filter(
            user=request.user, transaction_type="B"
        ).order_by('-date').values_list('symbol', flat=True)
        # Remove duplicates while maintaining order
        symbols_to_search = list(dict.fromkeys(all_bought_tickers))
    else:
        symbols_to_search = []  # No symbols if the user is not authenticated



    #print(f"Ticker All bought: {symbols_to_search}")

    formatted_day_stocks = stock_day_info(symbols_to_search)

    # Fetch all watchlists for authenticated user
    if request.user.is_authenticated:
        all_watch_lists = WatchList.objects.filter(user=request.user).order_by('order')
    else:
        all_watch_lists = []

    msg = 'Last All Bought Tickers'
    # Render the data into an HTML table
    return render(request, 'stock_day_info_table.html', {
        'day_stocks': formatted_day_stocks,
        'all_watch_lists': all_watch_lists,
        'nav_text': msg
    })
def stock_day_info_healthcare_bought_tickers(request):

    # Fetch all "Healthcare" symbols for the logged-in user with transaction_type "B", ordered by date (latest first), and remove duplicates
    if request.user.is_authenticated:
        healthcare_bought_tickers = BuyNSell.objects.filter(
            user=request.user, sector="Healthcare", transaction_type="B"
        ).order_by('-date').values_list('symbol', flat=True)
        # Remove duplicates while maintaining order
        symbols_to_search = list(dict.fromkeys(healthcare_bought_tickers))
    else:
        symbols_to_search = []  # No symbols if the user is not authenticated

    #print(f"Bought Tickers for Healthcare: {symbols_to_search}")

    formatted_day_stocks = stock_day_info(symbols_to_search)

    # Fetch all watchlists for authenticated user
    if request.user.is_authenticated:
        all_watch_lists = WatchList.objects.filter(user=request.user).order_by('order')
    else:
        all_watch_lists = []

    msg = 'Healthcare Bought Tickers'
    # Render the data into an HTML table
    return render(request, 'stock_day_info_table.html', {
        'day_stocks': formatted_day_stocks,
        'all_watch_lists': all_watch_lists,
        'nav_text': msg
    })