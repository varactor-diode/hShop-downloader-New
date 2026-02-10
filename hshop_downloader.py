import os, re, logging, time, argparse
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from time import sleep

# Configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Setup Download Directory using Absolute Pathing
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloads")
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

def get_driver():
    options = uc.ChromeOptions()
    driver = uc.Chrome(options=options, version_main=144)
    # Enforce the download directory via CDP
    driver.execute_cdp_cmd("Page.setDownloadBehavior", {
        "behavior": "allow", "downloadPath": DOWNLOAD_DIR
    })
    return driver

def is_already_downloaded(game_id):
    """Check for the Title ID fingerprint to prevent duplicates."""
    if not os.path.exists(DOWNLOAD_DIR): return False
    for filename in os.listdir(DOWNLOAD_DIR):
        if f"hID-{game_id}" in filename: return True
    return False

def main():
    driver = get_driver()
    try:
        driver.get("https://hshop.erista.me")
        print("\n[!] Solve CAPTCHA and wait for the homepage.")
        input(">>> Press ENTER once the homepage is loaded...")

        # MAPPING TO YOUR PROVIDED URL PARAMETERS
        # sb=name (Sort By Name) | sd=ascending (A-Z)
        sort_query = "&sb=name&sd=ascending" 

        soup = BeautifulSoup(driver.page_source, "html.parser")
        categories = soup.find_all("a", href=re.compile(r'^/c/'))
        
        print("\nAvailable Categories:")
        for i, c in enumerate(categories, 1): print(str(i) + ". " + c.text.strip())
        cat_sel = [int(s.strip()) - 1 for s in input("Select Category IDs: ").split(',') if s.strip().isdigit()]

        for idx in cat_sel:
            driver.get("https://hshop.erista.me" + categories[idx]['href'])
            sleep(2)
            
            sub_els = BeautifulSoup(driver.page_source, "html.parser").find_all("a", class_="list-entry block-link")
            sub_cats = [(e.find("h3").text.strip(), e['href']) for e in sub_els if e.find("h3")]
            
            print("\nSubcategories/Regions:")
            for i, s in enumerate(sub_cats, 1): print(str(i) + ". " + s[0])
            sub_sel = [int(s.strip()) - 1 for s in input("Select Sub IDs: ").split(',') if s.strip().isdigit()]

            for s_idx in sub_sel:
                name, link = sub_cats[s_idx]
                offset = 0
                while True:
                    # Construct URL exactly like your example
                    url = "https://hshop.erista.me" + link + "?count=100&offset=" + str(offset) + sort_query
                    driver.get(url)
                    sleep(2)
                    
                    page_soup = BeautifulSoup(driver.page_source, "html.parser")
                    games = [a['href'] for a in page_soup.find_all('a', href=True) if re.match(r'^/t/\d+$', a['href'])]
                    if not games: break

                    for g_url in games:
                        game_id = g_url.split('/')[-1]
                        
                        if is_already_downloaded(game_id):
                            logging.info("Skipping ID " + game_id + " (Already in Downloads)")
                            continue

                        driver.get("https://hshop.erista.me" + g_url)
                        sleep(1.5)
                        try:
                            dl_btn = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "Direct Download")))
                            dl_btn.click()
                            logging.info("Initiated Download: ID " + game_id)
                            sleep(5) # Delay to ensure Chrome starts the task
                        except Exception as e:
                            logging.warning("Error on ID " + game_id + ": " + str(e))

                    if len(games) < 100: break
                    offset += 100
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
