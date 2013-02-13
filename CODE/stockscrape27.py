#!/usr/bin/env python
# yahoo_lookup27.py
# 20130211
# Runs with: Python 2.7

import datetime as D
import urllib2 as U
import re
import os

def main(filename='stock_list.txt'):
    """
    Look up vital stock data and headlines on Yahoo 
    and save to new LaTeX document.
    """
    current_dir = os.getcwd()
    contents, running_text = get_contents(filename)
    ################################
    # 1. Stock prices 
    ################################
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
        running_text += ' & '.join(line_for_table) + '\\\\ \hline\n'
    running_text += '\\end{tabular}\n \\end{center}\n \\end{table}%\n\\clearpage'
    print '\nFinished prices.'
    ################################
    # 2. Stock news
    ################################
    # get today's date
    today = D.date.today().strftime('%Y-%m-%d')
    for symbol in contents:
        data = []
        # to URL, can append &t=2012-05-14 or other date
        url = 'http://finance.yahoo.com/q/h?s=' + symbol + '&t=' + today
        document = U.urlopen(url).read()
        document_list = document.split('</span></h3><ul>')
        if len(document_list) > 1:
            headlines = document_list[1].split('</ul>')[0]
            # headlines contains a set of <li>...</li> delimited headlines and
            #  URLs, along with other matter:
            # <li><a href="">HEADLINE</a><cite>SOURCE&nbsp;<span>DATE</span></cite></li>
            headline_list = headlines.replace('<li>', '').replace('</li>',
                    '\n').split('\n')[0:-1]
            for item in headline_list:
                title, item = item.split('">')[1].split('</a><cite>')
                title = title.replace('&amp;', '\\&')
                title = title.replace('&gt;', '>')
                title = title.replace('&lt;', '<')
                title = title.replace('$','\\$')
                title = title.replace('%', '\\%')
                title = title.replace('#', '\\#')
                #title = title.replace('[\\$\\$', '\\ [\\$\\$')
                source, date = item.split('&nbsp;<span>')
                date = date.split('</span></cite>')[0]
                data.append([title, source, date])
        running_text += '\n\n\section*{' + symbol + '}\n'
        if data:
            running_text += '\\begin{itemize}'
            for i in data:
                running_text += '\n\item ' + i[0] + ' --- ' + i[1] + ' ' + i[2]
            running_text = running_text.replace('\item [', '\item\\ [')
            running_text += '\n\end{itemize}'
        else:
            running_text += 'No news found.'
    write_contents(running_text)
    os.chdir(current_dir)
    print '\nFinished headlines.'


def lookup(tickers, list_items, stats = 'sd1l1c1dr1q'):
    '''
Look up a few vital elements in the Yahoo API and return them as a dictionary.
In:  Three arguments neeeded for accessing Yahoo API.
Out: Dictionary of tickers:stats.
'''
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
    # prepare dictionary to be returned
    full_data = []
    url = 'http://finance.yahoo.com/d/quotes.csv?s={0}&f={1}'.\
            format(tickers, stats)
    # get Yahoo data as list of lists
    try:
        data_list = U.urlopen(url).read().strip().split('\r\n')
    except U.URLError, e:
        print 'There is a URLerror\n{0}.'.format(e)
        quit()
    for item in data_list:
        one_row = item.split(',')
        # next: build dictionary for each "item"
        # and then append to list full_data
        one_row_dict = {}
        for i in xrange(len(list_items)):
            # strip quotes while adding item to one_row_dict
            one_row_dict[list_items[i]] = one_row[i].strip('"')
        full_data.append(one_row_dict)
    return full_data

def write_contents(running_text):
    """
    In:  Argument is string of LaTeX content without end-of-document matter.
    Out: Write the contents of the argument and save together with the file_end template.
    """
    os.chdir('../CODE')
    with open('file_end.tex', 'r') as f:
        running_text += f.read()
    os.chdir('..')
    with open('stock_report.tex', 'w') as f:
        f.write(running_text)
    return

def get_contents(filename):
    """
    In:  filename
    Out: file_start template and the contents of the file named as argument..
    """
    os.chdir('../CODE')
    with open('file_start.tex', 'r') as f:
        running_text = f.read()
    os.chdir('../DATA')
    with open(filename, 'r') as f:
        contents = f.read().split('\n')
    return contents, running_text

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
    # modify formatting of ticker information
    is_dict['Symbol'] = '\\head{' + is_dict['Symbol'] + '}'
    # add percent change information
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
    Out: x formatterd as string, truncated to "places" places
    """
    if type(x) not in [float, int]:
        print 'truncate() requires float or int as argument; {0} is of type'\
                '{1}.\n\nExiting.\n'.format(x, type(x))
        quit()
    elif x == 0:
        return str(0)
    else:
        x = str(int(x*(10**places)))
    return x[:-2] + '.' + x[-2:]

if __name__ == '__main__':
    main()
