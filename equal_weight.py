#!/usr/bin/env python3

#The goal of this section of the course is to create a Python script that will accept the value of your portfolio and tell you how many shares of each S&P 500 constituent you should purchase to get an equal-weight version of the index fund.

import numpy as np #numerical computing module (actually executed in C++)
import pandas as pd
import requests 
import math 
import xlsxwriter 

stocks = pd.read_csv('sp_500_stocks.csv')
from secrets import IEX_CLOUD_API_TOKEN #Be sure secrets.py is in your current working directory 

#symbol = 'AAPL'
#api_url = f'https://sandbox.iexapis.com/stable/stock/{symbol}/quote/?token={IEX_CLOUD_API_TOKEN}'
#data = requests.get(api_url)
#print(data.status_code) -> The status code will be printed in this case 
#data = requests.get(api_url).json() #returns a json object == dictionary of relevant info 

#Parsing API Call 
#price = data['latestPrice']
#market_cap = data['marketCap']

#Adding our stocks data to a PANDAS DataFrame 
my_columns = ['Ticker', 'Stock Price', 'Market Capitalization', 'Number of Shares to Buy']
final_dataframe = pd.DataFrame(columns = my_columns)
#for stock in stocks['Ticker'][:5]:
	#api_url = f'https://sandbox.iexapis.com/stable/stock/{stock}/quote/?token={IEX_CLOUD_API_TOKEN}'
	#data = requests.get(api_url).json()
	#final_dataframe = final_dataframe.append(pd.Series([stock, data['latestPrice'], data['marketCap'], 'N/A'], index=my_columns), ignore_index=True)
#print(final_dataframe)
#The code above does ~500 separate API calls, which will take a considerable amount of time. We can improve this via batch calls.

#Batch API Calls 
def chunks(lst, n):
	#n-sized chunks in the list (lst)
	for i in range(0, len(lst), n):
		yield lst[i: i+n]
symbol_strings = []
symbol_groups = list(chunks(stocks['Ticker'], 100)) #Provides a pd series (for the column, Ticker) that is then converted to a list
for i in range(0, len(symbol_groups)):
	symbol_strings.append(','.join(symbol_groups[i])) #go through the list of lists and join at the , -> Creates a long string with all the tickers for each n-sized chunk 
final_dataframe = pd.DataFrame(columns = my_columns)
for symbol_string in symbol_strings:
	batch_api_call_url = f'https://sandbox.iexapis.com/stable/stock/market/batch?symbols={symbol_string}&types=quote&token={IEX_CLOUD_API_TOKEN}'
	#print(batch_api_call_url)
	data = requests.get(batch_api_call_url).json()
	for symbol in symbol_string.split(','):
		final_dataframe = final_dataframe.append(
			pd.Series(
				[symbol, data[symbol]['quote']['latestPrice'], data[symbol]['quote']['marketCap'], 'N/A'], index = my_columns), ignore_index=True)

#print(final_dataframe)

#Calculating the Number of Shares to Buy
portfolio_size = input('Enter the value of portfolio:')
value = float(portfolio_size)
#I skipped doing the error-handling, but one could add try-except ValueError blocks in the case of the user inputting the incorrect data type 
position_size = value/len(final_dataframe.index)
for i in range(0, len(final_dataframe.index)):
	final_dataframe.loc[i, 'Number of Shares to Buy'] = math.floor(position_size/final_dataframe.loc[i, 'Stock Price'])
#print(final_dataframe)

#Formatting Excel Output 
writer = pd.ExcelWriter('recommended_trades.xlsx', engine='xlsxwriter')
final_dataframe.to_excel(writer, 'recommended_trades', index=False)
background_color = '#0a0a23'
font_color = '#ffffff'

string_format = writer.book.add_format({'font_color':font_color, 'bg_color':background_color, 'border':1})
dollar_format = writer.book.add_format({'num_format': '$0.00', 'font_color':font_color, 'bg_color':background_color, 'border':1})
integer_format = writer.book.add_format({'num_format': '0', 'font_color':font_color, 'bg_color':background_color, 'border':1})

#Apply Above Formats to Excel File 
#writer.sheets['recommended_trades'].set_column('A:A', 18, string_format)
#writer.sheets['recommended_trades'].set_column('B:B', 18, string_format)
#writer.sheets['recommended_trades'].set_column('C:C', 18, string_format)
#writer.sheets['recommended_trades'].set_column('D:D', 18, string_format)
#writer.save()

column_formats = {
	'A': ['Ticker', string_format],
	'B': ['Stock Price', dollar_format],
	'C': ['Market Capitalization', dollar_format],
	'D': ['Number of Shares to Buy', integer_format]
}

for column in column_formats.keys():
	writer.sheets['recommended_trades'].set_column(f'{column}:{column}', 18, column_formats[column][1]) #parsing out format and formatting 
	writer.sheets['recommended_trades'].write(f'{column}1', column_formats[column][0], column_formats[column][1]) #parsing out header and formatting 

writer.save()
