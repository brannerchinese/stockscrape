stockscrape
===========

**Version**: 1.1, 20130220

**Author**: David Prager Branner


Goal
----
To explore web scraping using the headline news service on (finance.yahoo.com).

Principal Contents
------------------

`stockscrape.py`: Version for Python 3.2 only.

`OUTPUT/`: where output file, `stock_report.tex` is saved. Note that this file needs to be compiled with LaTeX in order to be usable. The LaTeX output file `stock_report.pdf` will normally be found here as well.

`CODE/`: contains `.tex` templates for beginning and end of output file.

`DATA/`: contains `.txt` file of stock tickers to be looked up, one per line.

`PREVIOUS_VERSIONS/`: previous versions will be stored here with date appended, but they may not run as is because directory structures have changed. See past commits of the repository for complete working installations of these older versions.

Notes
-----

Output contains first a table of stock prices and related data, from the Yahoo API, followed by a list of recent headlines for each stock ticker. The LaTeX package `longtable` is used, to allow breaking of tables across pages if they exceed the amount of available space on the first page.

This version scrapes the Yahoo financial news site using Beautiful Soup 4. 


New in this version
-------------------
1. Suggestions from code review mostly implemented. (See (https://github.com/brannerchinese/stockscrape/pull/1))

---

Past versions:

 * 1.0, 20130219
 * 0.4, 20130214
 * 0.3, 20130213
 * 0.2, 20130213
 * 0.1, 20130212
