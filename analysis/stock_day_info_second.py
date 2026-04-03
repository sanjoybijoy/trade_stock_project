from .models import DayStockSymbolInfo

def stock_day_info(symbols):
    # Utility function to format numbers for display
    def format_big_number(number):
        return format(number, ",") if number is not None else None

    # Utility function to calculate percentage change
    def calculate_percentage_change_old(current, previous):
        if previous and previous != 0:
            return round(((current - previous) / previous) * 100, 2)
        return None
    
    def calculate_percentage_change(current, previous):
        if current is None or previous is None or previous == 0:
            return None  # Or return a specific value indicating the error
        return round(((current - previous) / previous) * 100, 2)


    # Filter stocks based on user's watchlist symbols from DayStockSymbolInfo
    day_stocks = DayStockSymbolInfo.objects.filter(symbol__in=symbols).values(
        'symbol','company_name', 'previousClose', 'open', 'currentPrice', 'dayLow', 'dayHigh',
        'volume', 'averageVolume3months', 'averageVolume10days', 'marketCap'
    )

    # Format the day stock data for display
    formatted_day_stocks = []
    for stock in day_stocks:
        previous_close = stock['previousClose']
        current_price = stock['currentPrice']
        day_high = stock['dayHigh']
        day_low = stock['dayLow']

        # Calculate derived fields
        price_change = round(current_price - previous_close, 3) if previous_close is not None and current_price is not None else None
        price_change_percentage = calculate_percentage_change(current_price, previous_close)
        price_change_to_high = calculate_percentage_change(day_high, previous_close)
        price_change_to_low = calculate_percentage_change(day_low, previous_close)

        formatted_day_stocks.append({
            'symbol': stock['symbol'],
            'company_name': stock['company_name'],
            'previousClose': format_big_number(previous_close),
            'open': format_big_number(stock['open']),
            'currentPrice': format_big_number(current_price),
            'dayLow': format_big_number(day_low),
            'dayHigh': format_big_number(day_high),
            'volume': format_big_number(stock['volume']),
            'averageVolume3months': format_big_number(stock['averageVolume3months']),
            'averageVolume10days': format_big_number(stock['averageVolume10days']),
            'marketCap': format_big_number(stock['marketCap']),
            'price_change': price_change,
            'price_change_percentage': price_change_percentage,
            'price_change_to_high': price_change_to_high,
            'price_change_to_low': price_change_to_low,
        })

    # Render the data into an HTML table
    return formatted_day_stocks
