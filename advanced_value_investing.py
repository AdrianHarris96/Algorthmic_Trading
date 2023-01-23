#!/usr/bin/env python3

#Value Investing Algorithm - Buying stocks that are cheap relative to their intrinsic value
#price to earnings metrics - current stock prick divided by estimated annually earnings 

import numpy as np
import pandas as pd
import subprocess as sp
import requests 
import math 
import xlsxwriter 
from scipy import stats 
import math
from secrets import IEX_CLOUD_API_TOKEN
import time 

def chunks(lst, n):
	#n-sized chunks from the inputted list of stocks
	for i in range(0, len(lst), n):
		yield lst[i:i+n]

def portfolio_input(): #This will need to be changed
	global portfolio_size
	portfolio_size = input('Enter the size of your portfolio_size:')
	position_size = float(portfolio_size)/len(value_df.index)
	#print position_size
	for row in value_df.index:
		value_df.loc[row, 'Number of Shares to Buy'] = math.floor(position_size/value_df.loc[row, 'Price'])
	print(value_df) 

start_time = time.time()
tickerList = []
url = 'ftp://ftp.nasdaqtrader.com/symboldirectory/nasdaqlisted.txt'
call = sp.call(["/opt/homebrew/bin/wget", url])

nasdaqFile = open("nasdaqlisted.txt", "r")
contents = nasdaqFile.readlines()
for line in contents:
	line = line.strip().split("|")
	#print(line[0])
	if len(line[0]) > 5:
		pass
	else:
		tickerList.append(line[0])
nasdaqFile.close()

nasdaqRemoval = sp.call(["rm", "nasdaqlisted.txt"])
symbol_groups = list(chunks(tickerList, 100))
symbol_strings = []
for i in range(0, len(symbol_groups)):
	symbol_strings.append(','.join(symbol_groups[i])) #string of 100-sized chunks printed with each iteration of the loop 
	#print(symbol_strings[i])

#Better Value Strategy
#Consider price-to-earnings, price-to-book, price-to-sales, enterprise value (divided by earnings before interests, taxes, depreciation, and amoritization), enterprise value (divided by gross profit)

symbol = 'AAPL'
batch_api_call_url = f'https://sandbox.iexapis.com/stable/stock/market/batch?symbols={symbol},fb&types=quote,advanced-stats&token={IEX_CLOUD_API_TOKEN}'
data = requests.get(batch_api_call_url).json()
#print(data[symbol]['advanced-stats'])

#price-to-earnings
pe_ratio = data[symbol]['quote']['peRatio']

#price-to-book
pb_ratio = data[symbol]['advanced-stats']['priceToBook']

#price-to-sales
ps_ratio = data[symbol]['advanced-stats']['priceToSales']

#enterprise_value EV/EBITDA - EV divided by earnings before interests, taxes, depreciation and amortization

enterprise_value = data[symbol]['advanced-stats']['enterpriseValue']
ebitda = data[symbol]['advanced-stats']['EBITDA']
#print(enterprise_value)

ev_to_ebitda = enterprise_value/ebitda

#enterprise_value divided by gross profit (EV/GP)
gross_profit = data[symbol]['advanced-stats']['grossProfit']
ev_to_gross_profit = enterprise_value/gross_profit

#Building the DataFrame 

value_columns = ['Ticker', 'Price', 'Number of Shares to Buy', 'Price-to-Earnings Ratio', 'PE Percentile', 'Price-to-Book Ratio', 'PB Percentile', 'Price-to-Sales Ratio', 'PS Percentile', 'EV/EBITDA', 'EV/EBITDA Percentile', 'EV/GP', 'EV/GP Percentile', 'Value Score']

value_df = pd.DataFrame(columns=value_columns)

for symbol_string in symbol_strings: # Troubleshooting with [:1] if necessary
	batch_api_call_url = f'https://sandbox.iexapis.com/stable/stock/market/batch?symbols={symbol_string},fb&types=quote,advanced-stats&token={IEX_CLOUD_API_TOKEN}'
	data = requests.get(batch_api_call_url).json()
	for symbol in symbol_string.split(','):
		try:
			enterprise_value = data[symbol]['advanced-stats']['enterpriseValue']
			ebitda = data[symbol]['advanced-stats']['EBITDA']
			gross_profit = data[symbol]['advanced-stats']['grossProfit']
			try:
				ev_to_ebitda = enterprise_value/ebitda
			except TypeError:
				ev_to_ebitda = np.NaN
			try:
				ev_to_gross_profit = enterprise_value/gross_profit
			except TypeError:
				ev_to_gross_profit = np.NaN
			value_df = value_df.append(
				pd.Series([
					symbol, 
					data[symbol]['quote']['latestPrice'],
					'n/a',
					data[symbol]['quote']['peRatio'],
					'n/a',
					data[symbol]['advanced-stats']['priceToBook'],
					'n/a',
					data[symbol]['advanced-stats']['priceToSales'],
					'n/a',
					ev_to_ebitda,
					'n/a',
					ev_to_gross_profit,
					'n/a',
					'n/a'
					], index = value_columns),
				ignore_index = True
			)
		except KeyError:
			continue

#Dealing with Missing Data 
value_df.dropna(inplace = True)
#Replacing the attributes in each column with the .mean() of the column makes little sense to me -> I instead simply drop those columns 
#for column in ['Price-to-Earnings Ratio', 'Price-to-Book Ratio', 'Price-to-Sales Ratio', 'EV/EBITDA', 'EV/GP']:
	#value_df[column].dropna()

#print(value_df[value_df.isnull().any(axis=1)]) #Specifies all the ROWS that may be null in a dataframe
#print(value_df)

#Calculating Metrics 
from scipy.stats import percentileofscore as score
metrics = {'Price-to-Earnings Ratio':'PE Percentile', 'Price-to-Book Ratio':'PB Percentile', 'Price-to-Sales Ratio':'PS Percentile', 'EV/EBITDA':'EV/EBITDA Percentile', 'EV/GP':'EV/GP Percentile'
}

for metric in metrics.keys():
	for row in value_df.index:
		value_df.loc[row, metrics[metric]] = score(value_df[metric], value_df.loc[row, metric]) / 100

#Calculating the RV Score 
from statistics import mean 
for row in value_df.index:
	value_percentiles = []
	for metric in metrics.keys():
		value_percentiles.append(value_df.loc[row, metrics[metric]]) #isolation of a specific row and value (using the metrics dictionary)
	value_df.loc[row, 'Value Score'] = mean(value_percentiles)

#Stock Selection 
value_df.sort_values('Value Score', ascending=True, inplace=True)
value_df = value_df[:50]
value_df.reset_index(drop=True, inplace=True)
#print(value_df)

#Number of Shares to Buy 
portfolio_input()

#Formatting Excel Output 
writer = pd.ExcelWriter('value_strategy.xlsx', engine='xlsxwriter')
value_df.to_excel(writer, sheet_name='value_strategy', index=False)

background_color = '#0a0a23'
font_color = '#ffffff'

string_format = writer.book.add_format({'font_color':font_color, 'bg_color':background_color, 'border':1})
dollar_format = writer.book.add_format({'num_format': '$0.00', 'font_color':font_color, 'bg_color':background_color, 'border':1})
integer_format = writer.book.add_format({'num_format': '0', 'font_color':font_color, 'bg_color':background_color, 'border':1})
percent_format = writer.book.add_format({'num_format': '0.0%', 'font_color':font_color, 'bg_color':background_color, 'border':1})
float_format = writer.book.add_format({'num_format': '0.0', 'font_color':font_color, 'bg_color':background_color, 'border':1})

column_formats = {'A' : ['Ticker', string_format], 'B' : ['Price', dollar_format], 'C' : ['Number of Shares to Buy', integer_format], 'D' : ['Price-to-Earnings Ratio', float_format], 'E' : ['PE Percentile', percent_format], 'F' : ['Price-to-Book Ratio', float_format], 'G' : ['PB Percentile', percent_format], 'H' : ['Price-to-Sales Ratio', float_format], 'I' : ['PS Percentile', percent_format], 'J' : ['EV/EBITDA', float_format], 'K' : ['EV/EBITDA Percentile', percent_format], 'L' : ['EV/GP', float_format], 'M' : ['EV/GP Percentile', percent_format], 'N' : ['Value Score', percent_format]}

for column in column_formats.keys():
	writer.sheets['value_strategy'].set_column(f'{column}:{column}', 25, column_formats[column][1]) #formatting excel sheet using for-loop
	writer.sheets['value_strategy'].write(f'{column}1', column_formats[column][0], column_formats[column][1]) #formating of header (hence, f-string 1 for cell A1, B1, C1 ...)
writer.save()

print('Runtime:', time.time() - start_time)


