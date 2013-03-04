#!/usr/bin/env python
# headline_to_db.py
# 20130304
# Run with Python 3.2

import datetime as D
import urllib.request as UR
import urllib.error as UE
import collections as C
import re
import os
from bs4 import BeautifulSoup as BS
import time as T
import sqlite3 as SQ

def main(filename='stock_list.txt'):
    """
    Look up vital stock data and headlines on Yahoo
    and store to database.
    """
    contents = get_contents(filename)
    ################################
    # 1. Stock prices
    process_tickers(contents)
    ################################
    # 2. Stock news
    process_news(contents)
    ################################
    # 3. Report to output
    print('\n\nFinished headlines.')

def process_tickers(contents):
    """Gather stock data from Yahoo API and output as LaTeX table."""
    list_items = ['Symbol', 'Last trade date', 'Last trade', 'Change',
            'Dividend/share', 'Dividend pay date', 'Ex-dividend date']
    # Create list of tickers
    tickers = create_ticker_string(contents)
    data = lookup(tickers, list_items)
    list_items.insert(4, 'Percent change')
    print('\n  Below we dump the dictionary of lists; each list contains '
            'values collected from the Yahoo API for a given ticker.\n')
    for row_dict in data:
        row_dict = format_data(row_dict)
        # create list of items to go into line of .tex table
        line_for_table = [row_dict[item] for item in list_items]
        # For now, print to STDOUT; LaTeX output to be handled in other program
        print(line_for_table)
    print('\nFinished prices.\n')

def process_news(contents):
    """Scrape news headlines and store to database."""
    # Get today's date in ISO 8601
    today = D.date.today().strftime('%Y-%m-%d')
    # Note that SQLite generates ISO 8601 with `SELECT date('now');`
    #     and these strings can be compared arithmetically, w correct results.
    #
    # Use "with" to keep db file clean
    with SQ.connect('hl.db') as connection:
        cursor = connection.cursor()
        # We need a copy of the existing db to prevent reduncant insertions
        cursor = cursor.execute('''SELECT ticker,headline FROM headlines''')
        current_db = cursor.fetchall()
        for symbol in contents:
#            print('\n**************\nNow processing {0}\n**************'.\
#                    format(symbol)) # debug-print
            headline_list = []
            # Date such as &t=2012-05-14 can be appended to URL
            url = 'http://finance.yahoo.com/q/h?s=' + symbol + '&t=' + today
            # Retrieve and process webpage, yielding list of lists
            webpage = retrieve_webpage(symbol)
            headline_list += process_webpage(webpage)
            if headline_list:
                for i in headline_list:
                    # Make sure nothing redundant is added;
                    #    for now check if symbol and headline already present
                    #    but later consider catch exception on INSERT
                    #        (must make them UNIQUE in db)
                    if (symbol, i[0]) in current_db:
                        continue
                    # Convert Yahoo's date to ISO 8601: %Y-%m-%d
                    #    Problem: we will get 1900 for the year.
                    #    So prefix current year to date of news,
                    #    unless month of news is higher than current month
                    #    (i.e., previous year).
                    #    (Assumes no news is more than 11 monts old.)
                    today_month = int(D.date.today().strftime('%m'))
                    news_month = int(D.datetime.strptime(i[3], '%a, %b %d').\
                            isoformat()[5:7])
                    if today_month < news_month:
                        news_year = str(int(D.date.today().strftime('%Y'))-1)
                    else:
                        news_year = int(D.date.today().strftime('%Y'))
                    i[3] = str(news_year) + '-' + \
                            D.datetime.strptime(i[3], '%a, %b %d').\
                            isoformat()[5:10]
                    #
                    # Add it to database
                    cursor.execute('''INSERT INTO headlines (''' +\
                            '''ticker, headline, url, source, date, ''' +\
                            '''lookupdate) VALUES (?, ?, ?, ?, ?, ?);''', \
                            (symbol, i[0], i[1], i[2], i[3], today))
        print('{0} tickers handled: \n   {1}.'.format(len(contents), contents))

def process_url(url, split_here = ''):
    """
    In:  url and optional to-split-at string (arguments)
    Out: returns list of discrete paragraph-contents, cast to UTF-8;
         if  URL error, quit.
    """
    try:
        data_list = UR.urlopen(url).read().strip()
        # As of Py3 we get error "Type str doesn't support the buffer API"
        # So convert to Unicode now, because what we received is bytecode
        data_list = data_list.decode().split(split_here)
    except UE.URLError as e:
        print('There is a URLerror\n', e, '\n and symbol =', symbol)
        # an empty return string will simply add no length to running value
        data_list = ''
    return data_list

def retrieve_webpage(symbol):
    """
    In:  symbol (argument)
    Out: BS object, webpage
    """
    today = D.date.today().strftime('\%Y-\%m-\%d')
    url = 'http://finance.yahoo.com/q/h?s=' + symbol + '&t=' + today
    try:
        data_list = UR.urlopen(url).read().strip()
    except UE.URLError as e:
        print('There is a URLerror\n', e, '\n and symbol =', symbol)
        # an empty return string will be trapped in "if webpage"
        return ''
    webpage = BS(data_list)
    return webpage

def process_webpage(webpage):
    """
    In:  webpage formatted by BS
    Out; list of lists; each sublist contains [headline, link, source, date]
    """
    headline_list = []
    if webpage:
        for item in webpage.find_all('li'):
            # Next: consider moving the processing of the four compounds out to
            # four functions, and calling from a list. Doing this will further
            # modularize the code.
            try:
                # Headline
                headline = item.a.text
                headline = escape_for_latex(headline)
                #
                # Link
                link = item.a.attrs['href']
                # many URLs have Yahoo-tracking prefix, which we strip
                link = re.sub('http.+?\*', '', link)
                #
                # Source, from which the date must be removed
                source = str(item.cite).replace('\xa0'+str(item.span), '')
                if source == 'None':
                    continue
                # replace <cite> and </cite> tags
                source = re.sub('<\/?cite>', '', source)
                # if Yahoo is supplying a link with a tracker, remove ``at ''
                source = re.sub('^at ', '', source)
                source = escape_for_latex(source)
                #
                # Date
                newsdate = item.span.text
                # replace parens
                newsdate = re.sub('\(|\)', '', newsdate)
                # If no date is given (string i.e., contains 'AM' or 'PM'),
                #   then we supply current local date.
                if newsdate.count('AM') or newsdate.count('PM'):
                     newsdate = T.strftime('%a, %b %d', T.localtime())
                #
                # Done
                headline_list.append([headline, link, source, newsdate])
            except Exception as e:
                continue
    return headline_list

def lookup(tickers, list_items, stats = 'sd1l1c1dr1q'):
    """
    Look up a few vital elements in the Yahoo API, return them as a dictionary.
    In:  Three arguments needed for accessing Yahoo API.
    Out: Dictionary of tickers:stats.
    """
    # Tag information from
    #    https://ilmusaham.wordpress.com/tag/stock-yahoo-data/
    # 0 s:  symbol
    # 1 d1: last trade date
    # 2 l1: last trade
    # 3 c:  change
    # 4 d:  dividend/share
    # 5 r1: dividend pay date
    # 6 q:  ex-dividend date
    # Note that names are handled separately; they may contain commas
    #
    # Prepare dictionary to be returned
    full_data = []
    url = 'http://finance.yahoo.com/d/quotes.csv?s={0}&f={1}'.\
            format(tickers, stats)
    # get Yahoo data as list of lists
    data_list = process_url(url, '\r\n')
    for item in data_list:
        one_row = item.split(',')
        # Next: build dictionary for each "item"
        #   and append to list full_data
        #   also, strip quotes while adding item to one_row_dict
        one_row_dict = {list_item: row_item.strip('"')
                for list_item, row_item in zip(list_items, one_row)}
        full_data.append(one_row_dict)
    return full_data

def get_contents(filename):
    """
    In:  filename
    Out: the contents of the file named as argument.
    """
    with open(os.path.join('DATA', filename), 'r') as f:
        contents = f.read().split('\n')
    return contents

def create_ticker_string(contents):
    """
    In: List of stock symbols
    Out: Returns the stock symbols, formatted as string of plus-sign-delimited symbols.
    """
    tickers = '+'.join(contents)
    # Use rstrip in case there had been an extra blank index.
    return tickers.rstrip('+')

def format_data(tckr_stats):
    """
    In:  Dictionary of ticker:statistics
    Out: Same dictionary, but with formatting edited.
    """
    # Add percent change information
    # Note that this will eventually be change from last lookup (stored data),
    #   for now, calculated only based on downloaded values.
    if tckr_stats['Change'] == 'N/A':
        tckr_stats['Percent change'] = 'N/A'
    else:
        # float() is being used because these values are strings;
        # the one exception, above, is 'N/A'
        pc_chg_as_float = (float(tckr_stats['Change']))*100/\
                (float(tckr_stats['Last trade']) - float(tckr_stats['Change']))
        tckr_stats['Percent change'] = '{0:.2f}%'.format(pc_chg_as_float)
        if tckr_stats['Percent change'].find('-') == -1:
            if tckr_stats['Percent change'] == '0%':
                tckr_stats['Percent change'] = '0'
            else:
                tckr_stats['Percent change'] = '+' +\
                        tckr_stats['Percent change']
    return tckr_stats

if __name__ == '__main__':
    main()
