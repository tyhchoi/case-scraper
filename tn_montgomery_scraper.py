import logging
from time import sleep
from selenium import webdriver
from itertools import product
import csv
from random import random
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException

from fake_useragent import UserAgent

# setup logger configuration
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)-25s %(levelname)-7s %(filename)-30s %(funcName)-45s %(lineno)-4s %(message)-8s')
logger = logging.getLogger(__name__)

options = Options()
user_agent = UserAgent()

"""
use this sleep so you see visually see the changes in the browser as it's automated; you can set it to 0 to run
the script as fast as possible
"""
sleep_seconds = 0


def main():
    logger.info("setup Selenium driver given its location on my computer...")
    browser = implement_new_user_agent()

    logger.info("instantiate object to use methods from ActionChains which involve mouse clicks")
    actions = ActionChains(browser)

    navigate_to_court_records_search_engine(browser, actions)

    # BREAKS HERE; immediately blocked on TOU page

    sleep(sleep_seconds + (2 * random()))
    two_letter_combos = create_list_of_search_engine_queries()

    with open('sc_case_details.csv', mode='w') as sc_case_details:
        fieldnames = ['Name', 'Role', 'Case Number', 'Filing Date', 'Status', 'Status Date', 'TCA Code', 'TCA Desc', 'Violation Date', 'Disposition Date', 'Disposition Type']
        writer_object = csv.DictWriter(sc_case_details, fieldnames=fieldnames)

        logger.info("loop through all items in two_letter_combos...")
        for two_letter_combo in two_letter_combos[0:1]:
            total_cases = []
            make_search_query(browser, two_letter_combo)

            logger.info("scrape the page for {0}...".format(two_letter_combo))
            if (not empty_page(browser)):
                while True:
                    cases = scrape_page(browser)
                    total_cases += cases
                    try:
                        next_page(browser)
                    except NoSuchElementException:
                        logger.info("end of results...")
                        break

            logger.info("writing cases for {0} to csv...".format(two_letter_combo))
            writer_object.writeheader()
            for case in total_cases:
                charges = case['Charges']
                for charge in charges:
                    new_case = case.copy()
                    new_case.update(charge)
                    del new_case['Charges']
                    writer_object.writerow(new_case)

            logger.info("sleep a bit...")
            sleep(random()*4)

        logger.info("quit browser...")
        browser.quit()


def navigate_to_court_records_search_engine(browser, actions):
    """
    Uses Selenium to open browser, navigate to SC County site, accept disclaimer
    :param browser: Selenium driver
    :return: None
    """
    logger.info("open empty browser")
    browser.maximize_window()
    logger.info("sleep...")
    sleep(sleep_seconds + (2 * random()))

    montgomery_county_search = 'https://montgomery.tncrtinfo.com/crCaseList.aspx'

    logger.info("navigate to the page: {0}".format(montgomery_county_search))
    browser.get(montgomery_county_search)

    sleep(sleep_seconds + (2 * random()))
    return None


def create_list_of_search_engine_queries():
    """
    Generate Python list of all three letter combos for the letters in the alphabet
    :return: three_letter_combos
    """
    logger.info("generate the cartesian product of all 2 letter combos in the alphabet...")
    logger.info("therefore, we can search aa then ab then ac and so forth...")

    logger.info("use the itertools product method to generate a list of tuples - each tuple containing 2 letters")
    letters_tuple_combos = list(product('ABCDEFGHIJKLMNOPQRSTUVWXYZ', repeat=2))
    logger.info("first 2 tuple combos: {0}".format(letters_tuple_combos[0:3]))

    logger.info("join those three strings in each combo in a single string and add them to a list")
    two_letter_combos = ["".join(tuple_val) for tuple_val in letters_tuple_combos]
    logger.info("first 2 letter combos in three_letter_combos: {0}".format(two_letter_combos[0:3]))

    return two_letter_combos


def make_search_query(browser, two_letter_combo_start):
    """
    Sends a search query using 2 letter combinations
    :param browser: chrome driver
    :param two_letter_combo_start: 2 letter combination for search query
    :return: None
    """
    logger.info("find last name text box input...")
    last_name_text_box = browser.find_element_by_name('ctl00$ctl00$cphContent$cphSelectionCriteria$txtPartyLastName')
    logger.info("type in the value {0} into the last name text box input".format(two_letter_combo_start))
    last_name_text_box.send_keys(two_letter_combo_start)
    sleep(sleep_seconds + (2 * random()))

    logger.info("find the search button...")
    search_button = browser.find_element_by_name('ctl00$ctl00$cphContent$cphSelectionCriteria$cmdFindNow')
    logger.info("click the search button to execute our search query...")
    search_button.click()
    sleep(sleep_seconds + (2 * random()))
    return None


def scrape_page(browser):
    """
    Scrapes the page and get each case data
    :param browser: Selenium driver
    :return: array of case objects
    """
    table = browser.find_element_by_xpath("//*[@id='ctl00_ctl00_cphContent_cphSearchResults_gridSearch']")
    rows = table.find_elements_by_xpath(".//tbody/tr[not(contains(@class,'searchListHeader'))]")
    case_list = []
    for row in rows:
        link = row.find_element_by_xpath('.//td[2]/a')
        name = link.get_attribute('text')
        logger.info("get data for {0}".format(name))
        role = row.find_element_by_xpath('.//td[3]').get_attribute('innerHTML')
        case_number = row.find_element_by_xpath('.//td[4]').get_attribute('innerHTML')
        filing_date = row.find_element_by_xpath('.//td[6]').get_attribute('innerHTML')
        status = row.find_element_by_xpath('.//td[7]').get_attribute('innerHTML')
        status_date = row.find_element_by_xpath('.//td[8]').get_attribute('innerHTML')

        if role == 'Defendant':
            logger.info("switch tab for charges...")
            ActionChains(browser).key_down(Keys.COMMAND).click(link).key_up(Keys.COMMAND).perform()
            browser.switch_to.window(browser.window_handles[1])
            charges_list = scrape_inner_page(browser)
            case = {
                'Name': name,
                'Role': role,
                'Case Number': case_number,
                'Filing Date': filing_date,
                'Status': status,
                'Status Date': status_date,
                'Charges': charges_list
            }
            case_list.append(case)

    return case_list


def scrape_inner_page(browser):
    """
    Gets the charge data for each case
    :param browser: Selenium driver
    :return: array of charge objects
    """
    charges_tab = browser.find_element_by_xpath("//*[@id='ctl00_ctl00_cphContent_cphTabbedBar_ultab']/li[2]/a")
    charges_tab.click()
    sleep(sleep_seconds + (4 * random()))
    table = browser.find_element_by_xpath("//*[@id='ctl00_ctl00_cphContent_cphFormDetail_gridcharges']")
    rows = table.find_elements_by_xpath(".//tbody/tr[not(contains(@class,'searchListHeader'))]")
    charges_list = []
    for row in rows:
        logger.info("get data for every charge...")
        tca_code = row.find_element_by_xpath('.//td[3]').get_attribute('innerHTML')
        tca_desc = row.find_element_by_xpath('.//td[4]').get_attribute('innerHTML')
        violation_date = row.find_element_by_xpath('.//td[6]').get_attribute('innerHTML')
        disposition_date = row.find_element_by_xpath('.//td[7]').get_attribute('innerHTML')
        disposition_type = row.find_element_by_xpath('.//td[8]').get_attribute('innerHTML')
        charges = {
            'TCA Code': tca_code,
            'TCA Desc': tca_desc,
            'Violation Date': violation_date,
            'Disposition Date': disposition_date,
            'Disposition Type': disposition_type
            }
        charges_list.append(charges)

    logger.info("close tab and switch back...")
    browser.close()
    browser.switch_to.window(browser.window_handles[0])
    return charges_list


def empty_page(browser):
    """
    Checks if there are results
    :param browser: Selenium driver
    :return: True or False
    """
    table = browser.find_element_by_xpath("//*[@id='ctl00_ctl00_cphContent_cphSearchResults_gridSearch']")
    rows = table.find_elements_by_xpath(".//tbody/tr")
    if (len(rows) == 1):
        logger.info("no results found...")
        return True

    return False


def next_page(browser):
    logger.info("go to the next page...")
    next_page = browser.find_element_by_name('ctl00$ctl00$cphContent$cphContentPaging$nextpage')
    next_page.click()
    return None


def implement_new_user_agent():
    new_user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36" #user_agent.random
    logger.info("new user agent is: {0}".format(new_user_agent))
    options.add_argument(f'User-Agent={new_user_agent}')
    browser = webdriver.Chrome(chrome_options=options, executable_path='/usr/local/bin/chromedriver')
    return browser


if __name__ == "__main__":
    main()
