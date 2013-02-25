#!/usr/bin/env python
# headline_length.py
# 20130225, works
# Run with Python 3.2

import datetime as D
import urllib.request as UR
import urllib.error as UE
import collections as C
import re
import os
from bs4 import BeautifulSoup as BS
import time as T
import sys

def main(filename='stock_list.txt'):
    """
    Find the length of the longest headline, link, and source
    for headlines scraped from the Yahoo financial news pages.
    """
    contents = get_contents(filename)
    ################################
    # Stock news
    process_news(contents)
    ################################
    print('\n\nFinished headlines.')

def process_news(contents):
    """Scrape news headlines."""
    # get today's date
    today = D.date.today().strftime('%Y-%m-%d')
    # prepare lists to receive lengths of headlines, links, and sources
    hl_lengths = []
    link_lengths = []
    source_lengths = []
    # now run through each ticker
    for symbol in contents:
#        print('\n*******************\nNow processing {0}\n*******************'.\
#                format(symbol)) # debug-print
        # Date such as &t=2012-05-14 can be appended to URL
        url = 'http://finance.yahoo.com/q/h?s=' + symbol + '&t=' + today
        # Retrieve and process webpage, yielding list of lists
        webpage = retrieve_webpage(symbol)
#        headline_list += process_webpage(webpage)
        hls, links, sources = process_webpage(webpage)
        hl_lengths.extend(hls)
        link_lengths.extend(links)
        source_lengths.extend(sources)
    print('longest headline:', max(hl_lengths), '\nlongest link:', \
            max(link_lengths), '\nlongest source:', max(source_lengths))
#    return running_tex_str

def escape_for_latex(a_string):
    """Perform simple text replacements for LaTeX compatibility."""
    # Using ordered dictionary in case order of replacement matters.
    # HTML forms probably rare in Beautiful Soup output, but retained in case.
    the_dict = C.OrderedDict([\
            ('&amp;', '\\&'), \
            ('&gt;', '>'), \
            ('&lt;', '<'), \
            ('&', '\\&'), \
            ('$', '\\$'), \
            ('%', '\\%'), \
            ('#', '\\#'), \
            (' "', ' ``'), \
            (" '", " `"), \
            ('"', "''"), \
            ('\xa0', ' ')])
    # Next: add curly quotes to this list?
    for key in the_dict:
        a_string = a_string.replace(key, the_dict.get(key))
    return a_string

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
    # prepare count of longest items
    hl_lengths = []
    link_lengths = []
    source_lengths = []
    if webpage:
        for item in webpage.find_all('li'):
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
                source = source.strip('at ')
                source = escape_for_latex(source)
                #
                hl_lengths.append(len(headline))
                link_lengths.append(len(link))
                source_lengths.append(len(source))
            except Exception as e:
                continue
    return hl_lengths, link_lengths, source_lengths

def get_contents(filename):
    """
    In:  filename
         Starting in main directory.
    Out: file_start template and the contents of the file named as argument.
         Ending in main directory.
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

def format_data(is_dict):
    """
    In:  Dictionary of ticker:statistics
    Out: Same dictionary, but with formatting edited.
    """
    # Modify formatting of ticker information
    is_dict['Symbol'] = '\\head{' + is_dict['Symbol'] + '}'
    # Add percent change information
    # Note that this will eventually be change from last lookup (stored data),
    #   for now, calculated only based on downloaded values.
    if is_dict['Change'] == 'N/A':
        is_dict['Percent change'] = 'N/A'
    else:
        # float() is being used because these values are strings;
        # the one exception, above, is 'N/A'
        as_float = (float(is_dict['Change']))*100/\
                (float(is_dict['Last trade']) - float(is_dict['Change']))
        is_dict['Percent change'] = '{0:.2f}\%'.format(as_float)
        if is_dict['Percent change'].find('-') == -1:
            if is_dict['Percent change'] == '0\%':
                is_dict['Percent change'] = '0'
            else:
                is_dict['Percent change'] = '+' + is_dict['Percent change']
    return is_dict

if __name__ == '__main__':
    main()
