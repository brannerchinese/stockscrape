stockscrape
===========

**Version**: 0.4, 20130214

**Author**: David Prager Branner


Goal
----
To explore web scraping using the headline news service on (finance.yahoo.com).

Principal Contents
------------------

stockscrape32.py: Version for Python 3.2 only.

OUTPUT: where output file, stock_report.tex is saved. Note that this file needs to be compiled with LaTeX in order to be usable.

CODE: contains .tex templates for beginning and end of output file.

DATA: contains .txt file of stock tickers to be looked up, one per line.

PREVIOUS_VERSIONS: previous versions will be stored here with date appended, but they may not run as is because directory structures have changed. See past commits of the repository for complete working installations of these older versions.

Notes
-----

This version is not a true scraper; it merely downloads individual web pages and uses simple regex to isolate the most recent day's headlines. I intend to use this as a foundation for a true scraper.

New in this version
-------------------
1. Refactored to modularize all major processes, for easier testing and improvement.
1. Main program now runs from top level of directory; input and output files are all in subdirectories.
1. Improved commenting and docstrings.
1. Version for Python 2.7 relegated to PREVIOUS_VERSIONS/ .

---

Past versions:

 * 0.3, 20130213
 * 0.2, 20130213
 * 0.1, 20130212
