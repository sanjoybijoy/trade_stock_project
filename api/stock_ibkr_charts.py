
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



from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from django.http import StreamingHttpResponse
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
import threading
import time
from datetime import datetime
from collections import defaultdict
from api.ticktype import TickTypeEnum


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
        self.active_requests = set() # Manages active market data requests

    def reqMktData(self, reqId, contract, genericTickList, snapshot, regulatorySnapshot, mktDataOptions):
        super().reqMktData(reqId, contract, genericTickList, snapshot, regulatorySnapshot, mktDataOptions)
        self.active_requests.add(reqId)

    def cancel_all_mkt_data(self):
        for reqId in list(self.active_requests):
            self.cancelMktData(reqId)
            self.active_requests.remove(reqId)

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


    #def disconnect(self):
        #self.disconnect()  # Disconnect from IBKR
        #print("Disconnected from IBKR.")

#def live_data_stream(app):
    #while True:
        #if app.data_stream:
            #yield f"{app.data_stream.pop(0)}\n"
        #time.sleep(0.1)


import time
from django.http import StreamingHttpResponse

class LiveMarketDataAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        app = LiveMarketDataApp()
        try:
            app.connect("127.0.0.1", 7496, 56)
            threading.Thread(target=app.run, daemon=True).start()
            time.sleep(1)

            # Define the contract
            mycontract = Contract()
            mycontract.symbol = "NVDA"
            mycontract.secType = "STK"
            mycontract.exchange = "SMART"
            mycontract.currency = "USD"

            # Request market data
            app.reqMarketDataType(3)
            app.reqMktData(app.nextId(), mycontract, "", False, False, [])

            # Stream data
            def event_stream():
                try:
                    while True:
                        if app.data_stream:
                            yield f"data: {app.data_stream.pop(0)}\n\n"
                        time.sleep(0.1)
                finally:
                    app.cancelMktData(app.nextId())
                    #app.cancel_all_mkt_data()
                    #app.disconnect()

            response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
            response['Cache-Control'] = 'no-cache'
            return response
            #response = event_stream() 
            #return Response(response)
        except Exception as e:
            app.cancel_all_mkt_data()
            #app.disconnect()
            raise e





