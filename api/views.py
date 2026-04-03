from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework import generics
from .serializers import UserSerializer , NoteSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Note


class NoteListCreate(generics.ListCreateAPIView):
    serializer_class = NoteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Note.objects.filter(author=user)

    def perform_create(self, serializer):
        if serializer.is_valid():
            serializer.save(author=self.request.user)
        else:
            print(serializer.errors)


class NoteDelete(generics.DestroyAPIView):
    serializer_class = NoteSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Note.objects.filter(author=user)


class CreateUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers

class UserProfileSerializer(serializers.Serializer):
    username = serializers.CharField()
    isSuperuser = serializers.BooleanField(source='is_superuser')
    isStaff = serializers.BooleanField(source='is_staff')
    isActive = serializers.BooleanField(source='is_active')

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from analysis.models import StockSymbolInfo
from .serializers import StockInfoSerializer

class StockInfoDataView(APIView):
    permission_classes = [IsAuthenticated]  # Or remove this if authentication isn't required

    def get(self, request):
        stocks = StockSymbolInfo.objects.all()
        serializer = StockInfoSerializer(stocks, many=True)
        return Response({"stocks": serializer.data})

class StockInfoWatchListDataView(APIView):
    permission_classes = [IsAuthenticated]  # Or remove this if authentication isn't required

    def get(self, request):
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

        #stocks = StockSymbolInfo.objects.all()
        serializer = StockInfoSerializer(stocks, many=True)
        return Response({"stocks": serializer.data})

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from analysis.models import WatchList, WatchListSymbol
from .serializers import WatchListSerializer, WatchListSymbolSerializer
from rest_framework.permissions import IsAuthenticated

class WatchListViewSet(viewsets.ModelViewSet):
    serializer_class = WatchListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return WatchList.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], url_path='add-symbol')
    def add_symbol(self, request, pk=None):
        watch_list = self.get_object()
        serializer = WatchListSymbolSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(watch_list=watch_list)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'], url_path='delete-symbol')
    def delete_symbol(self, request, pk=None):
        symbol_id = request.data.get('symbol_id')
        symbol = WatchListSymbol.objects.filter(id=symbol_id, watch_list__user=request.user).first()
        if symbol:
            symbol.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'error': 'Symbol not found'}, status=status.HTTP_404_NOT_FOUND)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from analysis.models import BuyNSell
from .serializers import BuySellSerializer
import yfinance as yf

class BuySellListCreateView(APIView):
    """
    Handles fetching all Buy and Sell transactions for the logged-in user
    and creating new transactions.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Filter transactions by the logged-in user
        buy_records = BuyNSell.objects.filter(user=request.user, transaction_type__in=['B', 'O']).order_by('-date')
        sell_records = BuyNSell.objects.filter(user=request.user, transaction_type='S').order_by('-date')

        # Serialize the data
        buy_serializer = BuySellSerializer(buy_records, many=True)
        sell_serializer = BuySellSerializer(sell_records, many=True)

        return Response({
            'buy_records': buy_serializer.data,
            'sell_records': sell_serializer.data
        })

    def post(self, request):
        # Validate and save new transaction
        serializer = BuySellSerializer(data=request.data)
        if serializer.is_valid():
            instance = serializer.save(user=request.user)  # Associate with the logged-in user
            
            # Generate order ID for buy transactions
            if instance.transaction_type == 'B':
                existing_orders = BuyNSell.objects.filter(user=request.user, symbol=instance.symbol, transaction_type='B').count()
                instance.order_id = f"{instance.symbol}-{existing_orders + 1:02d}"
                instance.save()

            # Fetch stock info (optional)
            try:
                stock_info = yf.Ticker(instance.symbol)
                instance.name = stock_info.info.get('shortName', 'Unknown Name')
                instance.sector = stock_info.info.get('sector', 'Unknown Name')
                instance.save()
            except Exception:
                instance.name = 'Unknown Name'
                instance.sector = 'Unknown Sector'
                instance.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BuySellDeleteView(APIView):
    """
    Handles deletion of a specific transaction.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        transaction = BuyNSell.objects.filter(pk=pk, user=request.user).first()
        if transaction:
            transaction.delete()
            return Response({"message": "Transaction deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        return Response({"error": "Transaction not found"}, status=status.HTTP_404_NOT_FOUND)

class GetOrderIdsView(APIView):
    """
    Returns order IDs for a specific symbol and user to populate dropdowns for Sell transactions.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        symbol = request.query_params.get('symbol', '')
        if not symbol:
            return Response({"error": "Symbol parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

        orders = BuyNSell.objects.filter(user=request.user, symbol=symbol, transaction_type='B').values_list('order_id', flat=True)
        return Response({"order_ids": list(orders)})



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import status
from analysis.models import TickerSplit
from .serializers import TickerSplitSerializer
from datetime import date
import yfinance as yf


class TickerSplitListView(APIView):
    """
    Handles fetching all splits and creating new splits.
    """

    def get(self, request):
        last_splits = TickerSplit.objects.filter(date__lt=date.today()).order_by('-date')
        next_splits = TickerSplit.objects.filter(date__gte=date.today()).order_by('date')
        last_serializer = TickerSplitSerializer(last_splits, many=True)
        next_serializer = TickerSplitSerializer(next_splits, many=True)
        return Response({
            "last_splits": last_serializer.data,
            "next_splits": next_serializer.data
        })

    def post(self, request):
        serializer = TickerSplitSerializer(data=request.data)
        if serializer.is_valid():
            # Save the serializer to create an instance of TickerSplit
            instance = serializer.save()

            # Fetch stock info from Yahoo Finance
            try:
                stock_info = yf.Ticker(instance.symbol)
                instance.name = stock_info.info.get('shortName', 'Unknown Name')
                instance.sector = stock_info.info.get('sector', 'Unknown Sector')
                instance.save()
            except Exception as e:
                # Handle errors if Yahoo Finance API fails
                instance.name = 'Unknown Name'
                instance.sector = 'Unknown Sector'
                instance.save()

            # Return the serialized data along with the updated name and sector
            updated_serializer = TickerSplitSerializer(instance)
            return Response(updated_serializer.data, status=status.HTTP_201_CREATED)

        # If the serializer is invalid, return the errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class TickerSplitDeleteView(APIView):
    """
    Handles deletion of a specific ticker split.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def delete(self, request, pk):
        split = TickerSplit.objects.filter(pk=pk).first()
        if split:
            split.delete()
            return Response({"message": "Ticker split deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        return Response({"error": "Ticker split not found"}, status=status.HTTP_404_NOT_FOUND)


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from analysis.models import WatchList
from analysis.ticker_lists import reg_sho_symbols



def normalize_data(data, keys):
    """
    Helper function to normalize data to a list of dictionaries.
    :param data: List of tuples containing data to normalize.
    :param keys: List of keys to map each tuple value to.
    :return: List of dictionaries.
    """
    normalized = []
    for item in data:
        if len(item) == len(keys):  # Ensure item matches the expected structure
            obj = {key: value for key, value in zip(keys, item)}
            normalized.append(obj)
        else:
            # Log or handle items with unexpected structure
            print(f"Skipping invalid item: {item}")
    return normalized


class RegShoSymbolsAPIView(APIView):
    """
    API view to provide Reg SHO Symbols data for frontend consumption.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Fetch user's watch lists
        if request.user.is_authenticated:
            all_watch_lists = WatchList.objects.filter(user=request.user).order_by('order')
        else:
            all_watch_lists = []

        # Fetch symbol data
        current_list_data, newly_added_data, deleted_data, latest_date = reg_sho_symbols()

        # Normalize data
        newly_added_data_normalized = normalize_data(newly_added_data, ["id", "symbol", "date_added"])
        deleted_data_normalized = normalize_data(deleted_data, ["id", "symbol", "date_deleted"])

        # Prepare response
        response_data = {
            "all_watch_lists": [{"id": wl.id, "name": wl.name} for wl in all_watch_lists],
            "current_list_data": current_list_data,  # Assuming this is already in dictionary format
            "newly_added_data": newly_added_data_normalized,
            "deleted_data": deleted_data_normalized,
            "latest_date": latest_date.strftime("%Y-%m-%d"),
        }

        return Response(response_data)


class WatchListViewSidebarSet(viewsets.ModelViewSet):
    serializer_class = WatchListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return WatchList.objects.filter(user=self.request.user)



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from analysis.models import WatchList, WatchListSymbol, NewsData
from datetime import timedelta, date
import yfinance as yf


class WatchlistScreenerAPIView(APIView):
    """
    API view to fetch and return screener data for the user's watchlist.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
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

                # Check for related news
                today = date.today()
                news = NewsData.objects.filter(news_symbol__symbol=symbol, Date=today).order_by('-providerPublishTime').first()
                news_title = news.NewsTitle if news else "No News Today"
                news_link = news.NewsLink if news else None
                news_publish_time = news.providerPublishTime if news else None

                # Extract the time and date
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
                    "current_price": current_price,
                    "news_title": news_title,
                    "news_link": news_link,
                    "news_publish_date": news_publish_date,
                    "news_publish_time_only": news_publish_time_only,
                })

            except Exception as e:
                # Handle failures gracefully
                screener_data.append({
                    "id": idx,
                    "symbol": symbol,
                    "long_name": "Error fetching data",
                    "price_change_pct": 0,
                    "price_change": 0,
                    "volume_per_min": 0,
                    "total_volume": 0,
                    "current_price": 0,
                    "news_title": "N/A",
                    "news_link": None,
                    "news_publish_date": None,
                    "news_publish_time_only": None,
                })
                print(f"Error processing symbol {symbol}: {e}")

        # Sorting
        sort_field = request.query_params.get('sort', 'price_change_pct')  # Default sorting field
        sort_direction = request.query_params.get('direction', 'desc')  # Default sorting direction
        reverse = sort_direction == 'desc'

        try:
            screener_data = sorted(
                screener_data,
                key=lambda x: x.get(sort_field, 0) if isinstance(x.get(sort_field, (int, float)), (int, float)) else 0,
                reverse=reverse
            )
        except KeyError:
            pass  # Handle invalid sort_field gracefully by skipping sorting

        return Response({"screener_data": screener_data})

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from analysis.models import WatchList, WatchListSymbol, NewsData
from datetime import timedelta, date
import yfinance as yf


class WatchlistNewsAPIView(APIView):
    """
    API view to fetch and return news for the user's watchlist symbols.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get the logged-in user's watchlists
        user_watchlists = WatchList.objects.filter(user=request.user)

        # Get all symbols from the user's watchlists
        watchlist_symbols = WatchListSymbol.objects.filter(watch_list__in=user_watchlists).values_list('symbol', flat=True)

        # Get today's and yesterday's dates
        today = date.today()
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

        # Fetch stock data and price change information
        symbol_data = {}
        for symbol in unique_symbols:
            stock_info = yf.Ticker(symbol)
            long_name = stock_info.info.get("longName", "Name not found")
            try:
                price_data = stock_info.history(period="1d")
                if not price_data.empty:
                    current_price = price_data['Close'][-1]
                    previous_close = stock_info.info.get("regularMarketPreviousClose", current_price)
                    price_change_pct = ((current_price - previous_close) / previous_close) * 100
                else:
                    price_change_pct = None
            except Exception:
                price_change_pct = None

            symbol_data[symbol] = {
                "long_name": long_name,
                "price_change_pct": round(price_change_pct, 2) if price_change_pct is not None else "N/A"
            }

        # Format news data
        def format_news(news_items):
            formatted_news = []
            for news in news_items:
                news_data = {
                    "symbol": news.news_symbol.symbol,
                    "long_name": symbol_data.get(news.news_symbol.symbol, {}).get("long_name", "Name not found"),
                    "price_change_pct": symbol_data.get(news.news_symbol.symbol, {}).get("price_change_pct", "N/A"),
                    "title": news.NewsTitle,
                    "link": news.NewsLink,
                    "publish_date": news.providerPublishTime.date(),
                    "publish_time": news.providerPublishTime.time(),
                }
                formatted_news.append(news_data)
            return formatted_news

        return Response({
            "news_today": format_news(news_today),
            "news_yesterday": format_news(news_yesterday),
        })

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import APIException

# Import your symbol lists
from analysis.views import (
    top_sv_symbol_lists,
    get_current_regsho_symbols,
    reg_sho_remove_list
)
from analysis.yscreener import (
    y_most_active,
    y_tranding,
    y_top_gainers,
    y_top_losers
)
from analysis.stock_day_info_second import stock_day_info

class StockDailyInfoDataView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Handles GET requests to dynamically fetch data based on the `urlName` parameter.
        """
        try:

            url_name = request.GET.get('path')
            print(f"manual url path:{url_name}")
            # Fetch user watchlists
            user_watchlists = WatchList.objects.filter(user=request.user)


            # Determine the symbols based on the dynamic URL part
            if url_name == "top-avg-short-volume":
                symbols = top_sv_symbol_lists()
            elif url_name == "current-reg-sho-lists":
                symbols = get_current_regsho_symbols()
            elif url_name == "reg-sho-removed-lists":
                symbols = reg_sho_remove_list()

            elif url_name == "last-splits":
                last_splits = TickerSplit.objects.filter(date__lt=date.today()).order_by('-date')
                symbols = [split.symbol for split in last_splits]
            elif url_name == "last-splits-healthcare":
                    # Fetch TickerSplit objects related to the healthcare sector
                last_splits_healthcare = TickerSplit.objects.filter(date__lt=date.today(), sector="Healthcare").order_by('-date')
                symbols = [split.symbol for split in last_splits_healthcare]

            elif url_name == "upcoming-splits":
                upcoming_splits = TickerSplit.objects.filter(date__gte=date.today())
                symbols = [split.symbol for split in upcoming_splits] 

            elif url_name == "bought-tickers":
                all_bought_tickers = BuyNSell.objects.filter(
                    user=request.user, transaction_type="B"
                ).order_by('-date').values_list('symbol', flat=True)
                # Remove duplicates while maintaining order
                symbols = list(dict.fromkeys(all_bought_tickers))
            elif url_name == "healthcare-bought-tickers":
                healthcare_bought_tickers = BuyNSell.objects.filter(
                    user=request.user, sector="Healthcare", transaction_type="B"
                ).order_by('-date').values_list('symbol', flat=True)
                # Remove duplicates while maintaining order
                symbols = list(dict.fromkeys(healthcare_bought_tickers))

            elif url_name == "most-active":
                symbols = y_most_active()
            elif url_name == "trending":
                symbols = y_tranding()
            elif url_name == "top-gainers":
                symbols = y_top_gainers()
            elif url_name == "top-losers":
                symbols = y_top_losers()
            else:
                # Get all symbols from the user's watchlists
                symbols = WatchListSymbol.objects.filter(watch_list__in=user_watchlists).values_list('symbol', flat=True)
                print(f"watchlist symbols: {symbols}")
                

            # Fetch and format stock data
            formatted_day_stocks = stock_day_info(symbols)
            return Response({"stocks": formatted_day_stocks})

        except Exception as e:
            print(f"Error in StockDailyInfoDataView GET: {str(e)}")
            raise APIException("An error occurred while processing the request.")
        
from django.shortcuts import get_object_or_404

class StockDailyInfoWatchListDataView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Handles GET requests to dynamically fetch data based on the `urlName` parameter.
        """
        try:

            watch_list_name = request.GET.get('path')
            
            # Fetch the watch list specific to the user
            watch_list = get_object_or_404(WatchList, name=watch_list_name, user=request.user)

            # Get symbols associated with the watch list
            symbols_to_search = list(WatchListSymbol.objects.filter(watch_list=watch_list).values_list('symbol', flat=True))
            symbols = [symbol.upper() for symbol in symbols_to_search]

            # Fetch and format stock data
            formatted_day_stocks = stock_day_info(symbols)
            return Response({"stocks": formatted_day_stocks})

        except Exception as e:
            print(f"Error in StockDailyInfoDataView GET: {str(e)}")
            raise APIException("An error occurred while processing the request.")
        
############################################################################################################


############################################################################################################

## Data from database

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.response import Response
from analysis.models import StockSymbolInfo, StockPriceData, NewsData, StockSymbolData
from .stock_chart_utils import preparedRegSho_df, check_symbol_dates
import pandas as pd
from datetime import datetime

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_chart_data_from_database(request):
    # symbols = request.data.get('symbols', [])
    #symbols = ['FFIE', 'MYNZ', 'NVDA', 'AAPL'] 
    
    url_name = request.GET.get('path')
    print(f"manual url path:{url_name}")
    # Fetch user watchlists
    user_watchlists = WatchList.objects.filter(user=2)


    # Determine the symbols based on the dynamic URL part
    if url_name == "top-average-short-volume-charts":
        symbols = top_sv_symbol_lists()
    elif url_name == "current-reg-sho-charts":
        symbols = get_current_regsho_symbols()
    elif url_name == "reg-sho-removed-charts":
        symbols = reg_sho_remove_list()

    elif url_name == "last-splits-charts":
        last_splits = TickerSplit.objects.filter(date__lt=date.today()).order_by('-date')
        symbols = [split.symbol for split in last_splits]
    elif url_name == "last-splits-healthcare-charts":
            # Fetch TickerSplit objects related to the healthcare sector
        last_splits_healthcare = TickerSplit.objects.filter(date__lt=date.today(), sector="Healthcare").order_by('-date')
        symbols = [split.symbol for split in last_splits_healthcare]

    elif url_name == "upcoming-splits":
        upcoming_splits = TickerSplit.objects.filter(date__gte=date.today())
        symbols = [split.symbol for split in upcoming_splits] 

    elif url_name == "bought-charts":
        all_bought_tickers = BuyNSell.objects.filter(
            user=request.user, transaction_type="B"
        ).order_by('-date').values_list('symbol', flat=True)
        # Remove duplicates while maintaining order
        symbols = list(dict.fromkeys(all_bought_tickers))
    elif url_name == "bought-healthcare-charts":
        healthcare_bought_tickers = BuyNSell.objects.filter(
            user=request.user, sector="Healthcare", transaction_type="B"
        ).order_by('-date').values_list('symbol', flat=True)
        # Remove duplicates while maintaining order
        symbols = list(dict.fromkeys(healthcare_bought_tickers))

    elif url_name == "most-active-charts":
        symbols = y_most_active()
    elif url_name == "trending-charts":
        symbols = y_tranding()
    elif url_name == "top-gainers-charts":
        symbols = y_top_gainers()
    elif url_name == "top-losers-charts":
        symbols = y_top_losers()
    else:
        # Get all symbols from the user's watchlists
        symbols = WatchListSymbol.objects.filter(watch_list__in=user_watchlists).values_list('symbol', flat=True)
        print(f"watchlist symbols: {symbols}")
        

    if not symbols:
        return Response({"error": "No symbols provided"}, status=400)

    response_data = {}
    
    for symbol in symbols:
        stock = StockSymbolInfo.objects.filter(symbol=symbol).first()
        
        if not stock:
            continue

        # Company profile information
        profile = {
            "company_name": stock.company_name,
            "most_recent_split": str(stock.lastSplitFactor) if stock.lastSplitFactor else None,
            "split_date": stock.lastSplitDate.isoformat() if stock.lastSplitDate else None,
            "high_52W": str(stock.fiftyTwoWeekHigh),
            "low_52W": str(stock.fiftyTwoWeekLow),
            "ten_day_avg_volume": str(stock.averageVolume10days),
            "market_cap": str(stock.marketCap),
            "float_shares_date": stock.dateShortInterest.isoformat() if stock.dateShortInterest else None,
            "float_shares": str(stock.floatShares),
            "outstanding_shares": str(stock.sharesOutstanding),
        }

        # Historical stock price data (last 90 days)
        stock_symbol = StockSymbolData.objects.filter(symbol=symbol).first()
        historical_data = []
        if stock_symbol:
            stock_prices = StockPriceData.objects.filter(stock_symbol=stock_symbol).order_by('-timestamp')[:65]
            for price in stock_prices:
                historical_data.append({
                    "date": price.timestamp.isoformat(),
                    "open": float(price.open),
                    "high": float(price.high),
                    "low": float(price.low),
                    "close": float(price.close),
                    "volume": float(price.volume),
                    "ShortVolume": float(price.ShortVolume) if price.ShortVolume is not None else 0.0,
                })

        # News data
        news_data = NewsData.objects.filter(news_symbol__symbol=symbol).order_by('-Date')[:10]
        news = [
            {
                "time": news_item.Date.isoformat(),
                "headline": news_item.NewsTitle,
                "newsLink": news_item.NewsLink,
                "providerPublishTime": news_item.providerPublishTime,
            }
            for news_item in news_data
        ]

        # Buy/Sell/Other Transactions
        transactions = BuyNSell.objects.filter(
            symbol=symbol,
            transaction_type__in=['B', 'S', 'O']
        ).values('date', 'transaction_type', 'quantity', 'fill_price', 'order_id')

        # Group transactions by date
        grouped_transactions = {}
        for transaction in transactions:
            transaction_date = transaction['date'].isoformat()
            if transaction_date not in grouped_transactions:
                grouped_transactions[transaction_date] = []
            grouped_transactions[transaction_date].append({
                "type": transaction['transaction_type'],
                "quantity": transaction['quantity'],
                "fill_price": transaction['fill_price'],
                "order_id": transaction['order_id']
            })

        # Reg SHO Events
        combined_sho_df = preparedRegSho_df()
        reg_sho_events = check_symbol_dates(combined_sho_df, symbol)
        # Fetch Reg SHO events
        reg_sho_events = [
            {
                "type": event["type"],
                "date": event["date"].strftime("%Y-%m-%d")  # Directly format the Timestamp object
            }
            for event in reg_sho_events
        ] if reg_sho_events else []
        # Combine data for the symbol
        response_data[symbol] = {
            "profile": profile,
            "transactions": grouped_transactions,  # Add grouped transaction data
            "regShoEvents": reg_sho_events,  # Add Reg SHO event data
            "news": news,
            "historical_data": historical_data,
            
        }

    return Response(response_data, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_chart_watchlist_data_from_database(request):
    # symbols = request.data.get('symbols', [])
    #symbols = ['FFIE', 'MYNZ', 'NVDA', 'AAPL'] 
    
    
    # Fetch user watchlists
    watch_list_name = request.GET.get('path')
    print(f"manual url path:{watch_list_name}")
    # Fetch the watch list specific to the user
    watch_list = get_object_or_404(WatchList, name=watch_list_name, user=request.user)

    # Get symbols associated with the watch list
    symbols_to_search = list(WatchListSymbol.objects.filter(watch_list=watch_list).values_list('symbol', flat=True))
    #symbols = [symbol.upper() for symbol in symbols_to_search]
    # Check if symbols_to_search contains any symbols
    if symbols_to_search:
        symbols = [symbol.upper() for symbol in symbols_to_search]
    else:
        symbols = []  # Assign an empty list if no symbols are found
    if not symbols:
        return Response({"error": "No symbols provided"}, status=400)

    response_data = {}
    
    for symbol in symbols:
        stock = StockSymbolInfo.objects.filter(symbol=symbol).first()
        
        if not stock:
            continue

        # Company profile information
        profile = {
            "company_name": stock.company_name,
            "most_recent_split": str(stock.lastSplitFactor) if stock.lastSplitFactor else None,
            "split_date": stock.lastSplitDate.isoformat() if stock.lastSplitDate else None,
            "high_52W": str(stock.fiftyTwoWeekHigh),
            "low_52W": str(stock.fiftyTwoWeekLow),
            "ten_day_avg_volume": str(stock.averageVolume10days),
            "market_cap": str(stock.marketCap),
            "float_shares_date": stock.dateShortInterest.isoformat() if stock.dateShortInterest else None,
            "float_shares": str(stock.floatShares),
            "outstanding_shares": str(stock.sharesOutstanding),
        }

        # Historical stock price data (last 90 days)
        stock_symbol = StockSymbolData.objects.filter(symbol=symbol).first()
        historical_data = []
        if stock_symbol:
            stock_prices = StockPriceData.objects.filter(stock_symbol=stock_symbol).order_by('-timestamp')[:65]
            for price in stock_prices:
                historical_data.append({
                    "date": price.timestamp.isoformat(),
                    "open": float(price.open),
                    "high": float(price.high),
                    "low": float(price.low),
                    "close": float(price.close),
                    "volume": float(price.volume),
                    "ShortVolume": float(price.ShortVolume) if price.ShortVolume is not None else 0.0,
                })

        # News data
        news_data = NewsData.objects.filter(news_symbol__symbol=symbol).order_by('-Date')[:10]
        news = [
            {
                "time": news_item.Date.isoformat(),
                "headline": news_item.NewsTitle,
                "newsLink": news_item.NewsLink,
                "providerPublishTime": news_item.providerPublishTime,
            }
            for news_item in news_data
        ]

        # Buy/Sell/Other Transactions
        transactions = BuyNSell.objects.filter(
            symbol=symbol,
            transaction_type__in=['B', 'S', 'O']
        ).values('date', 'transaction_type', 'quantity', 'fill_price', 'order_id')

        # Group transactions by date
        grouped_transactions = {}
        for transaction in transactions:
            transaction_date = transaction['date'].isoformat()
            if transaction_date not in grouped_transactions:
                grouped_transactions[transaction_date] = []
            grouped_transactions[transaction_date].append({
                "type": transaction['transaction_type'],
                "quantity": transaction['quantity'],
                "fill_price": transaction['fill_price'],
                "order_id": transaction['order_id']
            })

        # Reg SHO Events
        combined_sho_df = preparedRegSho_df()
        reg_sho_events = check_symbol_dates(combined_sho_df, symbol)
        # Fetch Reg SHO events
        reg_sho_events = [
            {
                "type": event["type"],
                "date": event["date"].strftime("%Y-%m-%d")  # Directly format the Timestamp object
            }
            for event in reg_sho_events
        ] if reg_sho_events else []
        # Combine data for the symbol
        response_data[symbol] = {
            "profile": profile,
            "transactions": grouped_transactions,  # Add grouped transaction data
            "regShoEvents": reg_sho_events,  # Add Reg SHO event data
            "news": news,
            "historical_data": historical_data,
            
        }

    return Response(response_data, status=200)




