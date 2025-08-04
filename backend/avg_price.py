import re
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def to_fullwidth(s):
    """Convert ASCII letters to fullwidth for price matching."""
    return ''.join(
        chr(ord(c) + 0xFEE0) if '!' <= c <= '~' else c
        for c in s
    )

def get_average_price(card_name_jp):
    """
    Fetch average card price from Toreca by searching with fullwidth Japanese card name.
    Returns the price in JPY as int, or None if not found.
    """
    search_url = f"https://toreca.net/list?game=&name={card_name_jp}"
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(search_url)
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        driver.quit()

        td_elements = soup.select("td.text-end")
        for td in td_elements:
            text = td.get_text(strip=True)
            if "円" in text:
                match = re.search(r"([\d,]+)", text)
                if match:
                    price = int(match.group(1).replace(",", ""))
                    print(f"💴 Found price: ¥{price}")
                    return price
        return None
    except Exception as e:
        print("❌ Selenium scraping error:", e)
        return None

import requests

def convert_jpy_to_twd(jpy):
    try:
        r = requests.get("https://api.exchangerate-api.com/v4/latest/JPY", timeout=10)
        if r.status_code != 200:
            return None
        rate = r.json()["rates"].get("TWD")
        if not rate:
            return None
        return round(jpy * rate, 2)
    except:
        return None

