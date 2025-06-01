import json
import undetected_chromedriver as uc
import time
from classes.ScrapeMal import MalScraping


def update_mal_info(json_path: str, mal_url: str, driver, identifier: str) -> None:
    mal_data = MalScraping(mal_url, driver).get_info_anime()

    with open(json_path, 'r') as infile:
        all_json_data = json.load(infile)
        infile.close()

        for mal_key, mal_value in mal_data.items():
            all_json_data[identifier]["mal_info"][mal_key] = mal_value

    with open(json_path, 'w') as outfile:
        json.dump(all_json_data, outfile)
        outfile.close()


def get_page_source(url):
    chrome_options = uc.ChromeOptions()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--ignore-urlfetcher-cert-requests')

    driver = uc.Chrome(headless=True, use_subprocess=False, options=chrome_options)
    driver.get(url)
    driver.implicitly_wait(10)

    while "DDoS-Guard" in driver.page_source:
        time.sleep(1)

    page_source = driver.page_source
    driver.quit()

    return page_source
