stockscrape
===========

**Version**: 1.4, 20130227

**Author**: David Prager Branner


Goal
====

To explore web scraping using the headline news service on (finance.yahoo.com).

Principal Contents
==================

Python Programs
---------------

1. `stockscrape.py`: Version for Python 3.2 only. This is the principal scraping program.

1. `headline_length.py`: Trimmed version for determining the longest attested headline, link, and news-source, in preparation for creating database fields. Default list of stock tickers is the same as for `stockscrape.py`; several others are found in `DATA/`.

1. `headline_play.py`: Preliminary version of `stockscrape.py` modified to save unique headlines and associated information to a SQLite database.

Directories
-----------

`OUTPUT/`: where output file, `stock_report.tex` is saved. Note that this file needs to be compiled with LaTeX in order to be usable. The LaTeX output file `stock_report.pdf` will normally be found here as well.

`CODE/`: contains `.tex` templates for beginning and end of output file.

`DATA/`: contains `.txt` file of stock tickers to be looked up, one per line.

`PREVIOUS_VERSIONS/`: previous versions will be stored here with date appended, but they may not run as is because directory structures have changed. See past commits of the repository for complete working installations of these older versions.

Scripts
-------

Scripts for use with `headline_play.py` (to be run in the following order):

 1. `create_table.sqlscript`: Creates the three tables currently in the database.
 1. `insert_all_tickers.sqlscript`: Populates the database with stock and fund tickers.

 Instructions for running these scripts are found in their headers.

 Note that before running `headline_play.py`, it is best to run `sqlite3` and empty the `headlines` table, otherwise the LaTeX output will not populate correctly. Use the following two commands at the `sqlite3` prompt:

 `DELETE FROM headlines;
SELECT ticker,headline FROM headlines;`

 This will ensure that the table is empty.

Notes
=====

Output of `stockscrape.py` contains first a table of stock prices and related data, from the Yahoo API, followed by a list of recent headlines for each stock ticker. The output is a `.tex` file, while must be compiled to produce human-readlable output. The LaTeX package `longtable` is used, to allow breaking of tables across pages if they exceed the amount of available space on the first page.

This version scrapes the Yahoo financial news site using Beautiful Soup 4. 

New in this version
-------------------
1. Code now populates an SQLite database with headlines and their urls, sources, and dates. Redundant headlines are suppressed.
1. Code adds the appropriate year to the date of the headeline: this year or last.

Overview of project
-------------------

 * Phase 1: ( **Finished**) Basic scraper and LaTeX output of API-data and scraped headlines.
 * Phase 2: Now underway: Use SQL to store and manipulate data.
 * Phase 3: Use a web framework to create a GUI for easy management of the application.

---

Past versions:

 * 1.3, 20130225
 * 1.2, 20130222
 * 1.1, 20130220
 * 1.0, 20130219
 * 0.4, 20130214
 * 0.3, 20130213
 * 0.2, 20130213
 * 0.1, 20130212
