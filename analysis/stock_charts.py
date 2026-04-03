from django.shortcuts import render
from .models import StockSymbolData, StockPriceData
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd


from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from .models import ThreeMonthsRegSHO, ThreeMonthsShortVolume
#from .sec import get_cik,  check_sec_filing_each_day
import os
from django.conf import settings
from django.http import HttpResponse
import json
from decimal import Decimal
from .stock_data import get_news_for_symbol
from .models import NewsSymbolData, NewsData
from datetime import datetime, timedelta
from django.http import JsonResponse
import pandas as pd
from .models import WatchList, WatchListSymbol, StockSymbolInfo, StockSymbolData, StockPriceData, ThreeMonthsRegSHO, ThreeMonthsShortVolume


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


def preparedRegSho_df():
    start_date = datetime.now()
    end_date = start_date - timedelta(days=90)
    combined_sho_data = ThreeMonthsRegSHO.objects.filter(Date__range=[end_date, start_date]).order_by('-Date')
    # Convert to DataFrames
    combined_sho_df = pd.DataFrame(list(combined_sho_data.values()))
    # Ensure Date columns are timezone-naive UTC
    combined_sho_df['Date'] = pd.to_datetime(combined_sho_df['Date']).dt.tz_localize(None)
    # Add vertical lines if dates info (Reg sho symbol) is found
    combined_sho_df['Date'] = pd.to_datetime(combined_sho_df['Date'])
    return combined_sho_df

def check_symbol_dates_old(df, symbol):
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
    



import pandas as pd
import pandas_market_calendars as mcal

def check_symbol_dates(df, symbol):
    # Ensure 'Date' column is in datetime format
    if 'Date' not in df or 'Symbol' not in df:
        raise ValueError("DataFrame must have 'Date' and 'Symbol' columns.")

    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')  # Convert to datetime
    symbol_data = df[df['Symbol'] == symbol].sort_values(by='Date')  # Filter and sort by Date

    if symbol_data.empty:
        return None  # No data for the given symbol

    # Reset index to ensure sequential indexing
    symbol_data = symbol_data.reset_index(drop=True)

    # Get NASDAQ trading calendar
    nasdaq_calendar = mcal.get_calendar('NASDAQ')
    trading_schedule = nasdaq_calendar.schedule(
        start_date=df['Date'].min(),
        end_date=df['Date'].max()
    )
    all_trading_days = trading_schedule.index  # Get all valid trading days

    # Initialize list for events
    event_dates = []

    # Find entry and exit points
    for idx in range(len(symbol_data)):
        current_date = symbol_data.at[idx, 'Date']
        previous_date = symbol_data.at[idx - 1, 'Date'] if idx > 0 else None

        if previous_date is None or current_date not in all_trading_days:
            # New entry detected
            event_dates.append({'type': 'En.', 'date': current_date})
        elif (current_date - previous_date).days > 1:
            # Check if the gap includes trading days
            trading_gap = all_trading_days[(all_trading_days > previous_date) & (all_trading_days < current_date)]
            if not trading_gap.empty:
                event_dates.append({'type': 'En.', 'date': current_date})

    # Add exit dates for gaps
    for i in range(len(event_dates) - 1):
        entry_date = event_dates[i]['date']
        next_entry_date = event_dates[i + 1]['date']

        # Find the last date before the next entry
        gap_data = symbol_data[(symbol_data['Date'] > entry_date) & (symbol_data['Date'] < next_entry_date)]
        if not gap_data.empty:
            last_date = gap_data['Date'].iloc[-1]
            if last_date != entry_date:
                event_dates.insert(i + 1, {'type': 'Ex.', 'date': last_date})

    # Handle the last exit if there's no 'Con.'
    last_event = event_dates[-1] if event_dates else None
    last_appearance = symbol_data['Date'].max()
    dataset_latest_date = df['Date'].max()

    if last_event and last_event['type'] == 'En.' and last_appearance != dataset_latest_date:
        # Add exit if the last event is an entry and no continue is present
        event_dates.append({'type': 'Ex.', 'date': last_appearance})
    elif last_appearance == dataset_latest_date:
        # Add a "continue" if the last appearance matches the dataset's latest date
        event_dates.append({'type': 'Con.', 'date': dataset_latest_date})

    return event_dates




def generateCharts_old(symbols):
    # Utility function to format numbers for display
    def format_big_number(number):
        return format(number, ",") if number is not None else None

    # Utility function to format percentages
    def format_percentage(value):
        return f"{value * 100:.1f}" if value is not None else 0

    stocks = StockSymbolInfo.objects.filter(symbol__in=symbols).values(
        'symbol', 'company_name', 'volume', 'averageVolume3months', 'averageVolume10days',
        'marketCap', 'fiftyTwoWeekLow', 'fiftyTwoWeekHigh', 'fiftyDayAverage',
        'floatShares', 'sharesOutstanding', 'sharesShort', 'sharesShortPriorMonth',
        'sharesShortPreviousMonthDate', 'dateShortInterest', 'shortPercentOfFloat',
        'heldPercentInsiders', 'heldPercentInstitutions', 'lastSplitFactor',
        'lastSplitDate', 'total_revenue', 'net_income', 'total_assets', 'total_liabilities', 'total_equity'
    )


    # Format the stock data for display
    charts_with_symbol  = []
    for stock in stocks:
        chart_html = generateSingleChart(stock)
                # Format lastSplitFactor into "1:x" or "x:1"
        last_split_factor = stock['lastSplitFactor']
        if last_split_factor is not None:
            if last_split_factor < 1:
                last_split_factor = f"1:{int(1 / last_split_factor)}"
            else:
                last_split_factor = f"{int(last_split_factor)}:1"
        # Format the stock data
        formatted_data = {
            'symbol': stock['symbol'],
            'chart_html': chart_html,
            'company_name': stock['company_name'],
            'volume': format_big_number(stock['volume']),
            'average_volume_3m': format_big_number(stock['averageVolume3months']),
            'average_volume_10d': format_big_number(stock['averageVolume10days']),
            'market_cap': format_big_number(stock['marketCap']),
            'fifty_two_week_range': f"{format_big_number(stock['fiftyTwoWeekLow'])} - {format_big_number(stock['fiftyTwoWeekHigh'])}",
            'fifty_day_average': format_big_number(stock['fiftyDayAverage']),
            'float_shares': format_big_number(stock['floatShares']),
            'shares_outstanding': format_big_number(stock['sharesOutstanding']),
            'shares_short': format_big_number(stock['sharesShort']),
            'shares_short_prior_month': format_big_number(stock['sharesShortPriorMonth']),
            'shares_short_previous_month_date': stock['sharesShortPreviousMonthDate'],
            'date_short_interest': stock['dateShortInterest'],
            'short_percent_of_float': format_percentage(stock['shortPercentOfFloat']),
            'held_percent_insiders': format_percentage(stock['heldPercentInsiders']),
            'held_percent_institutions': format_percentage(stock['heldPercentInstitutions']),
            'last_split_ratio': last_split_factor,
            'last_split_date': stock['lastSplitDate'],
            'total_revenue': format_big_number(stock['total_revenue']),
            'net_income': format_big_number(stock['net_income']),
            'total_assets': format_big_number(stock['total_assets']),
            'total_liabilities': format_big_number(stock['total_liabilities']),
            'total_equity': format_big_number(stock['total_equity'])
        }

        # Append formatted data to the list
        charts_with_symbol.append(formatted_data)

    return charts_with_symbol

def generateCharts(symbols,user_specific):
    # Utility function to format numbers for display
    def format_big_number(number):
        return format(number, ",") if number is not None else None

    # Utility function to format percentages
    def format_percentage(value):
        return f"{value * 100:.1f}" if value is not None else 0

    # Fetch stock data from the database
    stocks = StockSymbolInfo.objects.filter(symbol__in=symbols).values(
        'symbol', 'company_name', 'volume', 'averageVolume3months', 'averageVolume10days',
        'marketCap', 'fiftyTwoWeekLow', 'fiftyTwoWeekHigh', 'fiftyDayAverage',
        'floatShares', 'sharesOutstanding', 'sharesShort', 'sharesShortPriorMonth',
        'sharesShortPreviousMonthDate', 'dateShortInterest', 'shortPercentOfFloat',
        'heldPercentInsiders', 'heldPercentInstitutions', 'lastSplitFactor',
        'lastSplitDate', 'total_revenue', 'net_income', 'total_assets', 'total_liabilities', 'total_equity'
    )

    # Create a mapping of symbol to stock data for efficient ordering
    stock_map = {stock['symbol']: stock for stock in stocks}

    # Prepare the output in the order of input symbols
    charts_with_symbol = []
    for symbol in symbols:
        stock = stock_map.get(symbol)
        if stock is not None:
            chart_html = generateSingleChart(stock,user_specific)

            # Format lastSplitFactor into "1:x" or "x:1"
            last_split_factor = stock['lastSplitFactor']
            if last_split_factor is not None:
                if last_split_factor < 1:
                    last_split_factor = f"1:{int(1 / last_split_factor)}"
                else:
                    last_split_factor = f"{int(last_split_factor)}:1"

            # Format the stock data
            formatted_data = {
                'symbol': stock['symbol'],
                'chart_html': chart_html,
                'company_name': stock['company_name'],
                'volume': format_big_number(stock['volume']),
                'average_volume_3m': format_big_number(stock['averageVolume3months']),
                'average_volume_10d': format_big_number(stock['averageVolume10days']),
                'market_cap': format_big_number(stock['marketCap']),
                'fifty_two_week_range': f"{format_big_number(stock['fiftyTwoWeekLow'])} - {format_big_number(stock['fiftyTwoWeekHigh'])}",
                'fifty_day_average': format_big_number(stock['fiftyDayAverage']),
                'float_shares': format_big_number(stock['floatShares']),
                'shares_outstanding': format_big_number(stock['sharesOutstanding']),
                'shares_short': format_big_number(stock['sharesShort']),
                'shares_short_prior_month': format_big_number(stock['sharesShortPriorMonth']),
                'shares_short_previous_month_date': stock['sharesShortPreviousMonthDate'],
                'date_short_interest': stock['dateShortInterest'],
                'short_percent_of_float': format_percentage(stock['shortPercentOfFloat']),
                'held_percent_insiders': format_percentage(stock['heldPercentInsiders']),
                'held_percent_institutions': format_percentage(stock['heldPercentInstitutions']),
                'last_split_ratio': last_split_factor,
                'last_split_date': stock['lastSplitDate'],
                'total_revenue': format_big_number(stock['total_revenue']),
                'net_income': format_big_number(stock['net_income']),
                'total_assets': format_big_number(stock['total_assets']),
                'total_liabilities': format_big_number(stock['total_liabilities']),
                'total_equity': format_big_number(stock['total_equity'])
            }

            # Append formatted data to the list
            charts_with_symbol.append(formatted_data)

    return charts_with_symbol






def generateSingleChart_old(stock):
            # Utility function to format numbers for display
        def format_big_number(number):
            return format(number, ",") if number is not None else None

        
        last_split_factor = stock['lastSplitFactor']

        # Format lastSplitFactor into "1:x" or "x:1"
        if last_split_factor is not None:
            if last_split_factor < 1:
                last_split_factor = f"1:{int(1 / last_split_factor)}"
            else:
                last_split_factor = f"{int(last_split_factor)}:1"

        symbol = stock['symbol']
        company_name = stock['company_name']
        floatShares = format_big_number(stock['floatShares'])
        lastSplitDate = stock['lastSplitDate']

        # Fetch the latest 90 stock price data
        stock_symbol = StockSymbolData.objects.filter(symbol=stock['symbol']).first()
        html_charts =[]
        stock_data = []
        if stock_symbol:
            # Get the latest 90 records ordered by 'timestamp' in descending order
            #print(stock['symbol'])
            stock_data = StockPriceData.objects.filter(stock_symbol=stock_symbol).order_by('-timestamp')[:64]

            # Extract the stock price data into a DataFrame
            stock_prices = []
            if stock_data.exists():
                df = pd.DataFrame(list(stock_data.values('timestamp', 'open', 'high', 'low', 'close', 'volume','ShortVolume')))
                df.rename(columns={'timestamp': 'Date'}, inplace=True)
                df['Date'] = pd.to_datetime(df['Date'])
                df.set_index('Date', inplace=True)

                # Sort the DataFrame by Date in ascending order
                df.sort_index(ascending=True, inplace=True)
                # Prepare data
                combined_sho_df = preparedRegSho_df()
                dates_info = check_symbol_dates(combined_sho_df, stock['symbol'])

                stock_data = df
                #print(stock_data)
                dates = pd.to_datetime(stock_data.index)
                #print(dates)
                '''
                try:
                    sec_links, form_types, sec_hover_texts = check_sec_filing_each_day(stock['symbol'], dates)
                except NameError:
                    # Handle the case where the function does not exist
                    sec_links = ' '
                    form_types = ' '
                    sec_hover_texts = ' '
                '''

                #print(sec_links)
                # Ensure dates is a Pandas Series for apply functionality
                dates_series = pd.Series(dates)
                #print(dates_series)
                news_presence = dates_series.apply(
                    lambda d: '<br>'.join(
                        f"<a href='{news['NewsLink']}' target='_blank'>N</a>"
                        for news in NewsData.objects.filter(
                            news_symbol__symbol=stock['symbol'], Date=d.date()
                        ).values('NewsLink')
                    ) if NewsData.objects.filter(
                        news_symbol__symbol=stock['symbol'], Date=d.date()
                    ).exists() else ''
                )
                news_hovertext = stock_data.index.map(
                    lambda d: '<br>'.join(
                        f"Title: {news['NewsTitle']}<br>Publish Time: {news['providerPublishTime']}"
                        for news in NewsData.objects.filter(
                            news_symbol__symbol=stock['symbol'], Date=d.date()
                        ).values('NewsTitle', 'providerPublishTime')
                    ) if NewsData.objects.filter(news_symbol__symbol=stock['symbol'], Date=d.date()).exists() else ''
                )
                #print(news_presence)
                # Add formatted stock data including stock prices and short volume
                # Shift the 'Close' column by one day to get the previous day's close
                stock_data['PreviousClose'] = stock_data['close'].shift(1)

                # Calculate the percentage change from previous close to current close
                stock_data['PriceChangePercent'] = ((stock_data['close'] - stock_data['PreviousClose']) / stock_data['PreviousClose']) * 100

                # Format the text for annotations based on PriceChangePercent
                price_change_text = [
                    f"{change:.2f}" if not pd.isna(change) else "" for change in stock_data['PriceChangePercent']
                ]

                # Calculate daily Open to High price change in %
                stock_data['OHPriceChangePercent'] = ((stock_data['high'] - stock_data['open']) / stock_data['open']) * 100
                O_H_price_change_text = [
                f"{change:.2f}" for change in stock_data['OHPriceChangePercent']
                ]

                # Calculate daily Previous close to High price change in %
                stock_data['PreCloseToHighPriceChangePercent'] = ((stock_data['high'] - stock_data['PreviousClose']) / stock_data['PreviousClose']) * 100
                Pre_C_H_price_change_text = [
                f"{change:.2f}" for change in stock_data['PreCloseToHighPriceChangePercent']
                ]
                    # Add color for positive/negative change
                price_change_color = ['green' if change > 0 else 'red' for change in stock_data['PriceChangePercent'].fillna(0)]
                OH_price_change_color = ['green' if change > 0 else 'red' for change in stock_data['OHPriceChangePercent'].fillna(0)]
                PreCloseToHigh_price_change_color = ['green' if change > 0 else 'red' for change in stock_data['PreCloseToHighPriceChangePercent'].fillna(0)]

            
                    # Calculate bar width
                date_diffs =stock_data.index.to_series().diff().dropna()  # Get the differences between consecutive dates
                avg_date_diff = date_diffs.dt.total_seconds().mean()  # Average difference in seconds
                bar_width = avg_date_diff * 0.8 * 1000 if avg_date_diff > 0 else 86400000  # Default to 1 day in milliseconds
                #print(bar_width)
                    # Calculate colors for the candlestick chart
                colors = ['green' if close > open else 'red' for open, close in zip(stock_data['open'], stock_data['close'])]
                # Construct the Yahoo Finance URL
                yahoo_finance_url = f"https://finance.yahoo.com/quote/{symbol}"
                if yahoo_finance_url:
                    y_finance_url = yahoo_finance_url
                else:
                    y_finance_url = "#"
                    # Inject the hyperlink into the subplot title
                fig = make_subplots(
                    rows=3, 
                    cols=1, 
                    shared_xaxes=True, 
                    vertical_spacing=0.1,
                    subplot_titles=(
                        f'<b><a href="{y_finance_url}" target="_blank">{symbol}</a> :</b> {company_name}', 
                        'Total Volume', 
                        f'Short Volume | Float: {floatShares}'
                    ),
                    row_width=[0.15, 0.2, 0.65]
                )
                # Add candlestick trace
                fig.add_trace(
                    go.Candlestick(
                        x=stock_data.index,
                        open=stock_data['open'],
                        high=stock_data['high'],
                        low=stock_data['low'],
                        close=stock_data['close'],
                        name='Candlestick'
                    ),
                    row=1, col=1
                )
                for i, (index, row) in enumerate(stock_data.iterrows()):
                    fig.add_annotation(
                        x=index,
                        #y=row['High']* 1.2,  # Position slightly above the candlestick high
                        text=f"{price_change_text[i]}",
                        showarrow=False,
                        font=dict(color=price_change_color[i], size=12),
                        #hovertext=f"Price Change: {price_change_text[i]}%", 
                        hovertext=(
                            f"<span></span><br>"
                            f"<span style='color:{price_change_color[i]};'>"
                            f"&nbsp;&nbsp;Price Change: {price_change_text[i]}%&nbsp;&nbsp;</span><br>"

                            f"<span style='color:{OH_price_change_color[i]};'>"
                            f"&nbsp;&nbsp;R-O/H Change: {O_H_price_change_text[i]}%&nbsp;&nbsp;</span><br>"

                            f"<span style='color:{PreCloseToHigh_price_change_color[i]};'>"
                            f"&nbsp;&nbsp;Prev-C/H Change: {Pre_C_H_price_change_text[i]}%&nbsp;&nbsp;</span>"
                            f"<span></span>"
                        ),
                        textangle=90,              # Rotate text by 90 degrees
                        
                        
                    )

                
                # Add total volume bars (green and red)
                fig.add_trace(
                    go.Bar(
                        x=stock_data.index,
                        y=[v if c == 'green' else 0 for v, c in zip(stock_data['volume'], colors)],
                        name='Total Volume Increase',
                        marker_color='green',
                        width=bar_width
                    ),
                    row=2, col=1
                )
                fig.add_trace(
                    go.Bar(
                        x=stock_data.index,
                        y=[v if c == 'red' else 0 for v, c in zip(stock_data['volume'], colors)],
                        name='Total Volume Decrease',
                        marker_color='red',
                        #text=sec_links,                
                        textposition='outside',     # Inside the bar to move it downward
                        textangle=90,              # Rotate text by 90 degrees
                        #hovertext=sec_hover_texts,       # Show FormDescription in hover
                        insidetextanchor='start',  # Anchor text to the bottom of the bar               
                        width=bar_width
                    ),
                    row=2, col=1
                )

                # Add short volume bars if available
                
                fig.add_trace(
                    go.Bar(
                        x=stock_data.index,
                        y=stock_data['ShortVolume'],
                        name='Short Volume',
                        marker_color='red',
                        text=news_presence,  # Clickable links for news
                        textposition='outside',
                        hovertext=news_hovertext  # Use the prepared hovertext
                                    
                    ),
                    row=3, col=1
                )

                # Add vertical lines if dates info (Reg sho symbol) is found
                dates_info = check_symbol_dates(combined_sho_df, symbol)
                if dates_info:
                    for key, date in dates_info.items():
                        if date:  # Only add a line if the date is not None
                            date_ts = date.timestamp() * 1000
                            fig.add_vline(x=date_ts, line_width=2, line_dash="dash", line_color="blue", annotation_text=key, annotation_position="top right")
                

            
                        # Update y-axis properties for each row to move y-axis to the right
                fig.update_yaxes(side='right', row=1, col=1)
                fig.update_yaxes(side='right', row=2, col=1)
                fig.update_yaxes(side='right', row=3, col=1)
                # Adjust text alignment and padding
                #fig.update_yaxes(tickfont=dict(size=12), side='right', tickangle=0, tickmode='auto', ticklen=10, tickwidth=1, tickcolor='#000')
                # Update the layout to adjust the legend position
                fig.update_layout(
                    legend=dict(
                        x=1.05,  # Moves the legend slightly right from the default position
                        y=1,
                        xanchor='left',  # Anchors the legend at its left edge
                        yanchor='top'    # Anchors the legend at its top edge
                    ),
                uniformtext_minsize=8,  # Set the minimum text size for all text elements in the chart
                uniformtext_mode='show'  # Ensures that the text size is consistent across all elements
                )
                
                # Add annotation for the stock split if available
                if last_split_factor and last_split_factor.strip():  # Check if last_split_factor is non-empty
                    # Convert last split date to the appropriate timestamp format
                    split_annotation_date = pd.to_datetime(lastSplitDate).date()  # Convert to date only
                    dates_as_dates = dates.date  # Convert the DatetimeIndex to date format
                else:
                    split_annotation_date = None
                    dates_as_dates = dates.date

                if split_annotation_date in dates_as_dates:
                    # Use Decimal for multiplication to avoid TypeError
                    y_position = stock_data['high'].max() * Decimal('1.05')
                    # Add the annotation for stock split
                    fig.add_annotation(
                        x=split_annotation_date,
                        y=float(y_position),  # Convert Decimal back to float for the plot
                        text='S',  # Text to display
                        showarrow=False,
                        font=dict(color='blue', size=12, family='Arial Black'),
                        bgcolor='lightyellow',
                        bordercolor='black',
                        borderwidth=1,
                        xanchor='center',
                        yanchor='bottom'
                    )



                
                # Update layout for better presentation
                fig.update_layout(
                    margin=dict(l=0, r=0, t=50, b=50),  # margins
                    xaxis_rangeslider_visible=False,
                    title='',
                    hovermode='x unified',
                    height=600,
                    #showlegend=False,  # Hide legend
                    autosize=True,     # Ensure it resizes responsively
                    
                )
                
                chart_html = fig.to_html(full_html=False, include_plotlyjs=False)

            return chart_html 

from django.db.models import Q
import pandas as pd
from .models import BuyNSell
from django.contrib.auth.models import User
from django.http import HttpRequest
def generateSingleChart(stock,user_specific):
            # Utility function to format numbers for display
        def format_big_number(number):
            return format(number, ",") if number is not None else None

        
        last_split_factor = stock['lastSplitFactor']

        # Format lastSplitFactor into "1:x" or "x:1"
        if last_split_factor is not None:
            if last_split_factor < 1:
                last_split_factor = f"1:{int(1 / last_split_factor)}"
            else:
                last_split_factor = f"{int(last_split_factor)}:1"

        symbol = stock['symbol']
        company_name = stock['company_name']
        floatShares = format_big_number(stock['floatShares'])
        lastSplitDate = stock['lastSplitDate']

        # Fetch the latest 90 stock price data
        stock_symbol = StockSymbolData.objects.filter(symbol=stock['symbol']).first()
        html_charts =[]
        stock_data = []
        if stock_symbol:
            # Get the latest 90 records ordered by 'timestamp' in descending order
            #print(stock['symbol'])
            stock_data = StockPriceData.objects.filter(stock_symbol=stock_symbol).order_by('-timestamp')[:64]

            # Extract the stock price data into a DataFrame
            stock_prices = []
            if stock_data.exists():
                df = pd.DataFrame(list(stock_data.values('timestamp', 'open', 'high', 'low', 'close', 'volume','ShortVolume')))
                df.rename(columns={'timestamp': 'Date'}, inplace=True)
                df['Date'] = pd.to_datetime(df['Date'])
                df.set_index('Date', inplace=True)

                # Sort the DataFrame by Date in ascending order
                df.sort_index(ascending=True, inplace=True)
                # Prepare data


                stock_data = df
                #print(stock_data)
                dates = pd.to_datetime(stock_data.index)
                #print(dates)
                '''
                try:
                    sec_links, form_types, sec_hover_texts = check_sec_filing_each_day(stock['symbol'], dates)
                except NameError:
                    # Handle the case where the function does not exist
                    sec_links = ' '
                    form_types = ' '
                    sec_hover_texts = ' '
                '''

                #print(sec_links)
                # Ensure dates is a Pandas Series for apply functionality
                dates_series = pd.Series(dates)
                #print(dates_series)
                news_presence = dates_series.apply(
                    lambda d: '<br>'.join(
                        f"<a href='{news['NewsLink']}' target='_blank'>N</a>"
                        for news in NewsData.objects.filter(
                            news_symbol__symbol=stock['symbol'], Date=d.date()
                        ).values('NewsLink')
                    ) if NewsData.objects.filter(
                        news_symbol__symbol=stock['symbol'], Date=d.date()
                    ).exists() else ''
                )
                news_hovertext = stock_data.index.map(
                    lambda d: '<br>'.join(
                        f"Title: {news['NewsTitle']}<br>Publish Time: {news['providerPublishTime']}"
                        for news in NewsData.objects.filter(
                            news_symbol__symbol=stock['symbol'], Date=d.date()
                        ).values('NewsTitle', 'providerPublishTime')
                    ) if NewsData.objects.filter(news_symbol__symbol=stock['symbol'], Date=d.date()).exists() else ''
                )
                #print(news_presence)
                # Add formatted stock data including stock prices and short volume
                # Shift the 'Close' column by one day to get the previous day's close
                stock_data['PreviousClose'] = stock_data['close'].shift(1)

                # Calculate the percentage change from previous close to current close
                #stock_data['PriceChangePercent'] = ((stock_data['close'] - stock_data['PreviousClose']) / stock_data['PreviousClose']) * 100
                # Avoid DivisionByZero or NoneType errors
                stock_data['PriceChangePercent'] = stock_data.apply(
                    lambda row: ((row['close'] - row['PreviousClose']) / row['PreviousClose']) * 100
                    if row['PreviousClose'] and row['PreviousClose'] != 0 else None,
                    axis=1
                )

                # Format the text for annotations based on PriceChangePercent
                price_change_text = [
                    f"{change:.2f}" if not pd.isna(change) else "" for change in stock_data['PriceChangePercent']
                ]

                # Calculate daily Open to High price change in %
                #stock_data['OHPriceChangePercent'] = ((stock_data['high'] - stock_data['open']) / stock_data['open']) * 100
                #O_H_price_change_text = [
                    #f"{change:.2f}" for change in stock_data['OHPriceChangePercent']
                #]
                # Avoid DivisionByZero or NoneType errors
                stock_data['OHPriceChangePercent'] = stock_data.apply(
                    lambda row: ((row['high'] - row['open']) / row['open']) * 100
                    if row['open'] and row['open'] != 0 else None,
                    axis=1
                )
                O_H_price_change_text = [
                    f"{change:.2f}" if change is not None else "" for change in stock_data['OHPriceChangePercent']
                ]



                # Calculate daily Previous close to High price change in %
                #stock_data['PreCloseToHighPriceChangePercent'] = ((stock_data['high'] - stock_data['PreviousClose']) / stock_data['PreviousClose']) * 100
                #Pre_C_H_price_change_text = [
                #f"{change:.2f}" for change in stock_data['PreCloseToHighPriceChangePercent']
                #]
                stock_data['PreCloseToHighPriceChangePercent'] = stock_data.apply(
                    lambda row: ((row['high'] - row['PreviousClose']) / row['PreviousClose']) * 100
                    if row['PreviousClose'] and row['PreviousClose'] != 0 else None,
                    axis=1
                )
                Pre_C_H_price_change_text = [
                    f"{change:.2f}" if change is not None else "" for change in stock_data['PreCloseToHighPriceChangePercent']
                ]


                    # Add color for positive/negative change
                price_change_color = ['green' if change > 0 else 'red' for change in stock_data['PriceChangePercent'].fillna(0)]
                OH_price_change_color = ['green' if change > 0 else 'red' for change in stock_data['OHPriceChangePercent'].fillna(0)]
                PreCloseToHigh_price_change_color = ['green' if change > 0 else 'red' for change in stock_data['PreCloseToHighPriceChangePercent'].fillna(0)]

            
                    # Calculate bar width
                date_diffs =stock_data.index.to_series().diff().dropna()  # Get the differences between consecutive dates
                avg_date_diff = date_diffs.dt.total_seconds().mean()  # Average difference in seconds
                bar_width = avg_date_diff * 0.8 * 1000 if avg_date_diff > 0 else 86400000  # Default to 1 day in milliseconds
                #print(bar_width)
                    # Calculate colors for the candlestick chart
                colors = ['green' if close > open else 'red' for open, close in zip(stock_data['open'], stock_data['close'])]
                # Construct the Yahoo Finance URL
                yahoo_finance_url = f"https://finance.yahoo.com/quote/{symbol}"
                if yahoo_finance_url:
                    y_finance_url = yahoo_finance_url
                else:
                    y_finance_url = "#"
                    # Inject the hyperlink into the subplot title




                fig = make_subplots(
                    rows=3, 
                    cols=1, 
                    shared_xaxes=True, 
                    vertical_spacing=0.1,
                    subplot_titles=(
                        f'<b><a href="{y_finance_url}" target="_blank">{symbol}</a> :</b> {company_name}', 
                        'Total Volume', 
                        f'Short Volume | Float: {floatShares}'
                    ),
                    row_width=[0.15, 0.2, 0.65]
                )
                # Add candlestick trace
                fig.add_trace(
                    go.Candlestick(
                        x=stock_data.index,
                        open=stock_data['open'],
                        high=stock_data['high'],
                        low=stock_data['low'],
                        close=stock_data['close'],
                        name='Candlestick'
                    ),
                    row=1, col=1
                )
                for i, (index, row) in enumerate(stock_data.iterrows()):
                    fig.add_annotation(
                        x=index,
                        #y=row['High']* 1.2,  # Position slightly above the candlestick high
                        text=f"{price_change_text[i]}",
                        showarrow=False,
                        font=dict(color=price_change_color[i], size=12),
                        #hovertext=f"Price Change: {price_change_text[i]}%", 
                        hovertext=(
                            f"<span></span><br>"
                            f"<span style='color:{price_change_color[i]};'>"
                            f"&nbsp;&nbsp;Price Change: {price_change_text[i]}%&nbsp;&nbsp;</span><br>"

                            f"<span style='color:{OH_price_change_color[i]};'>"
                            f"&nbsp;&nbsp;R-O/H Change: {O_H_price_change_text[i]}%&nbsp;&nbsp;</span><br>"

                            f"<span style='color:{PreCloseToHigh_price_change_color[i]};'>"
                            f"&nbsp;&nbsp;Prev-C/H Change: {Pre_C_H_price_change_text[i]}%&nbsp;&nbsp;</span>"
                            f"<span></span>"
                        ),
                        textangle=90,              # Rotate text by 90 degrees
                        
                        
                    )

                
                # Add total volume bars (green and red)
                fig.add_trace(
                    go.Bar(
                        x=stock_data.index,
                        y=[v if c == 'green' else 0 for v, c in zip(stock_data['volume'], colors)],
                        name='Total Volume Increase',
                        marker_color='green',
                        width=bar_width
                    ),
                    row=2, col=1
                )
                fig.add_trace(
                    go.Bar(
                        x=stock_data.index,
                        y=[v if c == 'red' else 0 for v, c in zip(stock_data['volume'], colors)],
                        name='Total Volume Decrease',
                        marker_color='red',
                        #text=sec_links,                
                        textposition='outside',     # Inside the bar to move it downward
                        textangle=90,              # Rotate text by 90 degrees
                        #hovertext=sec_hover_texts,       # Show FormDescription in hover
                        insidetextanchor='start',  # Anchor text to the bottom of the bar               
                        width=bar_width
                    ),
                    row=2, col=1
                )

                # Add short volume bars if available
                
                fig.add_trace(
                    go.Bar(
                        x=stock_data.index,
                        y=stock_data['ShortVolume'],
                        name='Short Volume',
                        marker_color='red',
                        text=news_presence,  # Clickable links for news
                        textposition='outside',
                        hovertext=news_hovertext  # Use the prepared hovertext
                                    
                    ),
                    row=3, col=1
                )
                combined_sho_df = preparedRegSho_df()
                #dates_info = check_symbol_dates(combined_sho_df, stock['symbol'])
                # Add vertical lines if dates info (Reg sho symbol) is found

                dates_info = check_symbol_dates(combined_sho_df, symbol)
                #print(f"dates_info:{dates_info}")
                
                if dates_info:
                    for event in dates_info:
                        event_type = event['type']
                        event_date = event['date']
                        if event_date:  # Only add a line if the date is valid
                            date_ts = pd.Timestamp(event_date).timestamp() * 1000  # Convert to milliseconds
                            fig.add_vline(
                                x=date_ts,
                                line_width=2,
                                line_dash="dash",
                                line_color="blue",
                                annotation_text=event_type,
                                annotation_position="top right"
                            )
                
            
                        # Update y-axis properties for each row to move y-axis to the right
                fig.update_yaxes(side='right', row=1, col=1)
                fig.update_yaxes(side='right', row=2, col=1)
                fig.update_yaxes(side='right', row=3, col=1)
                # Adjust text alignment and padding
                #fig.update_yaxes(tickfont=dict(size=12), side='right', tickangle=0, tickmode='auto', ticklen=10, tickwidth=1, tickcolor='#000')
                # Update the layout to adjust the legend position
                fig.update_layout(
                    legend=dict(
                        x=1.05,  # Moves the legend slightly right from the default position
                        y=1,
                        xanchor='left',  # Anchors the legend at its left edge
                        yanchor='top'    # Anchors the legend at its top edge
                    ),
                uniformtext_minsize=8,  # Set the minimum text size for all text elements in the chart
                uniformtext_mode='show'  # Ensures that the text size is consistent across all elements
                )
                
                # Add annotation for the stock split if available
                if last_split_factor and last_split_factor.strip():  # Check if last_split_factor is non-empty
                    # Convert last split date to the appropriate timestamp format
                    split_annotation_date = pd.to_datetime(lastSplitDate).date()  # Convert to date only
                    dates_as_dates = dates.date  # Convert the DatetimeIndex to date format
                else:
                    split_annotation_date = None
                    dates_as_dates = dates.date

                if split_annotation_date in dates_as_dates:
                    # Use Decimal for multiplication to avoid TypeError
                    y_position = stock_data['high'].max() * Decimal('1.08')
                                            # Create hover text with transaction details
                    split_hover_text = "<br>".join([
                        f"Split Date: {split_annotation_date}<br>"
                        f"Split Ratio: {last_split_factor}<br>"
                   
                    ])
                    # Add the annotation for stock split
                    fig.add_annotation(
                        x=split_annotation_date,
                        y=float(y_position),  # Convert Decimal back to float for the plot
                        text='S',  # Text to display
                        showarrow=False,
                        font=dict(color='blue', size=12, family='Arial Black'),
                        bgcolor='lightyellow',
                        bordercolor='black',
                        borderwidth=1,
                        hovertext = split_hover_text,
                        xanchor='center',
                        yanchor='bottom'
                    )

                # Prepare annotations for transaction types (B, S, O)
                transactions = BuyNSell.objects.filter(
                    user=user_specific,
                    symbol=symbol,
                    date__range=[df.index.min().date(), df.index.max().date()],
                    transaction_type__in=['B', 'S', 'O']
                )

                # Proceed only if there are transactions for the symbol
                if transactions.exists():
                    # Group transactions by date
                    transaction_annotations = transactions.values('date', 'transaction_type', 'quantity', 'fill_price', 'name','order_id')
                    grouped_transactions = pd.DataFrame(transaction_annotations).groupby('date').apply(lambda x: x.to_dict('records'))

                    # Add transaction annotations to the chart
                    for date, transaction_details in grouped_transactions.items():
                        y_position = float(df['high'].max()) * 1.0  # Adjust position above candlestick high

                        # Create hover text with transaction details
                        hover_text = "<br>".join([
                            f"Type: {detail['transaction_type']}<br>"
                            f"Quantity: {detail['quantity']}<br>"
                            f"Fill Price: {detail['fill_price']}<br>"
                            f"Total Price: {detail['quantity']*detail['fill_price']}<br>"
                            f"Order Id: {detail['order_id']}<br>"
                            for detail in transaction_details
                        ])

                        # Create display text (e.g., "B | S | O")
                        display_text = " | ".join(set(detail['transaction_type'] for detail in transaction_details))

                        fig.add_annotation(
                            x=date,
                            y=y_position,
                            text=display_text,  # Combine transaction types (e.g., "B | S | O")
                            showarrow=False,
                            font=dict(color='blue', size=10),
                            bgcolor='lightyellow',
                            bordercolor='black',
                            borderwidth=1,
                            xanchor='center',
                            yanchor='bottom',
                            hovertext=hover_text  # Add hover text with transaction details
                        )
                
                # Update layout for better presentation
                fig.update_layout(
                    margin=dict(l=0, r=0, t=50, b=50),  # margins
                    xaxis_rangeslider_visible=False,
                    title='',
                    hovermode='x unified',
                    height=600,
                    #showlegend=False,  # Hide legend
                    autosize=True,     # Ensure it resizes responsively
                    
                )
                
                chart_html = fig.to_html(full_html=False, include_plotlyjs=False)

            return chart_html 

         