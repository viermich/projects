#!/usr/bin/env python
# coding: utf-8

# In[25]:


# import modules

import requests
import pandas as pd

# create request header

headers = {'User-Agent': "mvierela@seattleu.edu"}

# get data of all companies

companyTickers = requests.get("https://www.sec.gov/files/company_tickers.json", headers = headers)

# create dataframe with pandas

companyCIK = pd.DataFrame.from_dict(companyTickers.json(), orient = 'index')

# add leading series to create 10 digit CIK

companyCIK['cik_str'] = companyCIK['cik_str'].astype(str).str.zfill(10)

print(companyCIK)

cik = companyCIK[0:1].cik_str[0]

print(cik)

# SEC filing API

# https://data.sec.gov/submissions/CIK##########.json

# SEC filing API call

companyFiling = requests.get(f"https://data.sec.gov/submissions/CIK{cik}.json", headers = headers)

print(companyFiling.json()['filings'].keys())

allFilings = pd.DataFrame.from_dict(companyFiling.json()['filings']['files'])

print(allFilings)

# pull historic data from sec archive

companyFiling_archive = requests.get(f"https://data.sec.gov/submissions/{allFilings['name'][0]}", headers = headers)

# turn the sec archive response into a dataframe

allFilings_archive_df = pd.DataFrame.from_dict(companyFiling_archive.json())

print(allFilings_archive_df)

# pull all the unique filing types

uniqueFiling_types = allFilings_archive_df['form'].unique()

print(uniqueFiling_types)

# filter only 10Q forms

form_10Q_filings = allFilings_archive_df[allFilings_archive_df['form'] == '10-Q']

print(form_10Q_filings)

###########################
# pull the stock market price based on the filing date

import yfinance as yf
from datetime import datetime, timedelta

# create function to pull stock prices for different time frames

def get_stock_prices(ticker_symbol, start_date_str, end_date_str):
    ticker = yf.Ticker(ticker_symbol)
    historical_data = ticker.history(period='1d', start=start_date_str, end=end_date_str)
    return historical_data.iloc[0]['Close']


# create empty column to create stock price and stock prices before and after the filing date

form_10Q_filings['stock_price'] = 0
form_10Q_filings['stock_price_before'] = 0
form_10Q_filings['stock_price_after'] = 0


for index, row in form_10Q_filings.iterrows():
    value = row['filingDate']
    
    # we need a ticker symbol for the stock we want to pull
    
    ticker_symbol = 'AAPL' #companyCIK['ticker'][0]
    
    # start date for the api call
    
    start_date_str = value
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    
    # calculate the delta
    
    end_date = start_date + timedelta(days = 30)
    
    # convert end date to str
    
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    # create a y finance ticker object
    
    ticker = yf.Ticker(ticker_symbol)
    
    # pull yfinance historical data
    
    historical_data = ticker.history(period = '1d', start = start_date_str, end = end_date_str)
    
    historical_df = pd.DataFrame(historical_data)
    
    specific_data = historical_data.iloc[0]['Close']
    
    form_10Q_filings.at[index, 'stock_price'] = specific_data
    
    # calculate one week before and after filing date
    
    start_date_before = (datetime.strptime(value, '%Y-%m-%d') - timedelta(days = 7)).strftime('%Y-%m-%d')
    end_date_before = value
    
    start_date_after = value 
    end_date_after = (datetime.strptime(value, '%Y-%m-%d') + timedelta(days=7)).strftime('%Y-%m-%d')
    
    # pull stock prices one week before and after
    
    stock_price_before = get_stock_prices(ticker_symbol, start_date_before, end_date_before)
    stock_price_after = get_stock_prices(ticker_symbol, start_date_after, end_date_after)
    
    # put before and after stock prices into the dataframe
    
    form_10Q_filings.at[index, 'stock_price_before'] = stock_price_before
    form_10Q_filings.at[index, 'stock_price_after'] = stock_price_after
    
    
    #print(specific_data)
    

# filter dataframe from two years prior to the most recent filing date

form_10Q_filings['filingDate'] = pd.to_datetime(form_10Q_filings['filingDate'])
form_10Q_2yr_filings = form_10Q_filings[form_10Q_filings['filingDate'] >= form_10Q_filings['filingDate'].max() - pd.DateOffset(years=2)]
 
print(form_10Q_2yr_filings)

# plot each type of stock price

import matplotlib.pyplot as plt

plt.plot(form_10Q_2yr_filings['filingDate'], form_10Q_2yr_filings['stock_price_before'], color='red', label='Before Filing Date')
plt.plot(form_10Q_2yr_filings['filingDate'], form_10Q_2yr_filings['stock_price'], color='blue', label='Filing Date')
plt.plot(form_10Q_2yr_filings['filingDate'], form_10Q_2yr_filings['stock_price_after'], color='green', label='After Filing Date')
plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%m/%y'))
plt.xlabel('Filing Date')
plt.ylabel('Stock Price')
plt.title(f'Stock Price vs Filing Date for {ticker_symbol}')
plt.legend()
plt.show()


# In[ ]:





# In[ ]:




