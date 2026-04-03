from django.shortcuts import render
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

def stock_charts(symbols_to_search,user_specific):

    symbols_to_search = symbols_to_search
    charts_html = []
    # Dates for querying data
    start_date = datetime.now()
    end_date = start_date - timedelta(days=90)
    # Generate datetime objects directly
    #dates = [start_date - timedelta(days=i) for i in range((start_date - end_date).days + 1)]

    def check_news_each_day(ticker, date_range):
        stock = yf.Ticker(ticker)
        news = stock.news
        news_links = []
        hover_texts = []  # To hold the news title for hover text

        for single_date in date_range:
            news_link = ""
            hover_text = ""
            for article in news:
                article_date = datetime.utcfromtimestamp(article['providerPublishTime']).date()
                if article_date == single_date.date():
                    # Link and title for hover text
                    news_link = f"<a href='{article['link']}' target='_blank'>N</a>"
                    hover_text = article['title']
                    break
            news_links.append(news_link or " ")
            hover_texts.append(hover_text or " ")
        return news_links, hover_texts


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
    
    # It will Check Reg show symbol dates
    def check_symbol_dates(df, symbol):
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

   

    # Fetch data from Django models
    combined_sho_data = ThreeMonthsRegSHO.objects.filter(Date__range=[end_date, start_date]).order_by('-Date')
    combined_data = ThreeMonthsShortVolume.objects.filter(Date__range=[end_date, start_date]).order_by('-Date')

    # Convert to DataFrame
    combined_sho_df = pd.DataFrame(list(combined_sho_data.values()))
    combined_data_df = pd.DataFrame(list(combined_data.values()))

    # Ensure Date columns are timezone-naive UTC
    combined_sho_df['Date'] = pd.to_datetime(combined_sho_df['Date']).dt.tz_localize(None)
    combined_data_df['Date'] = pd.to_datetime(combined_data_df['Date']).dt.tz_localize(None)

    # Download data for '3mo' and if it fails due to a Error, it will try for '1mo'.
    def safe_download(symbol, period='3mo'):
        try:
            # Try fetching the data for the default period (3 months)
            data = yf.download(symbol, period=period, interval='1d')
            if data.empty:
                raise ValueError(f"No data returned for {symbol} using period {period}")
            return data
        except ValueError as e:
            # If there is an error or empty data, fall back to '1mo'
            if period == '3mo':
                print(f"Failed to download {symbol} data for '3mo': {e}, retrying with '1mo'")
                return yf.download(symbol, period='1mo', interval='1d')
            else:
                # If the fallback fails, propagate the exception
                raise

    for symbol in symbols_to_search:
        # Fetch stock info
        stock_info = yf.Ticker(symbol)
        float_shares = stock_info.info.get('floatShares', 0)
        formatted_fl_share = format(float_shares, ",")


        # Fetch summary data
        summary_info = stock_info.info
            
        # Summary
        days_range = (f"{summary_info.get('dayLow'):,}", f"{summary_info.get('dayHigh'):,}")
        fifty_two_week_range = (f"{summary_info.get('fiftyTwoWeekLow'):,}", f"{summary_info.get('fiftyTwoWeekHigh'):,}")
        market_capital = f"{summary_info.get('marketCap'):,}" if summary_info.get('marketCap') else None
        avg_volume_3m = f"{summary_info.get('averageVolume'):,}" if summary_info.get('averageVolume') else None
        avg_volume_10d = f"{summary_info.get('averageVolume10days'):,}" if summary_info.get('averageVolume10days') else None

        # Share Statistics
        outstanding_share = f"{summary_info.get('sharesOutstanding'):,}" if summary_info.get('sharesOutstanding') else None
        float_shares = f"{summary_info.get('floatShares'):,}" if summary_info.get('floatShares') else None
        held_by_insiders = f"{summary_info.get('heldPercentInsiders') * 100:.2f}%" if summary_info.get('heldPercentInsiders') else None
        held_by_institutions = f"{summary_info.get('heldPercentInstitutions') * 100:.2f}%" if summary_info.get('heldPercentInstitutions') else None
        shares_short = f"{summary_info.get('sharesShort'):,}" if summary_info.get('sharesShort') else None
        shares_short_date = summary_info.get('dateShortInterest')  # Assuming this is already a date format, no commas needed
        short_percent_float = f"{summary_info.get('shortPercentOfFloat') * 100:.2f}%" if summary_info.get('shortPercentOfFloat') else None

        # Financials
        financials = stock_info.financials
        balance_sheet = stock_info.balance_sheet
        
        # Use .iloc to safely extract values by index position
        try:
            revenue = f"{financials.loc['Total Revenue'].iloc[0]:,}" if 'Total Revenue' in financials.index and financials.loc['Total Revenue'].iloc[0] else "N/A"
            net_income = f"{financials.loc['Net Income'].iloc[0]:,}" if 'Net Income' in financials.index and financials.loc['Net Income'].iloc[0] else "N/A"
            total_assets = f"{balance_sheet.loc['Total Assets'].iloc[0]:,}" if 'Total Assets' in balance_sheet.index and balance_sheet.loc['Total Assets'].iloc[0] else "N/A"
            total_liabilities = f"{balance_sheet.loc['Total Liabilities Net Minority Interest'].iloc[0]:,}" if 'Total Liabilities Net Minority Interest' in balance_sheet.index and balance_sheet.loc['Total Liabilities Net Minority Interest'].iloc[0] else "N/A"
            total_equity = f"{balance_sheet.loc['Total Stockholder Equity'].iloc[0]:,}" if 'Total Stockholder Equity' in balance_sheet.index and balance_sheet.loc['Total Stockholder Equity'].iloc[0] else "N/A"
        except (KeyError, IndexError, AttributeError) as e:
            # If an error occurs, set all financials to 'N/A'
            revenue = net_income = total_assets = total_liabilities = total_equity = "N/A"

        # Get the earnings date with error handling
        try:
            earnings_date = stock_info.calendar.loc['Earnings Date'].iloc[0] if 'Earnings Date' in stock_info.calendar.index else "N/A"
        except (IndexError, KeyError, AttributeError):
            earnings_date = "N/A"
            
        # Fetch historical stock splits
        splits = stock_info.splits

        if not splits.empty:
            # Get the most recent split
            last_split_date = splits.index[-1]
            last_split_ratio = splits.iloc[-1]

            # Convert the split ratio to a "1:x" format
            split_ratio_formatted = f"1:{int(1 / last_split_ratio)}" if last_split_ratio < 1 else f"{int(last_split_ratio)}:1"

            #print(f"Last Split Date: {last_split_date}")
            #print(f"Last Split Ratio: {split_ratio_formatted}")

        else:
            split_ratio_formatted = None
            last_split_date = None

        # Prepare data
        combined_sho_df['Date'] = pd.to_datetime(combined_sho_df['Date'])
        symbol_sho_data = combined_sho_df[combined_sho_df['Symbol'] == symbol]

        combined_data_df['Date'] = pd.to_datetime(combined_data_df['Date'])
        symbol_short_volume = combined_data_df[combined_data_df['Symbol'] == symbol]

        # Fetch historical stock data
        stock_data = safe_download(symbol)
        stock_data.reset_index(inplace=True)
        stock_data['Date'] = pd.to_datetime(stock_data['Date']).dt.tz_localize(None)  # Standardize time zone for Yahoo data
        stock_data = stock_data.merge(symbol_short_volume[['Date', 'ShortVolume']], on='Date', how='left').set_index('Date')

        # Calculate colors and bar widths for the plot
        colors = ['green' if close > open else 'red' for open, close in zip(stock_data['Open'], stock_data['Close'])]
        dates = pd.to_datetime(stock_data.index)
        if len(dates) > 1:
            # Calculate the median time difference between consecutive dates
            date_diffs = (dates[1:] - dates[:-1]).median()
            bar_width = date_diffs.total_seconds() * 1000 * 0.8  # Convert to milliseconds and set width to 80% of interval
        else:
            # Default bar width if there is not enough data
            bar_width = 86400000 * 0.8  # Default to 80% of a day (in milliseconds) if there's not enough data

        #date_diffs = (dates[1:] - dates[:-1]).median()
        #bar_width = date_diffs.total_seconds() * 1000 * 0.8  # Convert to milliseconds and set width to 80% of interval

        # Fetch news data for the period
        news_labels, news_hover_texts = check_news_each_day(symbol, dates)
        sec_links, form_types, sec_hover_texts = check_sec_filing_each_day(symbol, dates)
        # Fetch Sec data
        #count = "50"
        #cik = get_cik(symbol)
        #sec_df = fetch_sec_data(cik, count)

        # Check if df exists before running sec_labels
        
        #sec_labels = check_sec_filing_each_day(symbol, dates, sec_df)

        # Calculate daily price change 
        #stock_data['PriceChange'] = stock_data['Close'] - stock_data['Open']
        #price_change_text = [
        #f"{change:.2f}" for change in stock_data['PriceChange']
        #]
 


        # Add color for positive/negative change
        #price_change_color = ['green' if change > 0 else 'red' for change in stock_data['PriceChange']]

        # Add color for positive/negative change
        #price_change_color = ['green' if change > 0 else 'red' for change in stock_data['PriceChangePercent']]

        # Shift the 'Close' column by one day to get the previous day's close
        stock_data['PreviousClose'] = stock_data['Close'].shift(1)

        # Calculate the percentage change from previous close to current close
        stock_data['PriceChangePercent'] = ((stock_data['Close'] - stock_data['PreviousClose']) / stock_data['PreviousClose']) * 100

        # Format the text for annotations based on PriceChangePercent
        price_change_text = [
            f"{change:.2f}" if not pd.isna(change) else "" for change in stock_data['PriceChangePercent']
        ]

       # Calculate daily Open to High price change in %
        stock_data['OHPriceChangePercent'] = ((stock_data['High'] - stock_data['Open']) / stock_data['Open']) * 100
        O_H_price_change_text = [
        f"{change:.2f}" for change in stock_data['OHPriceChangePercent']
        ]

        # Calculate daily Previous close to High price change in %
        stock_data['PreCloseToHighPriceChangePercent'] = ((stock_data['High'] - stock_data['PreviousClose']) / stock_data['PreviousClose']) * 100
        Pre_C_H_price_change_text = [
        f"{change:.2f}" for change in stock_data['PreCloseToHighPriceChangePercent']
        ]


        # Add color for positive/negative change
        price_change_color = ['green' if change > 0 else 'red' for change in stock_data['PriceChangePercent'].fillna(0)]
        OH_price_change_color = ['green' if change > 0 else 'red' for change in stock_data['OHPriceChangePercent'].fillna(0)]
        PreCloseToHigh_price_change_color = ['green' if change > 0 else 'red' for change in stock_data['PreCloseToHighPriceChangePercent'].fillna(0)]
        
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
                f'<b><a href="{y_finance_url}" target="_blank">{symbol}</a> :</b> {stock_info.info.get("longName", "Name not found")}', 
                'Total Volume', 
                f'Short Volume | Float: {formatted_fl_share}'
            ),
            row_width=[0.15, 0.2, 0.65]
        )
        
        # Create the chart
        #fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.1,
                            #subplot_titles=(f'<b>{symbol} :</b> {stock_info.info.get("longName", "Name not found")}', 'Total Volume', f'Short Volume | Float:{formatted_fl_share}'),
                            #row_width=[0.15, 0.2, 0.65])
        #print(stock_data.index)
        # Add traces
        fig.add_trace(go.Candlestick(x=stock_data.index, open=stock_data['Open'], high=stock_data['High'], low=stock_data['Low'], close=stock_data['Close'], name='Candlestick'), row=1, col=1)
        #add annotations with a 90-degree rotation:
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
        #fig.add_trace(go.Bar(x=stock_data.index, y=stock_data['Volume'], name='Total Volume', marker_color='blue'), row=2, col=1)
        fig.add_trace(go.Bar(x=stock_data.index, y=[v if c == 'green' else 0 for v, c in zip(stock_data['Volume'], colors)], name='Total Volume Increase', marker_color='green', width=bar_width), row=2, col=1)
        #fig.add_trace(go.Bar(x=stock_data.index, y=[v if c == 'red' else 0 for v, c in zip(stock_data['Volume'], colors)], name='Total Volume Decrease', marker_color='red', width=bar_width), row=2, col=1)
        fig.add_trace(go.Bar(
        x=stock_data.index,
        y=[v if c == 'red' else 0 for v, c in zip(stock_data['Volume'], colors)],
        name='Total Volume Decrease',
        marker_color='red',
        text=sec_links,                
        textposition='outside',     # Inside the bar to move it downward
        textangle=90,              # Rotate text by 90 degrees
        hovertext=sec_hover_texts,       # Show FormDescription in hover
        insidetextanchor='start',  # Anchor text to the bottom of the bar
        width=bar_width
    ), row=2, col=1)
        fig.add_trace(go.Bar(x=stock_data.index, y=stock_data['ShortVolume'], name='Short Volume', marker_color='red',hovertext=news_hover_texts,text=news_labels,textposition='outside'), row=3, col=1)
        
        # Add vertical lines if dates info (Reg sho symbol) is found
        dates_info = check_symbol_dates(combined_sho_df, symbol)
        if dates_info:
            for key, date in dates_info.items():
                if date:  # Only add a line if the date is not None
                    date_ts = date.timestamp() * 1000
                    fig.add_vline(x=date_ts, line_width=2, line_dash="dash", line_color="blue", annotation_text=key, annotation_position="top right")

        # Additional customization here

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

        # Increase margin in the layout
        fig.update_layout(
            margin=dict(l=0, r=0, t=50, b=50),  # left, right, top, bottom margins
            xaxis_rangeslider_visible=False,
            title='',
            hovermode='x unified',
            height=600
        )
        fig.add_annotation(
            xref="paper", 
            yref="paper", 
            x=1.17, 
            y=0.75,  # Adjust these values for positioning
            text=(
                "<span style='font-size:14px;'><b>Summary</b></span><br>"
                "<span style='color:black;'><b>1D R: </b>" + str(days_range) + "</span><br>"
                "<span style='color:black;'><b>52W R: </b>" + str(fifty_two_week_range) + "</span><br>"
                "<span style='color:black;'><b>Market Cap: </b>" + str(market_capital) + "</span><br>"

                "<span style='color:black;'><b>Avg Vol (3M): </b>" + str(avg_volume_3m) + "</span><br>"
                "<span style='color:black;'><b>Avg Vol (10D): </b>" + str(avg_volume_10d) + "</span><br>"           
                f"<span style='color:black;'><b>Last Split Ratio: </b>{split_ratio_formatted}</span><br>"
                f"<span style='color:black;'><b>Date: </b>{last_split_date.strftime('%Y-%m-%d') if isinstance(last_split_date, datetime) else last_split_date}</span><br>"
                "<span style='color:black;'></span><br>"
                "<span style='font-size:14px;'><b>Share Stats.</b></span><br>"
                "<span style='color:black;'><b>Outst.: </b>" + str(outstanding_share) + "</span><br>"
                "<span style='color:black;'><b>Float: </b>" + str(float_shares) + "</span><br>"
                "<span style='color:black;'><b>Insiders: </b>" + str(held_by_insiders) + "</span><br>"
                "<span style='color:black;'><b>Instit. : </b>" + str(held_by_institutions) + "</span><br>"
                "<span style='color:black;'><b>Short: </b>" + str(shares_short) + "</span><br>"
                "<span style='color:black;'><b>Of Float: </b>" + str(short_percent_float) + "</span><br>"
                "<span style='color:black;'></span><br>"
                "<span style='font-size:14px;'><b>Financials</b></span><br>"
                "<span style='color:black;'><b>Revenue: </b>" + str(revenue) + "</span><br>"
                "<span style='color:black;'><b>Net Inc.: </b>" + str(net_income) + "</span><br>"
                "<span style='color:black;'><b>Assets: </b>" + str(total_assets) + "</span><br>"
                "<span style='color:black;'><b>Liabilities: </b>" + str(total_liabilities) + "</span><br>"
                "<span style='color:black;'><b>Equity: </b>" + str(total_equity) + "</span><br>"
                "<span style='color:black;'><b>Next Earning: </b>" + str(earnings_date) + "</span>"
            ),
            showarrow=False,
            font=dict(size=10),
            align="right"
        )
        # Add annotation for the stock split if available
        if not splits.empty:
            # Convert last split date to the appropriate timestamp format
            split_annotation_date = pd.to_datetime(last_split_date).date()  # Convert to date only
            dates_as_dates = dates.date  # Convert the DatetimeIndex to date format
        else:
            split_annotation_date = None
            dates_as_dates = dates.date
        #print(dates_as_dates)
        if split_annotation_date in dates_as_dates:
            # Add the annotation for stock split
            fig.add_annotation(
                x=split_annotation_date,
                y=stock_data['High'].max() * 1.05,  # Position the 'S' label slightly above the highest candlestick
                text='S',  # Text to display
                showarrow=False,
                font=dict(color='blue', size=12, family='Arial Black'),
                bgcolor='lightyellow',
                bordercolor='black',
                borderwidth=1,
                xanchor='center',
                yanchor='bottom'
            )





        # Convert plot to HTML and store in list
        fig_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
        charts_html.append(fig_html)

        # Combine symbols and charts into a single list of dictionaries
        charts_with_symbol = [
            {'symbol': symbol, 'chart_html': chart_html}
            for symbol, chart_html in zip(symbols_to_search, charts_html)
        ]
    
    return charts_with_symbol

def stock_charts_hist_today(symbols_to_search):

    symbols_to_search = symbols_to_search
    charts_html = []
    # Dates for querying data
    start_date = datetime.now()
    end_date = start_date - timedelta(days=90)
    # Generate datetime objects directly
    #dates = [start_date - timedelta(days=i) for i in range((start_date - end_date).days + 1)]

    def check_news_each_day(ticker, date_range):
        stock = yf.Ticker(ticker)
        news = stock.news
        news_links = []
        hover_texts = []  # To hold the news title for hover text

        for single_date in date_range:
            news_link = ""
            hover_text = ""
            for article in news:
                article_date = datetime.utcfromtimestamp(article['providerPublishTime']).date()
                if article_date == single_date.date():
                    # Link and title for hover text
                    news_link = f"<a href='{article['link']}' target='_blank'>N</a>"
                    hover_text = article['title']
                    break
            news_links.append(news_link or " ")
            hover_texts.append(hover_text or " ")
        return news_links, hover_texts


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
    
    # It will Check Reg show symbol dates
    def check_symbol_dates(df, symbol):
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

   

    # Fetch data from Django models
    combined_sho_data = ThreeMonthsRegSHO.objects.filter(Date__range=[end_date, start_date]).order_by('-Date')
    combined_data = ThreeMonthsShortVolume.objects.filter(Date__range=[end_date, start_date]).order_by('-Date')

    # Convert to DataFrame
    combined_sho_df = pd.DataFrame(list(combined_sho_data.values()))
    combined_data_df = pd.DataFrame(list(combined_data.values()))

    # Ensure Date columns are timezone-naive UTC
    combined_sho_df['Date'] = pd.to_datetime(combined_sho_df['Date']).dt.tz_localize(None)
    combined_data_df['Date'] = pd.to_datetime(combined_data_df['Date']).dt.tz_localize(None)
    # Prepare data
    combined_sho_df['Date'] = pd.to_datetime(combined_sho_df['Date'])
    
    # Download data for '3mo' and if it fails due to a Error, it will try for '1mo'.
    def safe_download(symbol, period='3mo'):
        try:
            # Try fetching the data for the default period (3 months)
            data = yf.download(symbol, period=period, interval='1d')
            if data.empty:
                raise ValueError(f"No data returned for {symbol} using period {period}")
            return data
        except ValueError as e:
            # If there is an error or empty data, fall back to '1mo'
            if period == '3mo':
                print(f"Failed to download {symbol} data for '3mo': {e}, retrying with '1mo'")
                return yf.download(symbol, period='1mo', interval='1d')
            else:
                # If the fallback fails, propagate the exception
                raise

    for symbol in symbols_to_search:
        # Fetch stock info
        stock_info = yf.Ticker(symbol)
        float_shares = stock_info.info.get('floatShares', 0)
        formatted_fl_share = format(float_shares, ",")


        # Fetch summary data
        summary_info = stock_info.info
            
        # Summary
        days_range = (f"{summary_info.get('dayLow'):,}", f"{summary_info.get('dayHigh'):,}")
        fifty_two_week_range = (f"{summary_info.get('fiftyTwoWeekLow'):,}", f"{summary_info.get('fiftyTwoWeekHigh'):,}")
        market_capital = f"{summary_info.get('marketCap'):,}" if summary_info.get('marketCap') else None
        avg_volume_3m = f"{summary_info.get('averageVolume'):,}" if summary_info.get('averageVolume') else None
        avg_volume_10d = f"{summary_info.get('averageVolume10days'):,}" if summary_info.get('averageVolume10days') else None

        # Share Statistics
        outstanding_share = f"{summary_info.get('sharesOutstanding'):,}" if summary_info.get('sharesOutstanding') else None
        float_shares = f"{summary_info.get('floatShares'):,}" if summary_info.get('floatShares') else None
        held_by_insiders = f"{summary_info.get('heldPercentInsiders') * 100:.2f}%" if summary_info.get('heldPercentInsiders') else None
        held_by_institutions = f"{summary_info.get('heldPercentInstitutions') * 100:.2f}%" if summary_info.get('heldPercentInstitutions') else None
        shares_short = f"{summary_info.get('sharesShort'):,}" if summary_info.get('sharesShort') else None
        shares_short_date = summary_info.get('dateShortInterest')  # Assuming this is already a date format, no commas needed
        short_percent_float = f"{summary_info.get('shortPercentOfFloat') * 100:.2f}%" if summary_info.get('shortPercentOfFloat') else None

        # Financials
        financials = stock_info.financials
        balance_sheet = stock_info.balance_sheet
        
        revenue = f"{financials.loc['Total Revenue'][0]:,}" if 'Total Revenue' in financials.index and financials.loc['Total Revenue'][0] else None
        net_income = f"{financials.loc['Net Income'][0]:,}" if 'Net Income' in financials.index and financials.loc['Net Income'][0] else None
        total_assets = f"{balance_sheet.loc['Total Assets'][0]:,}" if 'Total Assets' in balance_sheet.index and balance_sheet.loc['Total Assets'][0] else None
        total_liabilities = f"{balance_sheet.loc['Total Liabilities Net Minority Interest'][0]:,}" if 'Total Liabilities Net Minority Interest' in balance_sheet.index and balance_sheet.loc['Total Liabilities Net Minority Interest'][0] else None
        total_equity = f"{balance_sheet.loc['Total Stockholder Equity'][0]:,}" if 'Total Stockholder Equity' in balance_sheet.index and balance_sheet.loc['Total Stockholder Equity'][0] else None

        # Get the earnings date from the calendar data
        try:
            earnings_date = stock_info.calendar.loc['Earnings Date'][0]
        except (IndexError, KeyError, AttributeError):
            earnings_date = None  # If earnings date isn't available, set to None
        # Fetch historical stock splits
        splits = stock_info.splits

        if not splits.empty:
            # Get the most recent split
            last_split_date = splits.index[-1]
            last_split_ratio = splits.iloc[-1]

            # Convert the split ratio to a "1:x" format
            split_ratio_formatted = f"1:{int(1 / last_split_ratio)}" if last_split_ratio < 1 else f"{int(last_split_ratio)}:1"

            #print(f"Last Split Date: {last_split_date}")
            #print(f"Last Split Ratio: {split_ratio_formatted}")

        else:
            split_ratio_formatted = None
            last_split_date = None

        # Prepare data
        #combined_sho_df['Date'] = pd.to_datetime(combined_sho_df['Date'])
        #symbol_sho_data = combined_sho_df[combined_sho_df['Symbol'] == symbol]

        combined_data_df['Date'] = pd.to_datetime(combined_data_df['Date'])
        symbol_short_volume = combined_data_df[combined_data_df['Symbol'] == symbol]

        # Fetch historical stock data
        stock_data = safe_download(symbol)
        stock_data.reset_index(inplace=True)
        stock_data['Date'] = pd.to_datetime(stock_data['Date']).dt.tz_localize(None)  # Standardize time zone for Yahoo data
        stock_data = stock_data.merge(symbol_short_volume[['Date', 'ShortVolume']], on='Date', how='left').set_index('Date')

        # Calculate colors and bar widths for the plot
        colors = ['green' if close > open else 'red' for open, close in zip(stock_data['Open'], stock_data['Close'])]
        dates = pd.to_datetime(stock_data.index)
        if len(dates) > 1:
            # Calculate the median time difference between consecutive dates
            date_diffs = (dates[1:] - dates[:-1]).median()
            bar_width = date_diffs.total_seconds() * 1000 * 0.8  # Convert to milliseconds and set width to 80% of interval
        else:
            # Default bar width if there is not enough data
            bar_width = 86400000 * 0.8  # Default to 80% of a day (in milliseconds) if there's not enough data

        #date_diffs = (dates[1:] - dates[:-1]).median()
        #bar_width = date_diffs.total_seconds() * 1000 * 0.8  # Convert to milliseconds and set width to 80% of interval

        # Fetch news data for the period
        news_labels, news_hover_texts = check_news_each_day(symbol, dates)
        sec_links, form_types, sec_hover_texts = check_sec_filing_each_day(symbol, dates)
        # Fetch Sec data
        #count = "50"
        #cik = get_cik(symbol)
        #sec_df = fetch_sec_data(cik, count)

        # Check if df exists before running sec_labels
        
        #sec_labels = check_sec_filing_each_day(symbol, dates, sec_df)

        # Shift the 'Close' column by one day to get the previous day's close
        stock_data['PreviousClose'] = stock_data['Close'].shift(1)

        # Calculate the percentage change from previous close to current close
        stock_data['PriceChangePercent'] = ((stock_data['Close'] - stock_data['PreviousClose']) / stock_data['PreviousClose']) * 100

        # Format the text for annotations based on PriceChangePercent
        price_change_text = [
            f"{change:.2f}" if not pd.isna(change) else "" for change in stock_data['PriceChangePercent']
        ]

       # Calculate daily Open to High price change in %
        stock_data['OHPriceChangePercent'] = ((stock_data['High'] - stock_data['Open']) / stock_data['Open']) * 100
        O_H_price_change_text = [
        f"{change:.2f}" for change in stock_data['OHPriceChangePercent']
        ]

        # Calculate daily Previous close to High price change in %
        stock_data['PreCloseToHighPriceChangePercent'] = ((stock_data['High'] - stock_data['PreviousClose']) / stock_data['PreviousClose']) * 100
        Pre_C_H_price_change_text = [
        f"{change:.2f}" for change in stock_data['PreCloseToHighPriceChangePercent']
        ]


        # Add color for positive/negative change
        price_change_color = ['green' if change > 0 else 'red' for change in stock_data['PriceChangePercent'].fillna(0)]
        OH_price_change_color = ['green' if change > 0 else 'red' for change in stock_data['OHPriceChangePercent'].fillna(0)]
        PreCloseToHigh_price_change_color = ['green' if change > 0 else 'red' for change in stock_data['PreCloseToHighPriceChangePercent'].fillna(0)]
        
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
                f'<b><a href="{y_finance_url}" target="_blank">{symbol}</a> :</b> {stock_info.info.get("longName", "Name not found")}', 
                'Total Volume', 
                f'Short Volume | Float: {formatted_fl_share}'
            ),
            row_width=[0.15, 0.2, 0.65]
        )
        
        #print(stock_data.index)
        # Add traces
       
        # Separate today's date from the rest of the data
        today = datetime.now().date()
        historical_data = stock_data[stock_data.index.date < today]
        today_data = stock_data[stock_data.index.date == today]

        # Plot historical data (cached)
        fig.add_trace(go.Candlestick(
            x=historical_data.index,
            open=historical_data['Open'],
            high=historical_data['High'],
            low=historical_data['Low'],
            close=historical_data['Close'],
            name='Candlestick',
            showlegend=True  # Keep in the legend
        ), row=1, col=1)

        for i, (index, row) in enumerate(historical_data.iterrows()):
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

        fig.add_trace(go.Bar(
            x=historical_data.index,
            y=[v if c == 'green' else 0 for v, c in zip(historical_data['Volume'], colors)],
            name='Total Volume Increase',
            showlegend=True,  # Keep in the legend
            marker_color='green',
            width=bar_width
        ), row=2, col=1)

        fig.add_trace(go.Bar(
            x=historical_data.index,
            y=[v if c == 'red' else 0 for v, c in zip(historical_data['Volume'], colors)],
            name='Total Volume Decrease',
            showlegend=True,  # Keep in the legend
            marker_color='red',
            text=sec_links,
            textposition='outside',
            textangle=90,
            hovertext=sec_hover_texts,
            insidetextanchor='start',
            width=bar_width
        ), row=2, col=1)

        fig.add_trace(go.Bar(
            x=historical_data.index,
            y=historical_data['ShortVolume'],
            name='Short Volume',
            showlegend=True,  # Keep in the legend
            marker_color='red',
            hovertext=news_hover_texts,
            text=news_labels,
            textposition='outside'
        ), row=3, col=1)

        # Plot today's data separately without caching
        fig.add_trace(go.Candlestick(
            x=today_data.index,
            open=today_data['Open'],
            high=today_data['High'],
            low=today_data['Low'],
            close=today_data['Close'],
            showlegend=False  # Hide from the legend
            #name='Candlestick'
        ), row=1, col=1)

        for i, (index, row) in enumerate(today_data.iterrows()):
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

        fig.add_trace(go.Bar(
            x=today_data.index,
            y=[v if c == 'green' else 0 for v, c in zip(today_data['Volume'], colors)],
            #name='Total Volume Increase',
            marker_color='green',
            showlegend=False,  # Hide from the legend
            width=bar_width
        ), row=2, col=1)

        fig.add_trace(go.Bar(
            x=today_data.index,
            y=[v if c == 'red' else 0 for v, c in zip(today_data['Volume'], colors)],
            #name='Total Volume Decrease',
            showlegend=False,  # Hide from the legend
            marker_color='red',
            text=sec_links,
            textposition='outside',
            textangle=90,
            hovertext=sec_hover_texts,
            insidetextanchor='start',
            width=bar_width
        ), row=2, col=1)

        fig.add_trace(go.Bar(
            x=today_data.index,
            y=today_data['ShortVolume'],
            #name='Short Volume',
            showlegend=False,  # Hide from the legend
            marker_color='red',
            hovertext=news_hover_texts,
            text=news_labels,
            textposition='outside'
        ), row=3, col=1)        
        # Add vertical lines if dates info (Reg sho symbol) is found
        dates_info = check_symbol_dates(combined_sho_df, symbol)
        if dates_info:
            for key, date in dates_info.items():
                if date:  # Only add a line if the date is not None
                    date_ts = date.timestamp() * 1000
                    fig.add_vline(x=date_ts, line_width=2, line_dash="dash", line_color="blue", annotation_text=key, annotation_position="top right")

        # Additional customization here

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

        # Increase margin in the layout
        fig.update_layout(
            margin=dict(l=0, r=0, t=50, b=50),  # left, right, top, bottom margins
            xaxis_rangeslider_visible=False,
            title='',
            hovermode='x unified',
            height=600
        )
        fig.add_annotation(
            xref="paper", 
            yref="paper", 
            x=1.16, 
            y=0.75,  # Adjust these values for positioning
            text=(
                "<span style='font-size:14px;'><b>Summary</b></span><br>"
                "<span style='color:black;'><b>1D R: </b>" + str(days_range) + "</span><br>"
                "<span style='color:black;'><b>52W R: </b>" + str(fifty_two_week_range) + "</span><br>"
                "<span style='color:black;'><b>Market Cap: </b>" + str(market_capital) + "</span><br>"

                "<span style='color:black;'><b>Avg Vol (3M): </b>" + str(avg_volume_3m) + "</span><br>"
                "<span style='color:black;'><b>Avg Vol (10D): </b>" + str(avg_volume_10d) + "</span><br>"           
                f"<span style='color:black;'><b>Last Split Ratio: </b>{split_ratio_formatted}</span><br>"
                f"<span style='color:black;'><b>Date: </b>{last_split_date.strftime('%Y-%m-%d') if isinstance(last_split_date, datetime) else last_split_date}</span><br>"
                "<span style='color:black;'></span><br>"
                "<span style='font-size:14px;'><b>Share Stats.</b></span><br>"
                "<span style='color:black;'><b>Outst.: </b>" + str(outstanding_share) + "</span><br>"
                "<span style='color:black;'><b>Float: </b>" + str(float_shares) + "</span><br>"
                "<span style='color:black;'><b>Insiders: </b>" + str(held_by_insiders) + "</span><br>"
                "<span style='color:black;'><b>Instit. : </b>" + str(held_by_institutions) + "</span><br>"
                "<span style='color:black;'><b>Short: </b>" + str(shares_short) + "</span><br>"
                "<span style='color:black;'><b>Of Float: </b>" + str(short_percent_float) + "</span><br>"
                "<span style='color:black;'></span><br>"
                "<span style='font-size:14px;'><b>Financials</b></span><br>"
                "<span style='color:black;'><b>Revenue: </b>" + str(revenue) + "</span><br>"
                "<span style='color:black;'><b>Net Inc.: </b>" + str(net_income) + "</span><br>"
                "<span style='color:black;'><b>Assets: </b>" + str(total_assets) + "</span><br>"
                "<span style='color:black;'><b>Liabilities: </b>" + str(total_liabilities) + "</span><br>"
                "<span style='color:black;'><b>Equity: </b>" + str(total_equity) + "</span><br>"
                "<span style='color:black;'><b>Next Earning: </b>" + str(earnings_date) + "</span>"
            ),
            showarrow=False,
            font=dict(size=10),
            align="right"
        )
        # Add annotation for the stock split if available
        if not splits.empty:
            # Convert last split date to the appropriate timestamp format
            split_annotation_date = pd.to_datetime(last_split_date).date()  # Convert to date only
            dates_as_dates = dates.date  # Convert the DatetimeIndex to date format
        else:
            split_annotation_date = None
            dates_as_dates = dates.date
        #print(dates_as_dates)
        if split_annotation_date in dates_as_dates:
            # Add the annotation for stock split
            fig.add_annotation(
                x=split_annotation_date,
                y=stock_data['High'].max() * 1.05,  # Position the 'S' label slightly above the highest candlestick
                text='S',  # Text to display
                showarrow=False,
                font=dict(color='blue', size=12, family='Arial Black'),
                bgcolor='lightyellow',
                bordercolor='black',
                borderwidth=1,
                xanchor='center',
                yanchor='bottom'
            )





        # Convert plot to HTML and store in list
        fig_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
        charts_html.append(fig_html)

        # Combine symbols and charts into a single list of dictionaries
        charts_with_symbol = [
            {'symbol': symbol, 'chart_html': chart_html}
            for symbol, chart_html in zip(symbols_to_search, charts_html)
        ]
    
    return charts_with_symbol, historical_data, today_data

def single_stock_charts(symbol):

    #symbols_to_search = symbols_to_search
    
    # Dates for querying data
    start_date = datetime.now()
    end_date = start_date - timedelta(days=90)
    # Generate datetime objects directly
    #dates = [start_date - timedelta(days=i) for i in range((start_date - end_date).days + 1)]

    def check_news_each_day(ticker, date_range):
        stock = yf.Ticker(ticker)
        news = stock.news
        news_links = []
        hover_texts = []  # To hold the news title for hover text

        for single_date in date_range:
            news_link = ""
            hover_text = ""
            for article in news:
                article_date = datetime.utcfromtimestamp(article['providerPublishTime']).date()
                if article_date == single_date.date():
                    # Link and title for hover text
                    news_link = f"<a href='{article['link']}' target='_blank'>N</a>"
                    hover_text = article['title']
                    break
            news_links.append(news_link or " ")
            hover_texts.append(hover_text or " ")
        return news_links, hover_texts


    def check_sec_filing_each_day(symbol, date_range):
        sec_links = []
        form_types = []  # To hold FormType for text display on top of the bars
        hover_texts = []  # To hold FormDescription for hover text display

        # Construct the file path within the function
        file_path = os.path.join(settings.BASE_DIR, "data", "sec_data_symbols.json")   
        # Print the file path to see where Django is looking (optional)
        print(f"Looking for file at: {file_path}")
        
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
    
    # It will Check Reg show symbol dates
    def check_symbol_dates(df, symbol):
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

   

    # Fetch data from Django models
    combined_sho_data = ThreeMonthsRegSHO.objects.filter(Date__range=[end_date, start_date]).order_by('-Date')
    combined_data = ThreeMonthsShortVolume.objects.filter(Date__range=[end_date, start_date]).order_by('-Date')

    # Convert to DataFrame
    combined_sho_df = pd.DataFrame(list(combined_sho_data.values()))
    combined_data_df = pd.DataFrame(list(combined_data.values()))

    # Ensure Date columns are timezone-naive UTC
    combined_sho_df['Date'] = pd.to_datetime(combined_sho_df['Date']).dt.tz_localize(None)
    combined_data_df['Date'] = pd.to_datetime(combined_data_df['Date']).dt.tz_localize(None)

    # Download data for '3mo' and if it fails due to a Error, it will try for '1mo'.
    def safe_download(symbol, period='3mo'):
        try:
            # Try fetching the data for the default period (3 months)
            data = yf.download(symbol, period=period, interval='1d')
            if data.empty:
                raise ValueError(f"No data returned for {symbol} using period {period}")
            return data
        except ValueError as e:
            # If there is an error or empty data, fall back to '1mo'
            if period == '3mo':
                print(f"Failed to download {symbol} data for '3mo': {e}, retrying with '1mo'")
                return yf.download(symbol, period='1mo', interval='1d')
            else:
                # If the fallback fails, propagate the exception
                raise

    #for symbol in symbols_to_search:
    # Fetch stock info
    # Ensure the symbol is a string
    if isinstance(symbol, list):
        # If it's a list, take the first item or join the list into a single string
        symbol = symbol[0] if len(symbol) == 1 else ','.join(symbol)

    stock_info = yf.Ticker(symbol)
    float_shares = stock_info.info.get('floatShares', 0)
    formatted_fl_share = format(float_shares, ",")


    # Fetch summary data
    summary_info = stock_info.info
        
    # Summary
    days_range = (f"{summary_info.get('dayLow'):,}", f"{summary_info.get('dayHigh'):,}")
    fifty_two_week_range = (f"{summary_info.get('fiftyTwoWeekLow'):,}", f"{summary_info.get('fiftyTwoWeekHigh'):,}")
    market_capital = f"{summary_info.get('marketCap'):,}" if summary_info.get('marketCap') else None
    avg_volume_3m = f"{summary_info.get('averageVolume'):,}" if summary_info.get('averageVolume') else None
    avg_volume_10d = f"{summary_info.get('averageVolume10days'):,}" if summary_info.get('averageVolume10days') else None

    # Share Statistics
    outstanding_share = f"{summary_info.get('sharesOutstanding'):,}" if summary_info.get('sharesOutstanding') else None
    float_shares = f"{summary_info.get('floatShares'):,}" if summary_info.get('floatShares') else None
    held_by_insiders = f"{summary_info.get('heldPercentInsiders') * 100:.2f}%" if summary_info.get('heldPercentInsiders') else None
    held_by_institutions = f"{summary_info.get('heldPercentInstitutions') * 100:.2f}%" if summary_info.get('heldPercentInstitutions') else None
    shares_short = f"{summary_info.get('sharesShort'):,}" if summary_info.get('sharesShort') else None
    shares_short_date = summary_info.get('dateShortInterest')  # Assuming this is already a date format, no commas needed
    short_percent_float = f"{summary_info.get('shortPercentOfFloat') * 100:.2f}%" if summary_info.get('shortPercentOfFloat') else None

    # Financials
    financials = stock_info.financials
    balance_sheet = stock_info.balance_sheet
    
    revenue = f"{financials.loc['Total Revenue'][0]:,}" if 'Total Revenue' in financials.index and financials.loc['Total Revenue'][0] else None
    net_income = f"{financials.loc['Net Income'][0]:,}" if 'Net Income' in financials.index and financials.loc['Net Income'][0] else None
    total_assets = f"{balance_sheet.loc['Total Assets'][0]:,}" if 'Total Assets' in balance_sheet.index and balance_sheet.loc['Total Assets'][0] else None
    total_liabilities = f"{balance_sheet.loc['Total Liabilities Net Minority Interest'][0]:,}" if 'Total Liabilities Net Minority Interest' in balance_sheet.index and balance_sheet.loc['Total Liabilities Net Minority Interest'][0] else None
    total_equity = f"{balance_sheet.loc['Total Stockholder Equity'][0]:,}" if 'Total Stockholder Equity' in balance_sheet.index and balance_sheet.loc['Total Stockholder Equity'][0] else None

    # Get the earnings date from the calendar data
    try:
        earnings_date = stock_info.calendar.loc['Earnings Date'][0]
    except (IndexError, KeyError, AttributeError):
        earnings_date = None  # If earnings date isn't available, set to None
    # Fetch historical stock splits
    splits = stock_info.splits

    if not splits.empty:
        # Get the most recent split
        last_split_date = splits.index[-1]
        last_split_ratio = splits.iloc[-1]

        # Convert the split ratio to a "1:x" format
        split_ratio_formatted = f"1:{int(1 / last_split_ratio)}" if last_split_ratio < 1 else f"{int(last_split_ratio)}:1"

        #print(f"Last Split Date: {last_split_date}")
        #print(f"Last Split Ratio: {split_ratio_formatted}")

    else:
        split_ratio_formatted = None
        last_split_date = None

    # Prepare data
    combined_sho_df['Date'] = pd.to_datetime(combined_sho_df['Date'])
    symbol_sho_data = combined_sho_df[combined_sho_df['Symbol'] == symbol]

    combined_data_df['Date'] = pd.to_datetime(combined_data_df['Date'])
    symbol_short_volume = combined_data_df[combined_data_df['Symbol'] == symbol]

    # Fetch historical stock data
    stock_data = safe_download(symbol)
    stock_data.reset_index(inplace=True)
    stock_data['Date'] = pd.to_datetime(stock_data['Date']).dt.tz_localize(None)  # Standardize time zone for Yahoo data
    stock_data = stock_data.merge(symbol_short_volume[['Date', 'ShortVolume']], on='Date', how='left').set_index('Date')

    # Calculate colors and bar widths for the plot
    colors = ['green' if close > open else 'red' for open, close in zip(stock_data['Open'], stock_data['Close'])]
    dates = pd.to_datetime(stock_data.index)
    if len(dates) > 1:
        # Calculate the median time difference between consecutive dates
        date_diffs = (dates[1:] - dates[:-1]).median()
        bar_width = date_diffs.total_seconds() * 1000 * 0.8  # Convert to milliseconds and set width to 80% of interval
    else:
        # Default bar width if there is not enough data
        bar_width = 86400000 * 0.8  # Default to 80% of a day (in milliseconds) if there's not enough data

    #date_diffs = (dates[1:] - dates[:-1]).median()
    #bar_width = date_diffs.total_seconds() * 1000 * 0.8  # Convert to milliseconds and set width to 80% of interval

    # Fetch news data for the period
    news_labels, news_hover_texts = check_news_each_day(symbol, dates)
    sec_links, form_types, sec_hover_texts = check_sec_filing_each_day(symbol, dates)


    # Calculate daily price change 
    stock_data['PriceChange'] = stock_data['Close'] - stock_data['Open']
    #price_change_text = [
    #f"{change:.2f}" for change in stock_data['PriceChange']
    #]
    # Calculate daily price change in %
    stock_data['PriceChangePercent'] = ((stock_data['Close'] - stock_data['Open']) / stock_data['Open']) * 100
    price_change_text = [
    f"{change:.2f}" for change in stock_data['PriceChangePercent']
    ]


    # Add color for positive/negative change
    price_change_color = ['green' if change > 0 else 'red' for change in stock_data['PriceChangePercent']]

    # Create the chart
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.1,
                        subplot_titles=(f'<b>{symbol} :</b> {stock_info.info.get("longName", "Name not found")}', 'Total Volume', f'Short Volume | Float:{formatted_fl_share}'),
                        row_width=[0.15, 0.2, 0.65])

    # Add traces
    fig.add_trace(go.Candlestick(x=stock_data.index, open=stock_data['Open'], high=stock_data['High'], low=stock_data['Low'], close=stock_data['Close'], name='Candlestick'), row=1, col=1)
    #add annotations with a 90-degree rotation:
    for i, (index, row) in enumerate(stock_data.iterrows()):
        fig.add_annotation(
            x=index,
            #y=row['High']* 1.2,  # Position slightly above the candlestick high
            text=f"{price_change_text[i]}",
            showarrow=False,
            font=dict(color=price_change_color[i], size=12),
            #hovertext=f"Price Change: {price_change_text[i]}%", 
            hovertext=(
                f"<span style='color:{price_change_color[i]};'>"
                f"Price Change: {price_change_text[i]}%</span>"
            ),
            textangle=90,              # Rotate text by 90 degrees
            
            
        )
    #fig.add_trace(go.Bar(x=stock_data.index, y=stock_data['Volume'], name='Total Volume', marker_color='blue'), row=2, col=1)
    fig.add_trace(go.Bar(x=stock_data.index, y=[v if c == 'green' else 0 for v, c in zip(stock_data['Volume'], colors)], name='Total Volume Increase', marker_color='green', width=bar_width), row=2, col=1)
    #fig.add_trace(go.Bar(x=stock_data.index, y=[v if c == 'red' else 0 for v, c in zip(stock_data['Volume'], colors)], name='Total Volume Decrease', marker_color='red', width=bar_width), row=2, col=1)
    fig.add_trace(go.Bar(
    x=stock_data.index,
    y=[v if c == 'red' else 0 for v, c in zip(stock_data['Volume'], colors)],
    name='Total Volume Decrease',
    marker_color='red',
    text=sec_links,                
    textposition='outside',     # Inside the bar to move it downward
    textangle=90,              # Rotate text by 90 degrees
    hovertext=sec_hover_texts,       # Show FormDescription in hover
    insidetextanchor='start',  # Anchor text to the bottom of the bar
    width=bar_width
), row=2, col=1)
    fig.add_trace(go.Bar(x=stock_data.index, y=stock_data['ShortVolume'], name='Short Volume', marker_color='red',hovertext=news_hover_texts,text=news_labels,textposition='outside'), row=3, col=1)
    
    # Add vertical lines if dates info (Reg sho symbol) is found
    dates_info = check_symbol_dates(combined_sho_df, symbol)
    if dates_info:
        for key, date in dates_info.items():
            if date:  # Only add a line if the date is not None
                date_ts = date.timestamp() * 1000
                fig.add_vline(x=date_ts, line_width=2, line_dash="dash", line_color="blue", annotation_text=key, annotation_position="top right")

    # Additional customization here

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

    # Increase margin in the layout
    fig.update_layout(
        margin=dict(l=0, r=0, t=50, b=50),  # left, right, top, bottom margins
        xaxis_rangeslider_visible=False,
        title='',
        hovermode='x unified',
        height=600
    )
    fig.add_annotation(
        xref="paper", 
        yref="paper", 
        x=1.17, 
        y=0.75,  # Adjust these values for positioning
        text=(
            "<span style='font-size:14px;'><b>Summary</b></span><br>"
            "<span style='color:black;'><b>1D R: </b>" + str(days_range) + "</span><br>"
            "<span style='color:black;'><b>52W R: </b>" + str(fifty_two_week_range) + "</span><br>"
            "<span style='color:black;'><b>Market Cap: </b>" + str(market_capital) + "</span><br>"

            "<span style='color:black;'><b>Avg Vol (3M): </b>" + str(avg_volume_3m) + "</span><br>"
            "<span style='color:black;'><b>Avg Vol (10D): </b>" + str(avg_volume_10d) + "</span><br>"           
            f"<span style='color:black;'><b>Last Split Ratio: </b>{split_ratio_formatted}</span><br>"
            f"<span style='color:black;'><b>Date: </b>{last_split_date.strftime('%Y-%m-%d') if isinstance(last_split_date, datetime) else last_split_date}</span><br>"
            "<span style='color:black;'></span><br>"
            "<span style='font-size:14px;'><b>Share Stats.</b></span><br>"
            "<span style='color:black;'><b>Outst.: </b>" + str(outstanding_share) + "</span><br>"
            "<span style='color:black;'><b>Float: </b>" + str(float_shares) + "</span><br>"
            "<span style='color:black;'><b>Insiders: </b>" + str(held_by_insiders) + "</span><br>"
            "<span style='color:black;'><b>Instit. : </b>" + str(held_by_institutions) + "</span><br>"
            "<span style='color:black;'><b>Short: </b>" + str(shares_short) + "</span><br>"
            "<span style='color:black;'><b>Of Float: </b>" + str(short_percent_float) + "</span><br>"
            "<span style='color:black;'></span><br>"
            "<span style='font-size:14px;'><b>Financials</b></span><br>"
            "<span style='color:black;'><b>Revenue: </b>" + str(revenue) + "</span><br>"
            "<span style='color:black;'><b>Net Inc.: </b>" + str(net_income) + "</span><br>"
            "<span style='color:black;'><b>Assets: </b>" + str(total_assets) + "</span><br>"
            "<span style='color:black;'><b>Liabilities: </b>" + str(total_liabilities) + "</span><br>"
            "<span style='color:black;'><b>Equity: </b>" + str(total_equity) + "</span><br>"
            "<span style='color:black;'><b>Next Earning: </b>" + str(earnings_date) + "</span>"
        ),
        showarrow=False,
        font=dict(size=10),
        align="right"
    )
    # Add annotation for the stock split if available
    if not splits.empty:
        # Convert last split date to the appropriate timestamp format
        split_annotation_date = pd.to_datetime(last_split_date).date()  # Convert to date only
        dates_as_dates = dates.date  # Convert the DatetimeIndex to date format
    else:
        split_annotation_date = None
        dates_as_dates = dates.date
    #print(dates_as_dates)
    if split_annotation_date in dates_as_dates:
        # Add the annotation for stock split
        fig.add_annotation(
            x=split_annotation_date,
            y=stock_data['High'].max() * 1.05,  # Position the 'S' label slightly above the highest candlestick
            text='S',  # Text to display
            showarrow=False,
            font=dict(color='blue', size=12, family='Arial Black'),
            bgcolor='lightyellow',
            bordercolor='black',
            borderwidth=1,
            xanchor='center',
            yanchor='bottom'
        )


    
    charts_html=[]

    # Convert plot to HTML and store in list
    fig_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
    charts_html.append(fig_html)

    # Combine symbols and charts into a single list of dictionaries
    charts_with_symbol = [
        {'symbol': symbol, 'chart_html': chart_html}
        for symbol, chart_html in zip(symbol, charts_html)
    ]
    
    return charts_with_symbol



