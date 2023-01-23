#!/usr/bin/env python3

#The goal of this script is to select 50 stocks from the S&P 500 with the highest price momentum. High-Quality Momentum Stock Strategy!
#Old Goal Above -> New Goal incorporates all the stocks on the nasdaq

import numpy as np #numerical computing module (actually executed in C++)
import pandas as pd
import requests 
import math 
import xlsxwriter 
from scipy.stats import percentileofscore as score
from statistics import mean 
import subprocess as sp
from secrets import IEX_CLOUD_API_TOKEN

def chunks(lst, n):
	#n-sized chunks from the inputted list of stocks
	for i in range(0, len(lst), n):
		yield lst[i:i+n]

def portfolio_input():
	global portfolio_size
	portfolio_size = input('Enter the size of your portfolio_size:')
	position_size = float(portfolio_size)/len(hqm_dataframe.index)
	#print(position_size)
	for i in hqm_dataframe.index:
		hqm_dataframe.loc[i, 'Number of Shares to Buy'] = math.floor(position_size/hqm_dataframe.loc[i, 'Price'])
	#print(hqm_dataframe)

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

hqm_columns = ['Ticker', 'Price', 'Number of Shares to Buy', 'One-Year Price Return', 'One-Year Return Percentile', 'Six-Month Price Return', 'Six-Month Return Percentile', 'Three-Month Price Return', 'Three-Month Return Percentile',  'One-Month Price Return', 'One-Month Return Percentile', 'HQM Score']

hqm_dataframe = pd.DataFrame(columns = hqm_columns)
#print(hqm_dataframe)
call_counts = 0
for symbol_string in symbol_strings: #remove [:1] this and be sure the csv is up-to-date
	batch_api_call_url = f'https://cloud.iexapis.com/stable/stock/market/batch?symbols={symbol_string},fb&types=price,stats&token={IEX_CLOUD_API_TOKEN}'
	data = requests.get(batch_api_call_url).json()
	call_counts += 1
	#print(data['AAPL']['price']) 
	#print(data.status_code) #remove conversion to json object before doing running the status_code comment
	for symbol in symbol_string.split(','):
		if symbol not in data.keys():
			pass
		else:
			hqm_dataframe = hqm_dataframe.append(
				pd.Series(
					[symbol, data[symbol]['price'], 'N/A', data[symbol]['stats']['year1ChangePercent'], 'N/A', data[symbol]['stats']['month6ChangePercent'], 'N/A', data[symbol]['stats']['month3ChangePercent'], 'N/A',  data[symbol]['stats']['month1ChangePercent'], 'N/A', 'N/A'], index = hqm_columns), ignore_index = True
				)
print(call_counts)
hqm_dataframe.dropna(inplace = True)
#print(hqm_dataframe)

#Calculating Momentum Percentiles 
time_periods = ['One-Year', 'Six-Month', 'Three-Month', 'One-Month']

for row in hqm_dataframe.index: #looping through each row to complete the caluculation
	for time_period in time_periods:
		change_col = f'{time_period} Price Return'
		percentile_col = f'{time_period} Return Percentile'
		hqm_dataframe.loc[row, percentile_col] = score(hqm_dataframe[change_col], hqm_dataframe.loc[row, change_col])/100

#print(hqm_dataframe)

#Calculating HQM Score 
for row in hqm_dataframe.index:
	momentum_percentiles = []
	for time_period in time_periods:
		momentum_percentiles.append(hqm_dataframe.loc[row, f'{time_period} Return Percentile']) #append the list with the percentile values for each row 
	hqm_dataframe.loc[row, 'HQM Score'] = mean(momentum_percentiles)

#print(hqm_dataframe)

hqm_dataframe.sort_values('HQM Score', ascending=False, inplace=True)
hqm_dataframe = hqm_dataframe[:50]
hqm_dataframe.reset_index(drop=True, inplace=True)

portfolio_input()

#Writing to Excel
writer = pd.ExcelWriter('momentum_strategy.xlsx', engine='xlsxwriter')
hqm_dataframe.to_excel(writer, sheet_name = 'momentum_strategy', index=False)

background_color = '#0a0a23'
font_color = '#ffffff'

string_format = writer.book.add_format({'font_color':font_color, 'bg_color':background_color, 'border':1})
dollar_format = writer.book.add_format({'num_format': '$0.00', 'font_color':font_color, 'bg_color':background_color, 'border':1})
integer_format = writer.book.add_format({'num_format': '0', 'font_color':font_color, 'bg_color':background_color, 'border':1})
percent_format = writer.book.add_format({'num_format': '0.0%', 'font_color':font_color, 'bg_color':background_color, 'border':1})

column_formats = {
	'A':['Ticker', string_format], 
	'B':['Price', dollar_format], 
	'C':['Number of Shares to Buy', integer_format], 
	'D':['One-Year Price Return', percent_format], 
	'E':['One-Year Return Percentile', percent_format], 
	'F':['Six-Month Price Return', percent_format], 
	'G':['Six-Month Return Percentile', percent_format], 
	'H':['Three-Month Price Return', percent_format], 
	'I':['Three-Month Return Percentile', percent_format],  
	'J':[']One-Month Price Return', percent_format], 
	'K':['One-Month Return Percentile', percent_format], 
	'L':['HQM Score', percent_format]}

for column in column_formats.keys():
	writer.sheets['momentum_strategy'].set_column(f'{column}:{column}', 18, column_formats[column][1]) #parsing out format and formatting 
	writer.sheets['momentum_strategy'].write(f'{column}1', column_formats[column][0], column_formats[column][1]) #parsing out header and formatting 
writer.save()

#Next steps: Comment, parallelize, further filtering to determine few stocks to invest in 
#Ultimate Goal: Link to Vanguard account, run autonomously, troubleshoot
