from django.core.cache import cache
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import WatchList
from .models import BuyNSell


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


def handle_cached_charts_view(request, cache_key, cache_time, title_text, page_path, symbols_to_search_func, charts_with_symbols_func, heading_text_func, number_of_tickers=50):
    """
    Generic function to handle caching, data generation, and rendering for views.

    Args:
        request: The HTTP request object.
        cache_key: Unique key for caching the data.
        cache_time: Time-to-live for cached data.
        title_text: Title text for the page.
        page_path: Path for the page.
        symbols_to_search_func: Function to fetch the symbols to search.
        charts_with_symbols_func: Function to generate charts for the symbols.
        heading_text_func: Function to generate the heading text dynamically.
        number_of_tickers: (Optional) The maximum number of tickers to include in the charts. Default is 50.
    """
    # Fetch watch lists for the user
    all_watch_lists = WatchList.objects.filter(user=request.user).order_by('order') if request.user.is_authenticated else []

    # Handle cache clearing
    if request.GET.get('clear_cache') == 'true':
        cache.delete(cache_key)
        return render(request, 'cache-clear-charts.html', {
            'charts_with_symbols': [],
            'all_watch_lists': all_watch_lists,
            'title_text': f"Cache: {title_text}",
            'message': f'{title_text}: Cache cleared successfully!'
        })

    # Attempt to retrieve data from cache
    cached_data = cache.get(cache_key)
    if cached_data:
        charts_with_symbols = cached_data.get('charts_with_symbols')
        legth_of_tickers = cached_data.get('legth_of_tickers', 0)
        heading_text = heading_text_func(legth_of_tickers)
        return render(request, 'top-all-charts.html', {
            'charts_with_symbols': charts_with_symbols,
            'all_watch_lists': all_watch_lists,
            'title_text': title_text,
            'heading_text': heading_text,
            'page_path': page_path,
        })

    # Generate fresh data if not in cache
    filtered_symbols = symbols_to_search_func()

    # Select the first `number_of_tickers` symbols
    symbols_to_search = filtered_symbols[:number_of_tickers] if len(filtered_symbols) > number_of_tickers else filtered_symbols
    legth_of_tickers = len(symbols_to_search)
    charts_with_symbols = charts_with_symbols_func(symbols_to_search, request.user)

    # Store the generated data in cache
    cache.set(cache_key, {
        'charts_with_symbols': charts_with_symbols,
        'legth_of_tickers': legth_of_tickers
    }, cache_time)

    non_healthcare_bought_tickers_list          = get_non_healthcare_bought_tickers(request.user)
    healthcare_bought_tickers_list              = get_healthcare_bought_tickers(request.user)
    # Render the response with the generated data
    heading_text = heading_text_func(legth_of_tickers)
    return render(request, 'top-all-charts.html', {
        'charts_with_symbols': charts_with_symbols,
        'all_watch_lists': all_watch_lists,
        'title_text': title_text,
        'heading_text': heading_text,
        'page_path': page_path,
        'length_of_non_healthcare_bought_tickers': len(non_healthcare_bought_tickers_list),
        'length_of_healthcare_bought_tickers_list': len(healthcare_bought_tickers_list)
    })
