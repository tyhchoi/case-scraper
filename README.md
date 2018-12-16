# case-scraper
Tennessee has several counties with websites that offer a free search engine to find public records of civil, criminal and traffic cases. A case is recorded in a counties’ database when a person is suspected of a crime.

We scrape the website for all cases in order to check if people are eligible for expungement, which is where their criminal record is cleared.

## How to Run
1. install python3
2. install selenium through pip
3. install chrome driver for selenium
4. run using the command: `python tn_montgomery_scraper.py > scraper_log.log 2>&1&`
