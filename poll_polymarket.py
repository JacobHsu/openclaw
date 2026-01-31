import requests
import time
from datetime import datetime, timezone

# --- Configuration ---
API_ENDPOINT = "https://gamma-api.polymarket.com/events"
# Filter for markets where all outcomes are between 5% and 95%
MIN_PRICE_THRESHOLD = 0.05
MAX_PRICE_THRESHOLD = 0.95
# Filter for markets expiring in the next 2 hours (in seconds)
EXPIRATION_WINDOW_SECONDS = 2 * 60 * 60

def parse_price(price_str):
    """Safely convert price string to float."""
    try:
        return float(price_str)
    except (ValueError, TypeError):
        return None

def is_profitable(market):
    """Check if a market's outcomes are within the profitable range."""
    outcome_prices_str = market.get("outcomePrices")
    if not outcome_prices_str:
        return False
    
    try:
        prices = [parse_price(p) for p in json.loads(outcome_prices_str)]
        # Ensure all prices were parsed correctly and are not None
        if any(p is None for p in prices):
            return False
        return all(MIN_PRICE_THRESHOLD < price < MAX_PRICE_THRESHOLD for price in prices)
    except (json.JSONDecodeError, TypeError):
        return False


def is_expiring_soon(market):
    """Check if a market is expiring within the defined window."""
    end_date_str = market.get("endDate")
    if not end_date_str:
        return False
    
    try:
        # Handle different timezone formats from the API
        if end_date_str.endswith('Z'):
            end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
        else:
            end_date = datetime.fromisoformat(end_date_str)
            
        # If the datetime object is naive, assume UTC
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)
            
        expiration_ts = int(end_date.timestamp())
        current_ts = int(time.time())
        
        return current_ts < expiration_ts <= (current_ts + EXPIRATION_WINDOW_SECONDS)
    except ValueError:
        return False

def fetch_and_filter_markets():
    """Fetch markets from Polymarket REST API and print filtered results."""
    try:
        params = {"active": "true", "closed": "false", "limit": "100"}
        response = requests.get(API_ENDPOINT, params=params)
        response.raise_for_status()
        events = response.json()
        
        if not events:
            print("Could not retrieve market data.")
            return

        all_markets = [market for event in events for market in event.get("markets", [])]

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
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as e:
        print(f"Error parsing data: {e}")

if __name__ == "__main__":
    fetch_and_filter_markets()
