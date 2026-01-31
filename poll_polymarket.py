import requests
import time
import json
import re
from datetime import datetime, timezone

# --- Configuration ---
URL = "https://polymarket.com/markets" # Using the main markets page is more reliable
HEADERS_LIST = [
    {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    },
    {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Version/16.5 Safari/605.1.15',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-us',
    }
]
MAX_RETRIES = 3
# --- UPDATED per user request ---
EXPIRATION_WINDOW_SECONDS = 4 * 60 * 60 
MIN_PRICE_THRESHOLD = 0.05
MAX_PRICE_THRESHOLD = 0.95


def is_profitable(market):
    """Check if a market's outcomes are within the profitable range."""
    # This check is now re-enabled
    prices = [float(p['price']) for p in market.get('outcomePrices', []) if 'price' in p]
    if not prices:
        return False
    return all(MIN_PRICE_THRESHOLD < price < MAX_PRICE_THRESHOLD for price in prices)

def is_expiring_soon(market):
    """Check if a market is expiring within the defined window."""
    # The expiration timestamp is correctly named in the __NEXT_DATA__
    expiration_ts = market.get("expirationTimestamp")
    if not expiration_ts:
        return False
    
    try:
        # The timestamp from __NEXT_DATA__ is already a Unix timestamp string
        expiration_ts_int = int(expiration_ts)
        current_ts = int(time.time())
        return current_ts < expiration_ts_int <= (current_ts + EXPIRATION_WINDOW_SECONDS)
    except (ValueError, TypeError):
        return False

def fetch_and_filter_markets():
    """Fetch markets by scraping __NEXT_DATA__ from the HTML, with retries."""
    html_content = ""
    for i in range(MAX_RETRIES):
        try:
            headers = HEADERS_LIST[i % len(HEADERS_LIST)]
            response = requests.get(URL, headers=headers, timeout=15)
            response.raise_for_status()
            
            match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', response.text)
            if match:
                html_content = match.group(1)
                break 
            time.sleep(1) # Wait a second before retrying
        except requests.exceptions.RequestException as e:
            if i == MAX_RETRIES - 1:
                print(f"Error fetching page after {MAX_RETRIES} retries: {e}")
                return
            time.sleep(1)

    if not html_content:
        print("Scraping failed: Could not find __NEXT_DATA__ after multiple retries.")
        return

    try:
        data = json.loads(html_content)
        all_markets = data.get("props", {}).get("pageProps", {}).get("initialState", {}).get("markets", {})
        
        if not all_markets:
            print("Could not retrieve market data from embedded JSON.")
            return

        market_list = list(all_markets.values())

        expiring_markets = [m for m in market_list if is_expiring_soon(m)]
        profitable_expiring_markets = [m for m in expiring_markets if is_profitable(m)]

        if not profitable_expiring_markets:
            # print("No profitable markets found expiring in the next 4 hours.")
            return # Silently exit to avoid spam

        print("🔔 **Polymarket Alerts** 📊\n")
        for i, market in enumerate(profitable_expiring_markets):
            if i > 0:
                print("\n---\n") 

            question = market['question']
            slug = market['slug']
            link = f"https://polymarket.com/event/{slug}"
            
            expiration_ts = int(market.get("expirationTimestamp"))
            end_date_obj = datetime.fromtimestamp(expiration_ts, tz=timezone.utc)
            formatted_date = end_date_obj.strftime("%B %d, %Y %H:%M UTC")
            
            output = (
                f"🎯 **Market Focus:** {question}\n"
                f"📅 **Resolution Date:** {formatted_date}\n"
                f"[Go to Market]({link})"
            )
            print(output)

    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as e:
        print(f"Error parsing data: {e}")

if __name__ == "__main__":
    fetch_and_filter_markets()
