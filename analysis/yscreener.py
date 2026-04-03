import requests
from bs4 import BeautifulSoup
import pandas as pd
from django.http import JsonResponse

def y_most_active():
    # Yahoo Finance URL for most active stocks
    url = "https://finance.yahoo.com/markets/stocks/most-active/"

    # Request the page content
    headers = {'User-Agent': 'Mozilla/5.0'}
    if url:
        response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    # Find the table and parse rows
    table = soup.find("table")
    rows = table.find_all("tr")[1:]  # Skip header row

    # Extract ticker, name, and volume
    data = []
    for row in rows[:10]:  # Limit to top 30
        columns = row.find_all("td")
        if len(columns) > 6:  # Ensure there are enough columns
            ticker = columns[0].text.strip()
            name = columns[1].text.strip()
            volume = columns[6].text.strip()
            data.append({"Ticker": ticker, "Name": name, "Volume": volume})

    # Convert to DataFrame
    df = pd.DataFrame(data)
    tickers_list = df['Ticker'].tolist()
    #print(tickers_list)
    return tickers_list

def y_tranding():
    # Yahoo Finance URL for most active stocks
    url = "https://finance.yahoo.com/markets/stocks/trending/"

    # Request the page content
    headers = {'User-Agent': 'Mozilla/5.0'}
    if url:
        response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    # Find the table and parse rows
    table = soup.find("table")
    rows = table.find_all("tr")[1:]  # Skip header row

    # Extract ticker, name, and volume
    data = []
    for row in rows[:10]:  # Limit to top 30
        columns = row.find_all("td")
        if len(columns) > 6:  # Ensure there are enough columns
            ticker = columns[0].text.strip()
            name = columns[1].text.strip()
            volume = columns[6].text.strip()
            data.append({"Ticker": ticker, "Name": name, "Volume": volume})

    # Convert to DataFrame
    df = pd.DataFrame(data)
    tickers_list = df['Ticker'].tolist()
    #print(tickers_list)
    return tickers_list

def y_top_gainers():
    # Yahoo Finance URL for most active stocks
    url = "https://finance.yahoo.com/markets/stocks/gainers/"

    # Request the page content
    headers = {'User-Agent': 'Mozilla/5.0'}
    if url:
        response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    # Find the table and parse rows
    table = soup.find("table")
    rows = table.find_all("tr")[1:]  # Skip header row

    # Extract ticker, name, and volume
    data = []
    for row in rows[:10]:  # Limit to top 30
        columns = row.find_all("td")
        if len(columns) > 6:  # Ensure there are enough columns
            ticker = columns[0].text.strip()
            name = columns[1].text.strip()
            volume = columns[6].text.strip()
            data.append({"Ticker": ticker, "Name": name, "Volume": volume})

    # Convert to DataFrame
    df = pd.DataFrame(data)
    tickers_list = df['Ticker'].tolist()
    #print(tickers_list)
    return tickers_list

def y_top_losers():
    # Yahoo Finance URL for most active stocks
    url = "https://finance.yahoo.com/markets/stocks/losers/"

    # Request the page content
    headers = {'User-Agent': 'Mozilla/5.0'}
    if url:
        response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    # Find the table and parse rows
    table = soup.find("table")
    rows = table.find_all("tr")[1:]  # Skip header row

    # Extract ticker, name, and volume
    data = []
    for row in rows[:10]:  # Limit to top 30
        columns = row.find_all("td")
        if len(columns) > 6:  # Ensure there are enough columns
            ticker = columns[0].text.strip()
            name = columns[1].text.strip()
            volume = columns[6].text.strip()
            data.append({"Ticker": ticker, "Name": name, "Volume": volume})

    # Convert to DataFrame
    df = pd.DataFrame(data)
    tickers_list = df['Ticker'].tolist()
    #print(tickers_list)
    return tickers_list