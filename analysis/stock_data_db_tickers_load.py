from .models import ThreeMonthsShortVolume, ThreeMonthsRegSHO,WatchList, WatchListSymbol, TickerSplit,BuyNSell
from datetime import datetime, timedelta
from django.db.models import Max, Avg
import pandas as pd
from django.http import JsonResponse

def get_top_sv_symbol_lists():
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


def get_reg_sho_remove_list():
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

 
    return removed_reg_sho_threshold_list

def is_valid_symbol(s):
    """ Ensure the symbol contains at least one alphabetic character """
    return any(c.isalpha() for c in s)

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


def get_user_watchlists_tickers(user):
        
    user_watchlists = WatchList.objects.filter(user=user)

    # Get all unique symbols from the user's watchlists
    watchlist_symbols = list(set(
        WatchListSymbol.objects.filter(watch_list__in=user_watchlists).values_list('symbol', flat=True)
    ))
    # Convert watchlist_symbols to a set before combining
    unique_watchlist_symbols = set(watchlist_symbols)
    unique_watchlist_symbols_lists=list(unique_watchlist_symbols)
    return unique_watchlist_symbols_lists

def get_all_watchlists_tickers():
        
    # Get all unique symbols from the user's watchlists
    watchlist_symbols = list(set(
        WatchListSymbol.objects.all().values_list('symbol', flat=True)
    ))
    # Convert watchlist_symbols to a set before combining
    unique_watchlist_symbols = set(watchlist_symbols)
    unique_watchlist_symbols_lists=list(unique_watchlist_symbols)
    return unique_watchlist_symbols_lists

def get_all_splits_tickers():
    # Fetch TickerSplit objects related to the healthcare sector
    all_splits = TickerSplit.objects.all()
    all_splits_lists = [split.symbol for split in all_splits]
    unique_all_splits = set(all_splits_lists)
    unique_all_splits_lists=list(unique_all_splits)
    return unique_all_splits_lists

def get_user_all_bought_tickers(user):
 
    if user.is_authenticated:
        all_bought_tickers = BuyNSell.objects.filter(
            user=user, transaction_type="B"
        ).values_list('symbol', flat=True)
        # Remove duplicates while maintaining order
        all_bought_tickers_list = list(dict.fromkeys(all_bought_tickers))
    else:
        all_bought_tickers_list = []  # No symbols if the user is not authenticated

    return all_bought_tickers_list

def get_all_bought_tickers():

    all_bought_tickers = BuyNSell.objects.all()
    all_bought_lists = [bought.symbol for bought in all_bought_tickers]
    unique_all_bought = set(all_bought_lists)
    unique_all_bought_lists=list(unique_all_bought)
    return unique_all_bought_lists

def view_test_tickers_load(request):
    user=request.user
    reg_sho_remove_symbols = get_user_all_bought_tickers(user) 
    return JsonResponse(reg_sho_remove_symbols, safe=False)