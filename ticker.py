#!/usr/bin/env python3

import pandas as pd
import subprocess as sp

def chunks(lst, n):
	#n-sized chunks from the inputted list of stocks
	for i in range(0, len(lst), n):
		yield lst[i:i+n]

tickerList = []
url = 'ftp://ftp.nasdaqtrader.com/symboldirectory/nasdaqlisted.txt'
call = sp.call(["/opt/homebrew/bin/wget", url])

nasdaqFile = open("nasdaqlisted.txt", "r")
contents = nasdaqFile.readlines()
for line in contents:
	line = line.strip().split("|")
	print(line[0])
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
	print(symbol_strings[i])



