## stockscrape

**Version**: 2.0, 20130405

**Author**: David Prager Branner


## Goal

To explore web scraping using the headline news service on http://finance.yahoo.com.

See the PDF file in the output directory for a sample.

## Principal Contents

### Python Programs

All code is tested with Python v. 3.2 only.

1. `headline_to_db.py`: **Newly revised with this version**. Preliminary version of `stockscrape.py` modified to save unique headlines and associated information to a SQLite database. There will be a separate `db_to_latex.py` program to produce LaTeX output from the database, but it has not been implemented yet.

1. `stockscrape.py`: This is the principal scraping program. It has not been updated since v. 1.2.

1. `headline_length.py`: Trimmed version of `stockscrape.py` for determining the longest attested headline, link, and news-source, in preparation for creating database fields. Default list of stock tickers is the same as for `stockscrape.py`; several others are found in `DATA/`. 

### Directories

`OUTPUT/`: where output file, `stock_report.tex` is saved. Note that this file needs to be compiled with LaTeX in order to be usable. The LaTeX output file `stock_report.pdf` will normally be found here as well.

`CODE/`: contains `.tex` templates for beginning and end of output file.

`DATA/`: contains `.txt` file of stock tickers to be looked up, one per line.

### Scripts

Scripts for use with `headline_to_db.py` (to be run in the following order):

 1. `create_table.sqlscript`: Creates the three tables currently in the database.
 1. `insert_all_tickers.sqlscript`: Populates the database with stock and fund tickers.

Instructions for running these scripts are found in their headers.

Note that before running `headline_to_db.py`, it is best to run `sqlite3` and empty the `headlines` table, otherwise the LaTeX output will not populate correctly. Use the following two commands at the `sqlite3` prompt:

`DELETE FROM headlines;
SELECT ticker,headline FROM headlines;`

This will ensure that the table is empty.

## Notes

Output of `stockscrape.py` contains first a table of stock prices and related data, from the Yahoo API, followed by a list of recent headlines for each stock ticker. The output is a `.tex` file, while must be compiled to produce human-readlable output. The LaTeX package `longtable` is used, to allow breaking of tables across pages if they exceed the amount of available space on the first page.

This version scrapes the Yahoo financial news site using Beautiful Soup 4. 

### New in this version

1. Converted to class structure.
1. Enabled `-v` flag for verbose output, if run from commend line.
1. Headlines now have clickable URLs attached to them.
1. Output to STDOUT and PDF both somewhat compressed now.
1. Numerous other small changes.

### Overview of project

 * Phase 1: ( **Finished**) Basic scraper and LaTeX output of API-data and scraped headlines.
 * Phase 2: Now underway: Use SQL to store and manipulate data.
 * Phase 3: Use a web framework to create a GUI for easy management of the application.

---

Past versions:

 * 1.5, 20130313
 * 1.42, 20130304
 * 1.41, 20130228
 * 1.4, 20130227
 * 1.3, 20130225
 * 1.2, 20130222
 * 1.1, 20130220
 * 1.0, 20130219
 * 0.4, 20130214
 * 0.3, 20130213
 * 0.2, 20130213
 * 0.1, 20130212
