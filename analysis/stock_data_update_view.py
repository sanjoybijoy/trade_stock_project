from .yscreener import y_most_active,y_tranding,y_top_gainers,y_top_losers
from .stock_data_db_tickers_load import(
    get_top_sv_symbol_lists, 
    get_reg_sho_remove_list, 
    get_current_regsho_symbols,

    get_all_watchlists_tickers,
    get_all_splits_tickers,
    get_all_bought_tickers,
    get_user_watchlists_tickers,
    get_user_all_bought_tickers
    
)
from .stock_data_update_utils import(
    update_news_for_tickers, 
    update_tickers_day_stock_info, 
    update_tickers_stock_info,

    update_and_merge_missing_short_volume_data,
    update_tickers_stock_data
    
)
from django.http import JsonResponse
from datetime import datetime, timedelta
import pandas as pd
from .stock_data import check_news_each_day,fetch_and_save_stock_data 
from .models import DayStockSymbolInfo,StockSymbolInfo,StockSymbolData,StockPriceData,ThreeMonthsShortVolume
from django.db import transaction
import yfinance as yf
import math
from .models import StockSymbolData,WatchList
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

# Assuming these functions return lists of tickers
y_most_active_tickers = y_most_active()  # Example: ['AAPL', 'MSFT', 'TSLA']
y_trending_tickers = y_tranding()       # Example: ['GOOG', 'AAPL', 'AMZN']
y_top_gainers_tickers = y_top_gainers() # Example: ['TSLA', 'NVDA', 'META']
y_top_losers_tickers = y_top_losers()   # Example: ['AMZN', 'NFLX', 'TSLA']

y_unique_most_active_trending_gainers_losers = set(
    y_most_active_tickers + 
    y_trending_tickers + 
    y_top_gainers_tickers + 
    y_top_losers_tickers 
)
y_unique_most_active_trending_gainers_losers_lists=list(y_unique_most_active_trending_gainers_losers)

top_short_volume_symbols = get_top_sv_symbol_lists()
current_regsho_symbols = get_current_regsho_symbols() 
reg_sho_remove_symbols = get_reg_sho_remove_list() 

unique_reg_sho_SV = set(
    top_short_volume_symbols + 
    current_regsho_symbols + 
    reg_sho_remove_symbols
 
)
unique_reg_sho_SV_list=list(unique_reg_sho_SV)

all_watchlists_tickers = get_all_watchlists_tickers()
all_splits_tickers = get_all_splits_tickers()
all_bought_tickers = get_all_bought_tickers()

unique_current_all_tickers = set(
    y_most_active_tickers + 
    y_trending_tickers + 
    y_top_gainers_tickers + 
    y_top_losers_tickers +
    top_short_volume_symbols + 
    current_regsho_symbols + 
    reg_sho_remove_symbols +
    all_watchlists_tickers +
    all_splits_tickers +
    all_bought_tickers
 
)
unique_current_all_tickers_lists=list(unique_current_all_tickers)

unique_y_sv_regsho_tickers = set(
    y_most_active_tickers + 
    y_trending_tickers + 
    y_top_gainers_tickers + 
    y_top_losers_tickers +
    top_short_volume_symbols + 
    current_regsho_symbols + 
    reg_sho_remove_symbols 
 
)
unique_y_sv_regsho_tickers_lists=list(unique_y_sv_regsho_tickers)

def get_user_current_all_tickers(user):

    user_watchlists_tickers =   get_user_watchlists_tickers(user)
    user_all_bought_tickers =   get_user_all_bought_tickers(user)

    unique_user_current_all_tickers = set(
        y_most_active_tickers + 
        y_trending_tickers + 
        y_top_gainers_tickers + 
        y_top_losers_tickers +
        top_short_volume_symbols + 
        current_regsho_symbols + 
        reg_sho_remove_symbols +
        user_watchlists_tickers +
        user_all_bought_tickers
        
        )
    unique_user_current_all_tickers_lists   =   list(unique_user_current_all_tickers)
    return unique_user_current_all_tickers_lists

# ---------------- Start Watch LIsts Tickers Update --------------------------
def update_watchlist_news_all_tickers_view(request):

    response_data,status = update_news_for_tickers(all_watchlists_tickers)
    return JsonResponse(response_data, status=status)

def update_watchlist_all_tickers_day_stock_info_view(request):

    response_data,status = update_tickers_day_stock_info(all_watchlists_tickers)
    return JsonResponse(response_data, safe=False, status=status)

def update_watchlist_all_tickers_stock_info_view(request):

    response_data,status = update_tickers_stock_info(all_watchlists_tickers)
    return JsonResponse(response_data, safe=False, status=status)

def update_and_merge_missing_short_volume_data_view(request):
 
    response_data,status = update_and_merge_missing_short_volume_data(all_watchlists_tickers)
    return JsonResponse(response_data, safe=False, status=status)


def update_watchlist_tickers_stock_data_view(request): 

    response_data,status = update_tickers_stock_data(all_watchlists_tickers)
    return JsonResponse(response_data, safe=False, status=status)
# ---------------- End Watch LIsts Tickers Update --------------------------

# ---------------- Start Most Active, Tranding, Top gainers and losers Tickers Update --------------------------
def update_y_all_news_view(request):

    response_data,status = update_news_for_tickers(y_unique_most_active_trending_gainers_losers_lists)
    return JsonResponse(response_data, status=status)

def update_y_all_day_stock_info_view(request):

    response_data,status = update_tickers_day_stock_info(y_unique_most_active_trending_gainers_losers_lists)
    return JsonResponse(response_data, safe=False, status=status)

def update_y_all_stock_info_view(request):

    response_data,status = update_tickers_stock_info(y_unique_most_active_trending_gainers_losers_lists)
    return JsonResponse(response_data, safe=False, status=status)

def update_and_merge_y_all_missing_short_volume_data_view(request):
 
    response_data,status = update_and_merge_missing_short_volume_data(y_unique_most_active_trending_gainers_losers_lists)
    return JsonResponse(response_data, safe=False, status=status)


def update_y_all_stock_data_view(request): 

    response_data,status = update_tickers_stock_data(y_unique_most_active_trending_gainers_losers_lists)
    return JsonResponse(response_data, safe=False, status=status)
# ---------------- End Most Active, Tranding, Top gainers and losers Tickers Update --------------------------


# ---------------- Start Regs Sho and Short Volume Tickers Update --------------------------
def update_regsho_SV_news_view(request):

    response_data,status = update_news_for_tickers(unique_reg_sho_SV_list)
    return JsonResponse(response_data, status=status)

def update_regsho_SV_day_stock_info_view(request):

    response_data,status = update_tickers_day_stock_info(unique_reg_sho_SV_list)
    return JsonResponse(response_data, safe=False, status=status)

def update_regsho_SV_stock_info_view(request):

    response_data,status = update_tickers_stock_info(unique_reg_sho_SV_list)
    return JsonResponse(response_data, safe=False, status=status)

def update_and_merge_regsho_SV_missing_short_volume_data_view(request):
 
    response_data,status = update_and_merge_missing_short_volume_data(unique_reg_sho_SV_list)
    return JsonResponse(response_data, safe=False, status=status)


def update_regsho_SV_stock_data_view(request): 

    response_data,status = update_tickers_stock_data(unique_reg_sho_SV_list)
    return JsonResponse(response_data, safe=False, status=status)
# ---------------- End Regs Sho and Short Volume Tickers Update --------------------------

# ---------------- Start Stock Splits Tickers Update --------------------------
def update_all_splits_tickers_news_view(request):

    response_data,status = update_news_for_tickers(all_splits_tickers)
    return JsonResponse(response_data, status=status)

def update_all_splits_tickers_day_stock_info_view(request):

    response_data,status = update_tickers_day_stock_info(all_splits_tickers)
    return JsonResponse(response_data, safe=False, status=status)

def update_all_splits_tickers_stock_info_view(request):

    response_data,status = update_tickers_stock_info(all_splits_tickers)
    return JsonResponse(response_data, safe=False, status=status)

def update_and_merge_all_splits_tickers_missing_short_volume_data_view(request):
 
    response_data,status = update_and_merge_missing_short_volume_data(all_splits_tickers)
    return JsonResponse(response_data, safe=False, status=status)


def update_all_splits_tickers_stock_data_view(request): 

    response_data,status = update_tickers_stock_data(all_splits_tickers)
    return JsonResponse(response_data, safe=False, status=status)
# ---------------- End Stock Splits Tickers Update --------------------------

# ---------------- Start Current All Tickers Update  Update --------------------------
def update_current_all_tickers_news_view(request):

    response_data,status = update_news_for_tickers(unique_current_all_tickers_lists)
    return JsonResponse(response_data, status=status)

def update_current_all_tickers_day_stock_info_view(request):

    response_data,status = update_tickers_day_stock_info(unique_current_all_tickers_lists)
    return JsonResponse(response_data, safe=False, status=status)

def update_current_all_tickers_stock_info_view(request):

    response_data,status = update_tickers_stock_info(unique_current_all_tickers_lists)
    return JsonResponse(response_data, safe=False, status=status)

def update_and_merge_current_all_tickers_missing_short_volume_data_view(request):
 
    response_data,status = update_and_merge_missing_short_volume_data(unique_current_all_tickers_lists)
    return JsonResponse(response_data, safe=False, status=status)


def update_current_all_tickers_stock_data_view(request): 

    response_data,status = update_tickers_stock_data(unique_current_all_tickers_lists)
    return JsonResponse(response_data, safe=False, status=status)
# ---------------- End Current All Tickers Update  Update --------------------------
# ---------------- Start Sidebar Data  Update --------------------------
def update_user_watchlist_tickers_news_view(request):
    user = request.user
    user_watchlists_tickers =   get_user_watchlists_tickers(user)
    response_data,status = update_news_for_tickers(user_watchlists_tickers)
    return JsonResponse(response_data, status=status)

def update_user_current_all_tickers_day_stock_info_view(request):
    user = request.user
    unique_user_current_all_tickers_lists = get_user_current_all_tickers(user)
    response_data,status = update_tickers_day_stock_info(unique_user_current_all_tickers_lists)
    return JsonResponse(response_data, safe=False, status=status)

def update_user_current_all_tickers_stock_info_view(request):
    user = request.user
    unique_user_current_all_tickers_lists = get_user_current_all_tickers(user)
    response_data,status = update_tickers_stock_info(unique_user_current_all_tickers_lists)
    return JsonResponse(response_data, safe=False, status=status)

def update_and_merge_user_current_all_tickers_missing_short_volume_data_view(request):
    user = request.user
    unique_user_current_all_tickers_lists = get_user_current_all_tickers(user)
    response_data,status = update_and_merge_missing_short_volume_data(unique_user_current_all_tickers_lists)
    return JsonResponse(response_data, safe=False, status=status)


def update_user_current_all_tickers_stock_data_view(request): 
    user = request.user
    unique_user_current_all_tickers_lists = get_user_current_all_tickers(user)
    response_data,status = update_tickers_stock_data(unique_user_current_all_tickers_lists)
    return JsonResponse(response_data, safe=False, status=status)
# ---------------- End Sidebar Data  Update --------------------------

# ---------------- Start Current All Tickers Update  Update --------------------------
@csrf_exempt
def update_custom_tickers_news_view(request):

    if request.method == 'POST':
        # Determine which form was submitted
        form_type = request.POST.get('form_type')

        if form_type == 'tickers_form':
            # Process the specific tickers form
            specific_tickers_input = request.POST.get('tickers', '')
            specific_tickers = [ticker.strip().upper() for ticker in specific_tickers_input.split(',') if ticker.strip()]

            try:
                # Define the date range (last 90 days)
                start_date = datetime.today()
                end_date = start_date - timedelta(days=90)
                date_range = pd.date_range(start=end_date, end=start_date)

                # To store news for each symbol
                all_news_data = {}

                for ticker in specific_tickers:
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
                    "message": "News data fetched successfully.",
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

            return JsonResponse(response_data, safe=False, status=status)
        else:
            return JsonResponse({"message": "Unknown form submission."}, status=400)

    else:
        # Handle GET request: calculate total_tickers for display
        title_msg = 'Fetch and Save News Data'
        all_watch_lists = WatchList.objects.filter(user=request.user).order_by('order') if request.user.is_authenticated else []
        return render(request, 'stock_data_custom_form.html', {
            'all_watch_lists': all_watch_lists,
            'title_msg': title_msg,
        })

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


def update_custom_tickers_tickers_day_stock_info_view(request):

    if request.method == 'POST':
        # Determine which form was submitted
        form_type = request.POST.get('form_type')

        if form_type == 'tickers_form':
            # Process the specific tickers form
            specific_tickers_input = request.POST.get('tickers', '')
            specific_tickers = [ticker.strip().upper() for ticker in specific_tickers_input.split(',') if ticker.strip()]


            updated_symbols = []
            created_symbols = []
            stocks_to_create = []
            stocks_to_update = []

            try:
                for symbol in specific_tickers:
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
        else:
            return JsonResponse({"message": "Unknown form submission."}, status=400)

    else:
        # Handle GET request: calculate total_tickers for display
        title_msg = 'Fetch and Save Daily Stock Info Data'
        all_watch_lists = WatchList.objects.filter(user=request.user).order_by('order') if request.user.is_authenticated else []
        return render(request, 'stock_data_custom_form.html', {
            'all_watch_lists': all_watch_lists,
            'title_msg': title_msg,
        })

def update_custom_tickers_tickers_stock_info_view(request):

    if request.method == 'POST':
        # Determine which form was submitted
        form_type = request.POST.get('form_type')

        if form_type == 'tickers_form':
            # Process the specific tickers form
            specific_tickers_input = request.POST.get('tickers', '')
            specific_tickers = [ticker.strip().upper() for ticker in specific_tickers_input.split(',') if ticker.strip()]

           
            updated_symbols = []
            created_symbols = []
            stocks_to_create = []
            stocks_to_update = []



            try:
                # Loop through symbols and fetch/update stock data
                for symbol in specific_tickers:
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
        else:
            return JsonResponse({"message": "Unknown form submission."}, status=400)

    else:
        # Handle GET request: calculate total_tickers for display
        title_msg = 'Fetch and Save Stock Info Data'
        all_watch_lists = WatchList.objects.filter(user=request.user).order_by('order') if request.user.is_authenticated else []
        return render(request, 'stock_data_custom_form.html', {
            'all_watch_lists': all_watch_lists,
            'title_msg': title_msg,
        })


from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def update_custom_tickers_tickers_stock_data_view(request): 

    if request.method == 'POST':
        # Determine which form was submitted
        form_type = request.POST.get('form_type')

        if form_type == 'tickers_form':
            # Process the specific tickers form
            specific_tickers_input = request.POST.get('tickers', '')
            specific_tickers = [ticker.strip().upper() for ticker in specific_tickers_input.split(',') if ticker.strip()]

            try:
                # Call the function to fetch and save stock data
                record_msg = fetch_and_save_stock_data(specific_tickers)
                update_and_merge_missing_short_volume_data(specific_tickers)

                # Retrieve the symbols that were updated or created
                updated_symbols = StockSymbolData.objects.filter(symbol__in=specific_tickers)
                response_data = {
                    "message": "Symbol Stock data fetched and saved and Short Volume merged successfully.",
                    "updated_symbols": [symbol.symbol for symbol in updated_symbols],
                    "record_msg": record_msg
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
        else:
            return JsonResponse({"message": "Unknown form submission."}, status=400)

    else:
        # Handle GET request: calculate total_tickers for display
        # Handle GET request: calculate total_tickers for display
        title_msg = 'Fetch and Save Stock Data'
        all_watch_lists = WatchList.objects.filter(user=request.user).order_by('order') if request.user.is_authenticated else []
        return render(request, 'stock_data_custom_form.html', {
            'all_watch_lists': all_watch_lists,
            'title_msg': title_msg,
        })

# ---------------- End Current All Tickers Update  Update --------------------------

def get_missing_tickers_in_stock_data(all_stocks_symbols):
    # Get tickers
    # 1. Get all symbols from StockSymbolData
    #all_stocks_symbols = StockSymbolData.objects.values_list('symbol', flat=True)
    set_all_stocks_symbols = set(all_stocks_symbols)

    y_unique_most_active_trending_gainers_losers_lists=list(y_unique_most_active_trending_gainers_losers)

    top_short_volume_symbols = get_top_sv_symbol_lists()
    current_regsho_symbols = get_current_regsho_symbols() 
    reg_sho_remove_symbols = get_reg_sho_remove_list() 

    unique_reg_sho = set(
        current_regsho_symbols + 
        reg_sho_remove_symbols
    
    )
    unique_reg_sho_list=list(unique_reg_sho)

    all_watchlists_tickers = get_all_watchlists_tickers()
    all_splits_tickers = get_all_splits_tickers()
    all_bought_tickers = get_all_bought_tickers()
    # 4. Convert to sets for easier comparison

 
    set_y_unique_most_active_trending_gainers_losers_lists = set(y_unique_most_active_trending_gainers_losers_lists)
    set_top_short_volume_symbols = set(top_short_volume_symbols)
    set_unique_reg_sho_list = set(unique_reg_sho_list)
    set_all_watchlists_tickers = set(all_watchlists_tickers)
    set_all_splits_tickers = set(all_splits_tickers)
    set_all_bought_tickers = set(all_bought_tickers)

    # 5. Check which tickers are missing from StockSymbolData
    y_unique_most_active_trending_gainers_losers_missing_tickers_in_stock_data = set_y_unique_most_active_trending_gainers_losers_lists - set_all_stocks_symbols
    sv_missing_tickers_in_stock_data = set_top_short_volume_symbols - set_all_stocks_symbols
    reg_sho_missing_tickers_in_stock_data = set_unique_reg_sho_list - set_all_stocks_symbols
    all_watchlist_missing_tickers_in_stock_data = set_all_watchlists_tickers - set_all_stocks_symbols
    all_stocks_splits_missing_tickers_in_stock_data = set_all_splits_tickers - set_all_stocks_symbols
    all_bought_missing_tickers_in_stock_data = set_all_bought_tickers - set_all_stocks_symbols

    # Convert the sets of missing tickers to lists for JSON serialization
   
    y_missing_tickers_in_stock_data = list(y_unique_most_active_trending_gainers_losers_missing_tickers_in_stock_data)
    sv_missing_tickers_list = list(sv_missing_tickers_in_stock_data)
    reg_sho_missing_tickers_list = list(reg_sho_missing_tickers_in_stock_data)
    all_watchlists_missing_tickers_list = list(all_watchlist_missing_tickers_in_stock_data)
    all_splits_missing_tickers_list = list(all_stocks_splits_missing_tickers_in_stock_data)
    all_bought_missing_tickers_list = list(all_bought_missing_tickers_in_stock_data)

    # Return the lists as a JSON response with safe=False
    return(
        y_missing_tickers_in_stock_data, 
        sv_missing_tickers_list,
        reg_sho_missing_tickers_list,
        all_watchlists_missing_tickers_list,
        all_splits_missing_tickers_list,
        all_bought_missing_tickers_list
    )

@login_required
def missing_ticker_info_in_stock_data_view(request):
    all_stocks_symbols = StockSymbolData.objects.values_list('symbol', flat=True)
    all_stocks_symbol_info = StockSymbolInfo.objects.values_list('symbol', flat=True)
    all_stocks_symbol_daily_info = DayStockSymbolInfo.objects.values_list('symbol', flat=True)
    
    y_missing_tickers,sv_missing_tickers,reg_sho_missing_tickers,all_watchlists_missing_tickers,all_splits_missing_tickers,all_bought_missing_tickers = get_missing_tickers_in_stock_data(all_stocks_symbols)
    y_missing_info,sv_missing_info,reg_sho_missing_info,all_watchlists_missing_info,all_splits_missing_info,all_bought_missing_info = get_missing_tickers_in_stock_data(all_stocks_symbol_info)
    y_missing_daily_info,sv_missing_daily_info,reg_sho_missing_daily_info,all_watchlists_missing_daily_info,all_splits_missing_daily_info,all_bought_missing_daily_info = get_missing_tickers_in_stock_data(all_stocks_symbol_daily_info)

    unique_all_missing_in_stock_data = set(
            y_missing_tickers + 
            sv_missing_tickers +
            reg_sho_missing_tickers +
            all_watchlists_missing_tickers +
            all_splits_missing_tickers +
            all_bought_missing_tickers     
        )
    unique_all_missing_in_stock_data_list=list(unique_all_missing_in_stock_data)
    #print(f"unique_all_missing_in_stock_data_list:{unique_all_missing_in_stock_data_list}")

    unique_all_missing_in_stock_info = set(
            y_missing_info + 
            sv_missing_info +
            reg_sho_missing_info +
            all_watchlists_missing_info +
            all_splits_missing_info +
            all_bought_missing_info     
        )
    
    unique_all_missing_in_stock_info_list=list(unique_all_missing_in_stock_info)
    #print(f"unique_all_missing_in_stock_info_list:{unique_all_missing_in_stock_info_list}")
    unique_all_missing_in_stock_daily_info = set(
            y_missing_daily_info + 
            sv_missing_daily_info +
            reg_sho_missing_daily_info +
            all_watchlists_missing_daily_info +
            all_splits_missing_daily_info +
            all_bought_missing_daily_info     
        )
    
    unique_all_missing_in_stock_daily_info_list=list(unique_all_missing_in_stock_daily_info)
    #print(f"unique_all_missing_in_stock_daily_info_list:{unique_all_missing_in_stock_daily_info_list}")

    if request.user.is_authenticated:
        all_watch_lists = WatchList.objects.filter(user=request.user).order_by('order')
    else:
        all_watch_lists = []
    return render(request, 'missing_tickers_info.html', {
        'all_watch_lists': all_watch_lists,
        
        'y_missing_tickers': y_missing_tickers,
        'sv_missing_tickers': sv_missing_tickers,
        'reg_sho_missing_tickers': reg_sho_missing_tickers,
        'all_watchlists_missing_tickers': all_watchlists_missing_tickers,
        'all_splits_missing_tickers': all_splits_missing_tickers,
        'all_bought_missing_tickers': all_bought_missing_tickers,
        'unique_all_missing_in_stock_data_list': unique_all_missing_in_stock_data_list,

        'y_missing_info': y_missing_info,
        'sv_missing_info': sv_missing_info,
        'reg_sho_missing_info': reg_sho_missing_info,
        'all_watchlists_missing_info': all_watchlists_missing_info,
        'all_splits_missing_info': all_splits_missing_info,
        'all_bought_missing_info': all_bought_missing_info,
        'unique_all_missing_in_stock_info_list': unique_all_missing_in_stock_info_list,

        'y_missing_daily_info': y_missing_daily_info,
        'sv_missing_daily_info': sv_missing_daily_info,
        'reg_sho_missing_daily_info': reg_sho_missing_daily_info,
        'all_watchlists_missing_daily_info': all_watchlists_missing_daily_info,
        'all_splits_missing_daily_info': all_splits_missing_daily_info,
        'all_bought_missing_daily_info': all_bought_missing_daily_info,
        'unique_all_missing_in_stock_daily_info_list': unique_all_missing_in_stock_daily_info_list,
        
        })

from .models import EarningsData
from .stock_earning_update import update_multiple_tickers_earnings

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
import pandas as pd
import requests
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .models import SP500Ticker


@require_GET
def update_snp_500_tickers_view(request):
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"

        # Fetch with headers (avoid 403)
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Parse table
        df = pd.read_html(response.text)[0]
        tickers = df["Symbol"].tolist()

        # Normalize symbols (important!)
        tickers = [t.upper().strip().replace(".", "-") for t in tickers]

        # Current DB symbols
        existing_symbols = set(
            SP500Ticker.objects.values_list('symbol', flat=True)
        )

        new_symbols = set(tickers)

        # Add new tickers
        to_create = [
            SP500Ticker(symbol=s)
            for s in new_symbols - existing_symbols
        ]
        SP500Ticker.objects.bulk_create(to_create, ignore_conflicts=True)

        # Remove old tickers (no longer in S&P 500)
        to_delete = existing_symbols - new_symbols
        SP500Ticker.objects.filter(symbol__in=to_delete).delete()

        return JsonResponse({
            "status": "success",
            "added": len(to_create),
            "removed": len(to_delete),
            "total_now": SP500Ticker.objects.count()
        })

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)

