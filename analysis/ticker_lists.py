from .models import ThreeMonthsShortVolume, ThreeMonthsRegSHO
from datetime import datetime, timedelta
from django.db.models import Max, Avg


from .models import TickerSplit
from typing import List, Set

def top_sv_symbol_lists_function():
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

def is_valid_symbol(s):
    """ Ensure the symbol contains at least one alphabetic character """
    return any(c.isalpha() for c in s)

def reg_sho_symbols():
    latest_date = ThreeMonthsRegSHO.objects.aggregate(latest=Max('Date'))['latest']
    consecutive_date = latest_date - timedelta(days=10)
    recent_reg_sho = ThreeMonthsRegSHO.objects.filter(Date__range=[consecutive_date, latest_date]).order_by('Date')

    symbols_by_date = {}
    symbol_to_name = {}
    previous_symbols = set()
    all_symbols = set()

    # Organize data by date
    for entry in recent_reg_sho:
        date = entry.Date.strftime("%Y%m%d")
        symbol = entry.Symbol
        security_name = entry.security_name

        if is_valid_symbol(symbol):
            symbols_by_date.setdefault(date, set()).add(symbol)
            symbol_to_name[symbol] = security_name
            all_symbols.add(symbol)  # Keep track of all symbols

    added_symbols = {}
    deleted_symbols = {}
    current_symbols = set()
    all_deleted_symbols = set()

    # Track symbol additions and deletions
    for date, symbols in sorted(symbols_by_date.items()):
        if previous_symbols:
            newly_added = symbols - previous_symbols
            removed = previous_symbols - symbols
            for symbol in newly_added:
                added_symbols[symbol] = (date, symbol_to_name[symbol])
            for symbol in removed:
                deleted_symbols[symbol] = (date, symbol_to_name[symbol])
                all_deleted_symbols.add(symbol)
        previous_symbols = symbols
        current_symbols.update(symbols)

    # Remove deleted symbols from the final current symbols
    final_current_symbols = sorted([s for s in current_symbols if s not in all_deleted_symbols and is_valid_symbol(s)])
    
    current_list_data = [{'id': idx, 'symbol': s, 'name': symbol_to_name[s]} for idx, s in enumerate(sorted(final_current_symbols))]
    newly_added_data = [(idx, s, d) for idx, (s, d, _) in enumerate(sorted([(s, d, symbol_to_name[s]) for s, d in added_symbols.items()], key=lambda x: x[1], reverse=True))]
    deleted_data = [(idx, s, d) for idx, (s, d, _) in enumerate(sorted([(s, d, symbol_to_name[s]) for s, d in deleted_symbols.items()], key=lambda x: x[1], reverse=True))]
    
    return current_list_data,newly_added_data,deleted_data, latest_date
