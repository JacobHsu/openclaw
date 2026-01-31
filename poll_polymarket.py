import requests
import time
import os

# --- Configuration ---
API_ENDPOINT = "https://gamma-api.polymarket.com/query"
# Filter for markets where all outcomes are between 5% and 95%
MIN_PRICE_THRESHOLD = 0.05
MAX_PRICE_THRESHOLD = 0.95
# Filter for markets expiring in the next 2 hours (in seconds)
EXPIRATION_WINDOW_SECONDS = 2 * 60 * 60

# --- GraphQL Query ---
# Note: Added 'expirationTimestamp' to the query
GRAPHQL_QUERY = """
query GetMarkets {
  markets(active: true, closed: false) {
    id
    question
    slug
    expirationTimestamp
    outcomePrices {
      price
    }
  }
}
"""

def is_profitable(market):
    """Check if a market's outcomes are within the profitable range."""
    if not market.get("outcomePrices"):
        return False
    prices = [float(p['price']) for p in market['outcomePrices']]
    return all(MIN_PRICE_THRESHOLD < price < MAX_PRICE_THRESHOLD for price in prices)

def is_expiring_soon(market):
    """Check if a market is expiring within the defined window."""
    expiration_ts = market.get("expirationTimestamp")
    if not expiration_ts:
        return False
    
    current_ts = int(time.time())
    return current_ts < int(expiration_ts) <= (current_ts + EXPIRATION_WINDOW_SECONDS)

def fetch_and_filter_markets():
    """Fetch markets from Polymarket API and print filtered results."""
    try:
        response = requests.post(API_ENDPOINT, json={"query": GRAPHQL_QUERY})
        response.raise_for_status()
        data = response.json()
        
        all_markets = data.get("data", {}).get("markets", [])
        if not all_markets:
            print("Could not retrieve market data.")
            return

        expiring_markets = [m for m in all_markets if is_expiring_soon(m)]
        profitable_expiring_markets = [m for m in expiring_markets if is_profitable(m)]

        if not profitable_expiring_markets:
            print("No profitable markets found expiring in the next 2 hours.")
            return

        print("📈 Polymarket - Expiring Soon:\n")
        for market in profitable_expiring_markets:
            question = market['question']
            slug = market['slug']
            link = f"https://polymarket.com/event/{slug}"
            print(f"- [{question}]({link})")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
    except (KeyError, TypeError, ValueError) as e:
        print(f"Error parsing data: {e}")

if __name__ == "__main__":
    fetch_and_filter_markets()
