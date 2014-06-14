#!/usr/bin/env python3
# db_to_latex.py
# 20140613, works
# Run with Python

"""Look up vital stock data and headlines in database; format in LaTeX."""

import datetime as D
import urllib.request as UR
import urllib.error as UE
import collections as C
import re
import os
from bs4 import BeautifulSoup as BS
import time as T
import sqlite3 as SQ

def main(filename='stock_list.txt', days_of_history = 7):
    """
    Look up vital stock data and headlines on Yahoo
    and store to database.
    """
    contents, running_tex_str = get_contents(filename)
    ################################
    # 1. Stock prices
    # ggg leave this alone for now
    running_tex_str = process_tickers(contents, running_tex_str)
    ###############################
    # 2. Stock news
    running_tex_str = process_news(contents, running_tex_str, days_of_history)
    ################################
    # 3. Write to output
    write_contents(running_tex_str)
    print('\n\nFinished headlines.')

def process_tickers(contents, running_tex_str):
    """Gather stock data from Yahoo API and output as LaTeX table."""
    # ggg leave this function alone for now.
    list_items = ['Symbol', 'Last trade date', 'Last trade', 'Change',
            'Dividend/share', 'Dividend pay date', 'Ex-dividend date']
    # Create list of tickers
    tickers = create_ticker_string(contents)
    data = lookup(tickers, list_items)
    list_items.insert(4, 'Percent change')
    for row_dict in data:
        row_dict = format_data(row_dict)
        # create list of items to go into line of .tex table
        line_for_table = [row_dict[item] for item in list_items]
        running_tex_str += ' & '.join(line_for_table) + '\\\\ \hline\n'
    running_tex_str += \
            '\\end{tabular}\n \\end{center}\n \\end{table}%\n\\clearpage'
    print('\nFinished prices.\n')
    return running_tex_str

def process_news(contents, running_tex_str, days_of_history):
    """Scrape news headlines and store to database."""
    # Get today's date as date object
    today = D.date.today()
    # Note that SQLite generates ISO 8601 with `SELECT date('now');`
    #     and these strings can be compared arithmetically, w correct results.
    #
    # Use "with" to keep db file clean
    with SQ.connect('hl.db') as connection:
        cursor = connection.cursor()
        for symbol in contents:
            print('\n\nNow processing {0}: '.format(symbol), 
                    end='') # debug-print
            # First check for no news at all.
            cursor = cursor.execute('''SELECT headline FROM headlines '''
                    '''WHERE ticker=?''', (symbol, ))
            if not cursor.fetchall():
                running_tex_str += '\n\n\section*{' + symbol +\
                        ' --- No news found.}\n'
                print('   No news found.') # debug-print
                continue
            # If we are here, there is some news so create section heading.
            running_tex_str += '\n\n\section*{' + symbol + '}\n'
            # Now retrieve news for each date within range back in time.
            #   Set sentinel for no news found.
            no_news = True
            print('dates: ', end='') # debug-print
            for days_back in range(0, days_of_history):
                the_date = today - D.timedelta(days_back)
                print(the_date, end='') # debug-print
                cursor = cursor.execute('''SELECT headline, source, date, url 
                        FROM headlines WHERE ticker=? 
                        AND date=? ''', (symbol, the_date))
                # Note that fetchall() returns a list of tuples
                # If there is news for this date, then send to separate
                #     function for processing and turn off no-news sentinel.
                tuple_list = cursor.fetchall()
                print(' ({}) '.format(len(tuple_list)), end='')
                if tuple_list:
                    no_news = False
#                    print('   sentinel unset for', symbol)
                    running_tex_str = \
                            append_dated_hl_to_tex(symbol, the_date, \
                            tuple_list, running_tex_str)
            if no_news:
#                print('\n   sentintel remains SET for', symbol)
#                print('\n', running_tex_str[-30:])
                print('\n    No news at all.', end='')
                running_tex_str = re.sub('{' + symbol + '}$',\
                        '{' + symbol + ' --- No news since ' +\
                        the_date.strftime('%A, %B %d, %Y') + '.}',\
                        running_tex_str)
#                print('\n', running_tex_str[-50:])
    return running_tex_str

def append_dated_hl_to_tex(symbol, the_date, tuple_list, running_tex_str):
    """
    In:  symbol (=ticker string), 
         the_date (single date for the headlines in tuple_list), 
         tuple_list: non-empty list of tuples, 
             each tuple containing hl, source, date; 
         running_tex_str contains LaTeX preamble and section header for symbol
             and also any subsection headers for headlines with later dates.
    Out: running_tex_str now has \subsection for this date.
    """
    # Begin formatting for LaTeX, for this symbol
    running_tex_str += '\n\subsection*{' +\
            the_date.strftime('%A, %B %d, %Y')    + '}\n'
    # Start itemized list of headlines in LaTeX file
    running_tex_str += '\\begin{itemize}'
    for i in tuple_list:
        # Convert headline_list into string for .tex file
        running_tex_str += ('\n\item\\ \\href{' + i[3] + '}{' + 
                escape_for_latex(i[0]) + '} (' + 
                escape_for_latex(i[1]) + ')')
    running_tex_str += '\n\end{itemize}'
    return running_tex_str

def make_date_obj(date):
    """
    In:  date string in ISO 8601 format.
    Out: Python datetime.date object comprising integers (year, month, day)
    """
    return D.date(int(date[0:4]), int(date[5:7]), int(date[8:]))

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

def write_contents(running_tex_str):
    """
    In:  Argument is string of LaTeX content without end-of-document matter.
    Out: Write the contents of the argument 
             and save together with the file_end template.
         Output is saved to output directory.
    """
    with open(os.path.join('code', 'file_end.tex'), 'r') as f:
        running_tex_str += f.read()
    with open(os.path.join('output', 'stock_report.tex'), 'w') as f:
        f.write(running_tex_str)
    return

def get_contents(filename):
    """
    In:  filename
    Out: file_start template and the contents of the file named as argument.
    """
    with open(os.path.join('code', 'file_start.tex'), 'r') as f:
        running_tex_str = f.read()
    with open(os.path.join('data', filename), 'r') as f:
        contents = f.read().split('\n')
        contents = [i for i in contents if i]
    return contents, running_tex_str

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
