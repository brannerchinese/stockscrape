#!/usr/bin/env python3
# headline_to_db.py
# 20130313, works
# Run with Python 3

import datetime
import urllib.request
import urllib.error
import collections
import re
import os
import bs4
import time
import sqlite3
import sys


class StockScraper():
    def __init__(self, verbose, filename):
        self.verbose = verbose
        self.api_results = None
        self.tag_names = ['Symbol', 'Last trade date', 'Last trade', 'Change',
                'Dividend/share', 'Dividend pay date', 'Ex-dividend date']
        # Tag information from
        #    https://ilmusaham.wordpress.com/tag/stock-yahoo-data/
        # Note that names are handled separately; they may contain commas
        self.tags_to_stats = {'Symbol': 's',
                       'Last trade date': 'd1',
                       'Last trade': 'l1',
                       'Change': 'c1',
                       'Dividend/share': 'd',
                       'Dividend pay date': 'r1',
                       'Ex-dividend date': 'q'}
        self.filename = filename
        self.ticker_str = None

    def debug_print(self, *args, end='\n'):
        if self.verbose:
            print(*args, end='\n')
        else:
            pass

    def process_tickers(self):
        """Gather stock data from Yahoo API and output as LaTeX table."""
        # Create list of tickers
        # We determined experimentally that Yahoo starts failing to respond
        #     when there are more than 200 tickers; in addition, Yahoo returned
        #     a message, "Sorry, the Yahoo! Finance system limits quotes to 200
        #     ticker symbols at a time. Please adjust your request to include
        #     200 or less."
        yahoo_limit = 200
        # Empty set to start with
        data = []
        # We don't want to destroy self.api_results in this process.
        temp_api_results = self.api_results
        while temp_api_results:
            self.ticker_str = self.create_ticker_string(yahoo_limit)
            temp_api_results = temp_api_results[yahoo_limit:]
            data.extend(self.lookup())
        self.tag_names.insert(4, 'Percent change')
        self.debug_print('\nBelow we dump the dictionary of lists; each '
                'list contains '
                'values collected from the Yahoo API for a given ticker.')
        for row_dict in data:
            row_dict = self.format_data(row_dict)
            # create list of items to go into line of .tex table
            line_for_table = [row_dict[item]
                    for item in self.tag_names
                    if item in row_dict]
            # For now, print to STDOUT;
            #    LaTeX output to be handled in other program
            self.debug_print(line_for_table)
        print('\nFinished prices.\n')

    def get_api_results(self):
        """
        In:  filename
        Out: the contents of the file named as argument.
        """
        with open(os.path.join('DATA', self.filename), 'r') as f:
            self.api_results = f.read().split('\n')
        return self.api_results

    def create_ticker_string(self, limit):
        """
        In: Yahoo's upper limit of tickers per REQUEST
        Out: Assigns to self.ticker a string of plus-sign-delimited symbols.
        """
        self.ticker_str = '+'.join(self.api_results[:limit])
        # Use rstrip in case there had been an extra blank index.
        self.ticker_str.rstrip('+')

    def process_news(self):
        """Scrape news headlines and store to database."""
        # Get today's date as datetime object
        today = datetime.date.today()
        # Note that SQLite generates ISO 8601 with `SELECT date('now');`
        #   and these strings can be compared arithmetically, w correct results.
        #
        # Use "with" to keep db file clean
        with sqlite3.connect('hl.db') as connection:
            cursor = connection.cursor()
            # We need a copy of the existing db to prevent reduncant insertions
            cursor = cursor.execute('''SELECT ticker,headline FROM headlines''')
            current_db = cursor.fetchall()
            new_headline_count = 0
            old_headline_count = 0
            for symbol in self.api_results:
                print('\nNow processing {0}: '.format(symbol), end='')
                # Date such as &t=2012-05-14 can be appended to URL
                url = ('http://finance.yahoo.com/q/h?s=' + symbol + '&t=' +
                        today.isoformat())
                # Retrieve and process webpage, yielding list of lists
                webpage = self.retrieve_webpage(symbol)
                headline_list = self.process_webpage(webpage)
                self.debug_print('length of headline_list:', len(headline_list))
                for headline, link, source, newsdate in headline_list:
                    # Make sure nothing redundant is added;
                    #   for now check if symbol and headline already present
                    #   but later consider catch exception on INSERT
                    #       (must make them UNIQUE in db)
                    if (symbol, headline) in current_db:
                        old_headline_count += 1
                        self.debug_print(' found:', symbol, newsdate, headline)
                        continue
                    else:
                        self.debug_print(' added:', symbol, newsdate, headline)
                    # Problem: Yahoo's dates in headlines have no year;
                    #    if we convert, we will get 1900 for the year.
                    #    So prefix current year to date of news,
                    #    unless month of news is higher than current month
                    #    (i.e., previous year).
                    #    (Assumes no news is more than 11 months old;
                    #    untrue for ARTIX, for example, which had
                    #    February 29, 2012 when accessed on 20130306,
                    #    causing a Python error.)
                    try:
                        news_date = datetime.datetime.strptime(newsdate,
                                '%a, %b %d')
                    except:
                        print('  Date exception for', symbol)
                        continue
                    if today.month < news_date.month:
                        news_year = today.year - 1
                    else:
                        news_year = today.year
                    news_date = datetime.datetime(news_year,
                            news_date.month,
                            news_date.day)
                    news_date_str = datetime.datetime.strftime(news_date,
                            '%Y-%m-%d')
                    #
                    # Add it to database
                    new_headline_count += 1
                    cursor.execute('''INSERT INTO headlines (
                            ticker, headline, url, source, date, 
                            lookupdate) VALUES (?, ?, ?, ?, ?, ?);''',
                            (symbol, headline, link, source, news_date_str,
                                today))
                    print('.', end='')
                    if news_date == today:
                        print('  news date:', news_date, i)
            print('\n\n{0} new headlines added; {1} old headlines found.'.
                    format(new_headline_count, old_headline_count))

    def process_url(self, url, split_here = ''):
        """
        In:  url and optional to-split-at string (arguments)
        Out: returns list of discrete paragraph-contents, cast to UTF-8;
             if  URL error, quit.
        """
        try:
            retrieved_contents = urllib.request.urlopen(url).read().strip()
            # As of Py3 we get error "Type str doesn't support the buffer API"
            # So convert to Unicode now, because what we received is bytecode
            retrieved_contents = retrieved_contents.decode().split(split_here)
        except urllib.error.URLError as e:
            print('There is a URLerror\n', e, '\n and symbol =', symbol)
            # an empty return string will simply add no length to running value
            retrieved_contents = ''
        return retrieved_contents

    def retrieve_webpage(self, symbol):
        """
        In:  symbol (argument)
        Out: BS object, webpage
        """
        today = datetime.date.today().strftime('\%Y-\%m-\%d')
        url = 'http://finance.yahoo.com/q/h?s=' + symbol + '&t=' + today
        try:
            retrieved_contents = urllib.request.urlopen(url).read().strip()
        except urllib.error.URLError as e:
            print('There is a URLerror\n', e, '\n and symbol =', symbol)
            # an empty return string will be trapped in "if webpage"
            return None
        return bs4.BeautifulSoup(retrieved_contents)

    def process_webpage(self, webpage):
        """
        In:  webpage formatted by BS
        Out; list of lists; each sublist contains [headline, link, source, date]
        """
        headline_list = []
        if webpage:
            for item in webpage.find_all('li'):
                try:
                    # Headline
                    headline = item.a.text
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
                    #
                    # Date
                    newsdate = item.span.text
                    # replace parens
                    newsdate = re.sub('\(|\)', '', newsdate)
                    # If no date is given (string i.e., contains 'AM' or 'PM'),
                    #   then we supply current local date.
                    if newsdate.count('AM') or newsdate.count('PM'):
                         newsdate = time.strftime('%a, %b %d', time.localtime())
                    #
                    # Done
                    headline_list.append([headline, link, source, newsdate])
                except Exception as e:
                    continue
        return headline_list

    def lookup(self):
        """
        Look up a few vital elements in the Yahoo API;
                return them as a dictionary.
        In:  tickers has been assigned a string.
        Out: list of dictionaries, each representing the stats for a
                particular ticker.
        """
        stats_wanted = [item for item in self.tag_names
                if item in self.tags_to_stats]
        stats = ''.join(self.tags_to_stats[item] for item in stats_wanted)
        # Report on missing items
        missing = set(self.tag_names) - set(stats_wanted)
        if missing:
            print("Cannot identify tag(s): {}".format(', '.join(missing)))
        # get Yahoo data as list of lists
        url = ('http://finance.yahoo.com/d/quotes.csv?s={0}&f={1}'.
                format(self.ticker_str, stats))
        retrieved_contents = self.process_url(url, '\r\n')
        #
        # Prepare dictionary to be returned
        full_data = []
        for item in retrieved_contents:
            one_row = item.split(',')
            # Next: build dictionary for each "item"
            full_data.append({list_item: row_item.strip('"')
                    for list_item, row_item in zip(self.tag_names, one_row)})
        return full_data

    def format_data(self, tckr_stats):
        """
        In:  Dictionary of ticker:statistics
        Out: Same dictionary, but with formatting edited.
        """
        # Add percent change information
        # Note that this will eventually be change from last lookup
        #   (stored data), for now, calculated only based on downloaded values.
        if tckr_stats['Change'] == 'N/A':
            tckr_stats['Percent change'] = 'N/A'
        else:
            # float() is being used because these values are strings;
            # the one exception, above, is 'N/A'
            if (float(tckr_stats['Last trade']) == 0.0
                    and float(tckr_stats['Change' ]) == 0.0):
                pc_chg_as_float = 0.0
                print(' ***They were both zero.')
            elif (float(tckr_stats['Last trade']) -
                    float(tckr_stats['Change' ]) == 0):
                pc_chg_as_float = 100.0
                print(' *** Late trade', float(tckr_stats['Last trade']),
                        'Change', float(tckr_stats['Change' ]))
            else:
                pc_chg_as_float = ((float(tckr_stats['Change'])) * 100 /
                        (float(tckr_stats['Last trade']) -
                        float(tckr_stats['Change'])))
            tckr_stats['Percent change'] = '{0:.2f}%'.format(pc_chg_as_float)
            if tckr_stats['Percent change'].find('-') == -1:
                if tckr_stats['Percent change'] == '0%':
                    tckr_stats['Percent change'] = '0'
                else:
                    tckr_stats['Percent change'] = ('+' +
                            tckr_stats['Percent change'])
        return tckr_stats

##################
def main(filename='stock_list.txt', verbose=False):
    """
    Look up vital stock data and headlines on Yahoo
    and store to database.
    """
    S = StockScraper(verbose, filename)
    ################################
    S.api_results = S.get_api_results()
    ################################
    # 1. Stock prices
    S.process_tickers()
    ################################
    # 2. Stock news
    S.process_news()
    ################################
    # 3. Report to output
    print('\n\nFinished headlines.')

if __name__ == '__main__':
    main(verbose='-v' in sys.argv)
