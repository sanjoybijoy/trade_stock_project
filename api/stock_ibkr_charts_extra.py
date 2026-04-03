
from django.shortcuts import render
from ib_insync import *
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import AllowAny,IsAuthenticated

import asyncio
import nest_asyncio

# Apply nested asyncio for compatibility
nest_asyncio.apply()

#tickers = ['MYNZ','NVDA','AAPL']

from ib_insync import IB, Stock
import xml.etree.ElementTree as ET
from rest_framework.decorators import api_view, permission_classes

@api_view(['GET'])
@permission_classes([AllowAny])
def get_historical_data(request):
    ib = IB()
    try:
        ib.connect('127.0.0.1', 7496, clientId=33)
        print("Connected to IBKR")

        # tickers = request.query_params.getlist('tickers[]', [])
        tickers = ['MTC','MYNZ', 'NVDA', 'AAPL']  # Example tickers
        result = {}

        subscribed_providers = ['DJ-RTG']  # Replace with your subscribed providers

        for ticker in tickers:
            contract = Stock(ticker, 'SMART', 'USD')

            # Validate contract details
            details = ib.reqContractDetails(contract)
            if not details:
                print(f"Invalid contract details for {ticker}")
                continue

            conId = details[0].contract.conId

            # Fetch historical data
            try:
                bars = ib.reqHistoricalData(
                    contract, endDateTime='', durationStr='80 D',
                    barSizeSetting='1 day', whatToShow='TRADES', useRTH=False
                )
                historical_data = [
                    {
                        'date': bar.date.strftime('%Y-%m-%d %H:%M:%S'),
                        'open': bar.open,
                        'high': bar.high,
                        'low': bar.low,
                        'close': bar.close,
                        'volume': bar.volume
                    }
                    for bar in bars
                ] if bars else []
            except Exception as e:
                print(f"Error fetching historical data for {ticker}: {e}")
                historical_data = "Error fetching historical data."

            # Fetch fundamental data (profile)
            try:
                fundamental_data = ib.reqFundamentalData(contract, reportType='ReportSnapshot')
                if fundamental_data:
                    profile_xml = fundamental_data
                    root = ET.fromstring(profile_xml)

                    # Extract required fields from XML
                    company_name = root.find(".//CoID[@Type='CompanyName']").text
                    most_recent_split = root.find(".//MostRecentSplit").text
                    split_date = root.find(".//MostRecentSplit").attrib['Date']
                    high_52W = root.find(".//Ratio[@FieldName='NHIG']").text
                    low_52W = root.find(".//Ratio[@FieldName='NLOW']").text
                    ten_day_avg_volume = root.find(".//Ratio[@FieldName='VOL10DAVG']").text
                    market_cap = root.find(".//Ratio[@FieldName='MKTCAP']").text
                    float_shares_date = root.find(".//SharesOut").attrib['Date']
                    float_shares = root.find(".//SharesOut").attrib['TotalFloat']
                    outstanding_shares = root.find(".//SharesOut").text
                    #financial_summary = root.find(".//Text[@Type='Financial Summary']").text

                    profile = {
                        'company_name': company_name,
                        'most_recent_split': most_recent_split,
                        'split_date': split_date,
                        'high_52W': high_52W,
                        'low_52W': low_52W,
                        'ten_day_avg_volume': ten_day_avg_volume,
                        'market_cap': market_cap,
                        'float_shares_date': float_shares_date,
                        'float_shares': float_shares,
                        'outstanding_shares': outstanding_shares,
                        #'financial_summary': financial_summary
                    }
                else:
                    profile = "No fundamental data available."
            except Exception as e:
                print(f"Error fetching fundamental data for {ticker}: {e}")
                profile = "Error fetching profile."

            # Fetch news
            try:
                news = ib.reqHistoricalNews(
                    conId=conId,
                    providerCodes=','.join(subscribed_providers),
                    startDateTime='20241201 00:00:00',
                    endDateTime='',
                    totalResults=5
                )
                news_data = []
                for item in news:
                    try:
                        news_data.append({
                            'time': item.time.strftime('%Y-%m-%d %H:%M:%S'),
                            'headline': item.headline,
                            'provider': item.providerCode
                        })
                    except Exception as e:
                        print(f"Error fetching article details for {item.articleId}: {e}")
                        news_data.append({
                            'time': item.time.strftime('%Y-%m-%d %H:%M:%S'),
                            'headline': item.headline,
                            'provider': item.providerCode
                        })
            except Exception as e:
                print(f"Error fetching news for {ticker}: {e}")
                news_data = "Error fetching news."

            # Gather results
            result[ticker] = {

                'profile': profile,
                'news': news_data,
                'historical_data': historical_data
                
            }

        return Response(result)

    except Exception as e:
        print(f"Error: {e}")
        return Response({'error': str(e)}, status=500)

    finally:
        ib.disconnect()
        print("Disconnected from IBKR")




# views.py
from django.http import StreamingHttpResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import threading
import time
import json

import json
import time
import threading
from queue import Queue, Empty
from django.http import StreamingHttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from ib_insync import Contract
from ib_insync.ib import IB
from django.http import JsonResponse


class IBKRClient(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.real_time_data = Queue()

    def realtimeBar(self, reqId, time, open_, high, low, close, volume, wap, count):
        print(f"Realtime bar received: {time}, {open_}, {high}, {low}, {close}, {volume}")
        bar = {
            "time": time,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": float(volume),
            "wap": float(wap),
            "count": count,
        }
        self.real_time_data.put(bar)

    def get_data_stream(self, reqId, contract):
        self.reqRealTimeBars(reqId, contract, 5, "TRADES", 0, [])
        try:
            while True:
                try:
                    # Wait for a new bar for up to 1 second
                    bar = self.real_time_data.get(timeout=1)
                    yield f"data: {json.dumps(bar)}\n\n"
                except Empty:
                    # No data received; keep the connection alive
                    yield f"data: {{'message': 'no data received'}}\n\n"

        except Exception as e:
            yield f"data: {{'error': '{str(e)}'}}\n\n"

@api_view(["GET"])
@permission_classes([AllowAny])
def get_live_data(request):
    app = IBKRClient()
    try:
        app.connect("127.0.0.1", 7496, clientId=52)

        contract = Contract()
        contract.symbol = "NVDA"
        contract.secType = "STK"
        contract.currency = "USD"
        contract.exchange = "SMART"

        # Start the IBKR app in a separate thread
        threading.Thread(target=app.run, daemon=True).start()

        return StreamingHttpResponse(
            app.get_data_stream(3001, contract),
            content_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Access-Control-Allow-Origin": "*",  # Adjust for production
            },
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# views.py
from django.http import StreamingHttpResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import threading
import time
import json

import json
import time
import threading
from queue import Queue, Empty
from django.http import StreamingHttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from ib_insync import Contract
from ib_insync.ib import IB
from django.http import JsonResponse

import threading
import time
import json
from queue import Queue, Empty
from ib_insync import Contract
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from django.http import StreamingHttpResponse, JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
import json
import threading
import time
from queue import Queue, Empty
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from django.http import StreamingHttpResponse, JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny

class IBKRClient(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.real_time_data = Queue()
        self.is_running = False
        self.active_requests = set()  # Track active request IDs
        self.req_counter = 1  # Unique request counter

    def cancel_request(self, reqId):
        if reqId in self.active_requests:
            try:
                self.cancelRealTimeBars(reqId)
                print(f"Real-time bars request {reqId} canceled.")
                self.active_requests.remove(reqId)
            except Exception as e:
                print(f"Error canceling request {reqId}: {e}")

    def realtimeBar(self, reqId, time, open_, high, low, close, volume, wap, count):
        print(f"Realtime bar received: reqId={reqId}, time={time}, open={open_}, close={close}")
        bar = {
            "time": time,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": float(volume),
            "wap": float(wap),
            "count": count,
        }
        self.real_time_data.put(bar)

    def run(self):
        self.is_running = True
        super().run()
        self.is_running = False

    def get_data_stream(self, reqId, contract):
        self.cancel_request(reqId)  # Cancel any previous request
        print(f"Requesting real-time bars for {contract.symbol} with reqId={reqId}")
        self.reqRealTimeBars(reqId, contract, 5, "TRADES", 0, [])
        self.active_requests.add(reqId)

        try:
            while True:
                try:
                    # Get data from the queue with a timeout
                    bar = self.real_time_data.get(timeout=1)
                    print(f"Yielding bar data for reqId={reqId}: {bar}")
                    yield f"data: {json.dumps(bar)}\\n\\n"
                except Empty:
                    print(f"No data received for reqId={reqId}")
                    yield f"data: {{\"message\": \"no data received\"}}\\n\\n"
        except GeneratorExit:
            # Handle client disconnect
            print(f"Client disconnected, stopping stream for reqId={reqId}")
            self.cancel_request(reqId)
        except Exception as e:
            print(f"Error in get_data_stream: {str(e)}")
            yield f"data: {{\"error\": \"{str(e)}\"}}\\n\\n"


# Utility functions
def disconnect_client(app):
    try:
        app.disconnect()
        print("Disconnected from TWS.")
    except Exception as e:
        print(f"Error during disconnection: {e}")

def start_client_thread(app):
    if not app.is_running:
        threading.Thread(target=app.run, daemon=True).start()
    else:
        print("Client is already running.")

@api_view(["GET"])
@permission_classes([AllowAny])
def get_live_data(request):
    app = IBKRClient()
    try:
        # Disconnect previous client if needed
        disconnect_client(app)

        print(f"Connecting to TWS on 127.0.0.1:7496 with clientId 53")
        app.connect("127.0.0.1", 7496, clientId=53)

        if not app.isConnected():
            raise Exception("Failed to connect to TWS. Ensure it is running and accessible.")

        # Define the contract
        contract = Contract()
        contract.symbol = "NVDA"  # Replace with desired symbol
        contract.secType = "STK"
        contract.currency = "USD"
        contract.exchange = "SMART"

        # Start the IBKR app thread
        start_client_thread(app)

        reqId = app.req_counter  # Unique ID for the request
        app.req_counter += 1

        return StreamingHttpResponse(
            app.get_data_stream(reqId, contract),
            content_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Access-Control-Allow-Origin": "*",  # Adjust for production
                "X-Accel-Buffering": "no",  # Disable buffering
            },
        )
    except Exception as e:
        print(f"Error in get_live_data: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)

# Example usage for Django development server
# Add `path('api/live_data', get_live_data)` to your Django URLs.

from django.http import StreamingHttpResponse
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import threading
import time

# Import TickTypeEnum from your ticktype.py
from api.ticktype import TickTypeEnum

# Define the IBKR app
class LiveMarketDataApp(EClient, EWrapper):
    def __init__(self):
        EClient.__init__(self, self)
        self.data_stream = []
        self.orderId = 0  # Initialize orderId

    def nextValidId(self, orderId: int):
        self.orderId = orderId

    def nextId(self):
        self.orderId += 1
        return self.orderId

    def tickPrice(self, reqId, tickType, price, attrib):
        tick_type_str = TickTypeEnum.to_str(tickType)
        self.data_stream.append(f"Price - reqId: {reqId}, tickType: {tick_type_str}, price: {price}\\n")

    def tickSize(self, reqId, tickType, size):
        tick_type_str = TickTypeEnum.to_str(tickType)
        self.data_stream.append(f"Size - reqId: {reqId}, tickType: {tick_type_str}, size: {size}\\n")


# Define a generator function for streaming
def live_data_stream(app):
    while True:
        if app.data_stream:
            yield app.data_stream.pop(0)
        time.sleep(0.1)

# Django view function
def getLiveData(request):
    # Set up the IBKR app
    app = LiveMarketDataApp()
    app.connect("127.0.0.1", 7496, 55)

    # Run the IBKR app in a separate thread
    threading.Thread(target=app.run, daemon=True).start()
    time.sleep(1)

    # Define the contract for the market data
    mycontract = Contract()
    mycontract.symbol = "NVDA"
    mycontract.secType = "STK"
    mycontract.exchange = "SMART"
    mycontract.currency = "USD"

    # Request live market data
    app.reqMarketDataType(3)  # Real-time market data
    app.reqMktData(app.nextId(), mycontract, "", False, False, [])

    # Return a StreamingHttpResponse
    response = StreamingHttpResponse(live_data_stream(app), content_type="text/plain")
    response['Cache-Control'] = 'no-cache'
    return response


from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.views import APIView
from django.http import StreamingHttpResponse
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import threading
import time

# Import TickTypeEnum from your ticktype.py
from api.ticktype import TickTypeEnum

# Define the IBKR app
class LiveMarketDataApp(EClient, EWrapper):
    def __init__(self):
        EClient.__init__(self, self)
        self.data_stream = []
        self.orderId = 0  # Initialize orderId

    def nextValidId(self, orderId: int):
        self.orderId = orderId

    def nextId(self):
        self.orderId += 1
        return self.orderId

    def tickPrice(self, reqId, tickType, price, attrib):
        tick_type_str = TickTypeEnum.to_str(tickType)
        self.data_stream.append(f"Price - reqId: {reqId}, tickType: {tick_type_str}, price: {price}\\n")

    def tickSize(self, reqId, tickType, size):
        tick_type_str = TickTypeEnum.to_str(tickType)
        self.data_stream.append(f"Size - reqId: {reqId}, tickType: {tick_type_str}, size: {size}\\n")

# Define a generator function for streaming
def live_data_stream(app):
    while True:
        if app.data_stream:
            yield app.data_stream.pop(0)
        time.sleep(0.1)

# DRF API view for live data streaming
class LiveMarketDataAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, *args, **kwargs):
        # Set up the IBKR app
        app = LiveMarketDataApp()
        app.connect("127.0.0.1", 7496, 55)

        # Run the IBKR app in a separate thread
        threading.Thread(target=app.run, daemon=True).start()
        time.sleep(1)

        # Define the contract for the market data
        mycontract = Contract()
        mycontract.symbol = "NVDA"
        mycontract.secType = "STK"
        mycontract.exchange = "SMART"
        mycontract.currency = "USD"

        # Request live market data
        app.reqMarketDataType(3)  # Real-time market data
        app.reqMktData(app.nextId(), mycontract, "", False, False, [])

        # Return a StreamingHttpResponse
        response = StreamingHttpResponse(live_data_stream(app), content_type="text/plain")
        response['Cache-Control'] = 'no-cache'
        return response




class LiveMarketDataApp(EClient, EWrapper):
    def __init__(self):
        EClient.__init__(self, self)
        self.data_stream = []
        self.orderId = 0
        self.current_aggregated_data = defaultdict(lambda: {
            "open": None,
            "close": None,
            "high": None,
            "low": None,
            "volume": 0,
        })
        self.current_interval_start = None

    def nextValidId(self, orderId: int):
        self.orderId = orderId

    def nextId(self):
        self.orderId += 1
        return self.orderId

    def tickPrice(self, reqId, tickType, price, attrib):
        tick_type_str = TickTypeEnum.to_str(tickType)
        if tick_type_str in ["LAST", "CLOSE", "OPEN", "HIGH", "LOW"]:
            self.aggregate_data(reqId, tickType, price)

    def tickSize(self, reqId, tickType, size):
        tick_type_str = TickTypeEnum.to_str(tickType)
        if tick_type_str == "VOLUME":
            self.current_aggregated_data[reqId]["volume"] += size

    def aggregate_data(self, reqId, tickType, price):
        current_time = datetime.now()
        if self.current_interval_start is None:
            self.current_interval_start = current_time

        # Get the current aggregation
        agg = self.current_aggregated_data[reqId]

        # Update aggregation
        if agg["open"] is None:
            agg["open"] = price
        agg["close"] = price
        agg["high"] = max(price, agg["high"]) if agg["high"] is not None else price
        agg["low"] = min(price, agg["low"]) if agg["low"] is not None else price

        # If the interval has elapsed (e.g., 1 second), emit the data
        if (current_time - self.current_interval_start).total_seconds() >= 1:
            self.data_stream.append({
                "reqId": reqId,
                "open": agg["open"],
                "close": agg["close"],
                "high": agg["high"],
                "low": agg["low"],
                "volume": agg["volume"],
            })
            self.current_aggregated_data[reqId] = {
                "open": None,
                "close": None,
                "high": None,
                "low": None,
                "volume": 0,
            }
            self.current_interval_start = current_time


def live_data_stream(app):
    while True:
        if app.data_stream:
            yield f"{app.data_stream.pop(0)}\n"
        time.sleep(0.1)


class LiveMarketDataAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        # Set up the IBKR app
        app = LiveMarketDataApp()
        app.connect("127.0.0.1", 7496, 55)

        # Run the IBKR app in a separate thread
        threading.Thread(target=app.run, daemon=True).start()
        time.sleep(1)

        # Define the contract for the market data
        mycontract = Contract()
        mycontract.symbol = "NVDA"
        mycontract.secType = "STK"
        mycontract.exchange = "SMART"
        mycontract.currency = "USD"

        # Request live market data
        app.reqMarketDataType(3)  # Real-time market data
        app.reqMktData(app.nextId(), mycontract, "", False, False, [])

        # Return a StreamingHttpResponse
        response = StreamingHttpResponse(live_data_stream(app), content_type="text/event-stream")
        response['Cache-Control'] = 'no-cache'
        
        return response
