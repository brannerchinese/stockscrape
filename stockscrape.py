#!/usr/bin/env python
# stockscrape32.py
# 20130219, works
# Run with Python 3.2

import datetime as D
import urllib as U
import collections as C
import re
import os
from bs4 import BeautifulSoup as BS
import time as T

def main(filename='stock_list.txt'):
    """
    Look up vital stock data and headlines on Yahoo
    and save to new LaTeX document.
    """
    contents, running_tex_str = get_contents(filename)
    ################################
    # 1. Stock prices
    running_tex_str = process_tickers(contents, running_tex_str)
    ################################
    # 2. Stock news
    running_tex_str = process_news(contents, running_tex_str)
    ################################
    # 3. Write to output
    write_contents(running_tex_str)
    print('\n\nFinished headlines.')

def process_tickers(contents, running_tex_str):
    """Gather stock data from Yahoo API and output as LaTeX table."""
    list_items = ['Symbol', 'Last trade date', 'Last trade', 'Change',
            'Dividend/share', 'Dividend pay date', 'Ex-dividend date']
    # Create list of tickers
    tickers = create_ticker_string(contents)
    data = lookup(tickers, list_items)
    list_items.insert(4, 'Percent change')
    for row_dict in data:
        line_for_table = []
        row_dict = format_data(row_dict)
        # create list of items to go into line of .tex table
        for item in list_items:
            line_for_table.append(row_dict[item])
        running_tex_str += ' & '.join(line_for_table) + '\\\\ \hline\n'
    running_tex_str += '\\end{tabular}\n \\end{center}\n \\end{table}%\n\\clearpage'
    print('\nFinished prices.\n')
    return running_tex_str

def process_news(contents, running_tex_str):
    """Scrape news headlines."""
    # get today's date
    today = D.date.today().strftime('%Y-%m-%d')
    for symbol in contents:
#        print('\n*******************\nNow processing {0}\n*******************'.\
#                format(symbol)) # debug-print
        headline_list = []
        # Date such as &t=2012-05-14 can be appended to URL
        url = 'http://finance.yahoo.com/q/h?s=' + symbol + '&t=' + today
        # Retrieve and process webpage, yielding list of lists
        webpage = retrieve_webpage(symbol)
        headline_list += process_webpage(webpage)
        # Done
        running_tex_str += '\n\n\section*{' + symbol + '}\n'
        if headline_list:
            running_tex_str += '\\begin{itemize}'
            for i in headline_list:
            # Convert headline_list into string
                running_tex_str += '\n\item ' + i[0] + ' (' + i[2] + \
                        ') ' + i[3] + ')'
            running_tex_str = running_tex_str.replace('\item [', '\item\\ [')
            running_tex_str += '\n\end{itemize}'
        else:
            running_tex_str += 'No news found.'
    return running_tex_str

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
        data_list = U.request.urlopen(url).read().strip()
        # As of Py3 we get error "Type str doesn't support the buffer API"
        # So convert to Unicode now, because what we received is bytecode
        data_list = data_list.decode().split(split_here) 
    except U.error.URLError as e:
        print('There is a URLerror\n{0}.').format(e) 
        quit()
    return data_list

def retrieve_webpage(symbol):
    """
    In:  symbol (argument)
    Out: BS object, webpage
    """
    today = D.date.today().strftime('\%Y-\%m-\%d')
    url = 'http://finance.yahoo.com/q/h?s=' + symbol + '&t=' + today
    try:
        data_list = U.request.urlopen(url).read().strip()
    except U.error.URLError as e:
        print('There is a URLerror\n{0}.').format(e)
        quit()
    webpage = BS(data_list)
    return webpage

def process_webpage(webpage):
    """
    In:  webpage formatted by BS
    Out; list of lists; each sublist contains [headline, link, source, date]
"""
    headline_list = []
    for item in webpage.find_all('li'):
        # Next: consdier moving the processing of the four compounds out to
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
            source = source.strip('at ')
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
            # ggg question: are we getting more than one headline per symbol?
#            print('\n', headline, '\n  ', link, '\n  ', source, \
#                    '\n   ', newsdate) # debug-print
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
        #   and then append to list full_data
        one_row_dict = {}
        for i in range(len(list_items)):
            # Strip quotes while adding item to one_row_dict
            one_row_dict[list_items[i]] = one_row[i].strip('"')
        full_data.append(one_row_dict)
    return full_data

def write_contents(running_tex_str):
    """
    In:  Argument is string of LaTeX content without end-of-document matter.
         Starting in main directory.
    Out: Write the contents of the argument and save together with the file_end template.
         Output is saved to OUTPUT directory; we return in main directory.
    """
    os.chdir('CODE')
    with open('file_end.tex', 'r') as f:
        running_tex_str += f.read()
    os.chdir('../OUTPUT')
    with open('stock_report.tex', 'w') as f:
        f.write(running_tex_str)
    os.chdir('..')
    return

def get_contents(filename):
    """
    In:  filename
         Starting in main directory.
    Out: file_start template and the contents of the file named as argument.
         Ending in main directory.
    """
    os.chdir('CODE')
    with open('file_start.tex', 'r') as f:
        running_tex_str = f.read()
    os.chdir('../DATA')
    with open(filename, 'r') as f:
        contents = f.read().split('\n')
    os.chdir('..')
    return contents, running_tex_str

def create_ticker_string(contents):
    """
    In: List of stock symbols
    Out: Returns the stock symbols, formatted as string of plus-sign-delimited symbols.
    """
    tickers = ''
    for item in contents:
        item_list = item.split(r'\n')
        tickers += item_list[0] + '+'
    return tickers.rstrip('+')

def format_data(is_dict):
    """
    In:  Dictionary of ticker:statistics
    Out: Same dictionary, but with formatting edited.
    """
    # Modify formatting of ticker information
    is_dict['Symbol'] = '\\head{' + is_dict['Symbol'] + '}'
    # Add percent change information
    # Note that this will eventually be cange from last lookup (stored data),
    #   for now, calculated only based on downloaded values.
    if is_dict['Change'] == 'N/A':
        is_dict['Percent change'] = 'N/A'
    else:
        as_float = (float(is_dict['Change']))*100/\
                (float(is_dict['Last trade']) - float(is_dict['Change']))
        is_dict['Percent change'] = truncate(as_float, 2) + '\%'
        if is_dict['Percent change'].find('-') == -1:
            if is_dict['Percent change'] == '0\%':
                is_dict['Percent change'] = '0'
            else:
                is_dict['Percent change'] = '+' + is_dict['Percent change']
    return is_dict

def truncate(x, places):
    """
    In:  x: float or int
    Out: x formatted as string, truncated to "places" places
    """
    if type(x) not in [float, int]:
        print('truncate() requires float or int as argument; {0} is of type'\
                '{1}.\n\nExiting.\n').format(x, type(x))
        quit()
    elif x == 0:
        return str(0)
    else:
        x = str(int(x*(10**places)))
    return x[:-2] + '.' + x[-2:]

if __name__ == '__main__':
    main()
