import requests
import time
import json
import re

# --- Configuration ---
URL = "https://polymarket.com/"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}
MIN_PRICE_THRESHOLD = 0.05
MAX_PRICE_THRESHOLD = 0.95
EXPIRATION_WINDOW_SECONDS = 2 * 60 * 60

def is_profitable(market):
    if not market.get("outcomePrices"):
        return False
    prices = [float(p['price']) for p in market['outcomePrices']]
    return all(MIN_PRICE_THRESHOLD < price < MAX_PRICE_THRESHOLD for price in prices)

def is_expiring_soon(market):
    expiration_ts = market.get("expirationTimestamp")
    if not expiration_ts:
        return False
    current_ts = int(time.time())
    return current_ts < int(expiration_ts) <= (current_ts + EXPIRATION_WINDOW_SECONDS)

def fetch_and_filter_markets():
    try:
        response = requests.get(URL, headers=HEADERS)
        response.raise_for_status()
        html_content = response.text

        match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html_content)
        if not match:
            print("Could not find __NEXT_DATA__ script tag in HTML. Scraping failed.")
            return

        data = json.loads(match.group(1))
        # This path might change, but it's the most likely one based on Next.js structure
        all_markets = data.get("props", {}).get("pageProps", {}).get("initialState", {}).get("markets", {})
        
        if not all_markets:
            print("Could not retrieve market data from embedded JSON.")
            return

        # The markets are in a dictionary, we need the values
        market_list = list(all_markets.values())

        expiring_markets = [m for m in market_list if is_expiring_soon(m)]
        profitable_expiring_markets = [m for m in expiring_markets if is_profitable(m)]

        if not profitable_expiring_markets:
            print("No profitable markets found expiring in the next 2 hours.")
            return

        print("📈 Polymarket - Expiring Soon (via Scraping):\n")
        for market in profitable_expiring_markets:
            question = market['question']
            slug = market['slug']
            link = f"https://polymarket.com/event/{slug}"
            print(f"- [{question}]({link})")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching page: {e}")
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as e:
        print(f"Error parsing data: {e}")

if __name__ == "__main__":
    fetch_and_filter_markets()
