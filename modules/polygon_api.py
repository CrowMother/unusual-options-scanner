from polygon import WebSocketClient
from polygon.websocket.models import WebSocketMessage, Market
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

import modules
from modules.utils import app

# Initialize WebSocket client
client = WebSocketClient(modules.utils.get_secret("POLYGON_API_KEY"), feed=modules.utils.get_secret("POLYGON_FEED"), market=Market.Options)

# Initialize database and fetch tickers
database = modules.my_database.Database()
TICKERS = database.get_all_symbols()

# Thread pool for concurrent message processing
executor = ThreadPoolExecutor(max_workers=int(modules.utils.get_secret("MAX_CONCURRENT_REQUESTS")))  # Adjust max_workers for your CPU capacity and workload


#initialize constants
MIN_PRICE = int(modules.utils.get_secret("MINIMUM_PRICE"))
MIN_SIZE = int(modules.utils.get_secret("MINIMUM_SIZE"))

def process_message(msg: WebSocketMessage):
    """
    Function to process an individual message.
    """
    try:
        database_thread = modules.my_database.Database()
        # print(f"Processing Message: {msg}")

        # Extract and validate symbol
        symbol_split = msg.symbol.split(":")[1]
        symbol = modules.utils.extract_symbol(symbol_split)
        # run through list of filters
        if filter_message(msg, symbol, symbol_split, database_thread):


            open_interest = database_thread.get_open_interest(symbol_split)

                # Format data into a JSON object
            with app.app_context():
                data = modules.utils.jsonify_data(
                    msg.price,
                    msg.size,
                    msg.timestamp,
                    symbol,
                    open_interest,
                    msg.symbol
                )

                # Send JSON data to webhook
                try:
                    json.loads(json.dumps(data))
                except json.JSONDecodeError as e:
                    print(f"Invalid JSON: {e}")
                    # handle the error
                else:
                    modules.utils.send_to_webhook(data)
                    print(f"Sent data to webhook for {symbol}")

    except Exception as e:
            print(f"Error processing message: {e}")


def handle_msg(msgs: List[WebSocketMessage]):
    """
    Handles incoming messages concurrently using ThreadPoolExecutor.
    """
    print(f"Received {len(msgs)} messages")

    # Submit all messages to the thread pool for processing
    futures = [executor.submit(process_message, msg) for msg in msgs]

    # Optional: Wait for all futures to complete and handle exceptions
    for future in as_completed(futures):
        try:
            future.result()  # Ensures any exception in the worker thread is raised here
        except Exception as e:
            print(f"Error in thread: {e}")


def start_client():
    """
    Start the Polygon WebSocket client and subscribe to option trades.
    """
    print("Starting Polygon client...")
    # Subscribe to option trades that are within the TICKERS list
    symbols = database.get_all_symbols()
    for symbol in symbols:
        client.subscribe(f"T:{symbol}")
    # client.subscribe("T.*")  # Subscribe to all trades (filtering done in process_message)
    while True:
        client.run(handle_msg)
    


def filter_message(msg, symbol, full_symbol, database_thread):

    if symbol not in TICKERS:
        return False
    if not min_price(msg):
        return False
    if not min_size(full_symbol, database_thread):
        return False
    if not greater_than_open_interest(msg, full_symbol, database_thread):
        return False
    if not within_strike_price_range(msg, symbol, full_symbol, database_thread):
        return False
    

    return True
    

def min_price(msg):
    return (msg.price * msg.size) * 100 >= MIN_PRICE

def min_size(full_symbol, database_thread):
    open_interest = database_thread.get_open_interest(full_symbol)
    return int(open_interest) >= MIN_SIZE

def greater_than_open_interest(msg, full_symbol, database_thread):
    open_interest = database_thread.get_open_interest(full_symbol)
    return open_interest is not None and msg.size > open_interest
    

def within_strike_price_range(msg, symbol, full_symbol, database_thread):
    #split off the first part of the symbol from C or P
    symbol_split = modules.utils.extract_symbol_and_date(full_symbol)
    min, max = database_thread.get_strike_range(symbol_split)
    min_range, max_range = calculate_range(min, max, symbol)
    strike = modules.utils.extract_strike_price(msg.symbol) / 1000

    return min_range <= strike <= max_range


def calculate_range(min_strike, max_strike, symbol):
    """
    Calculates the middle 40% range closest to the current price.

    Args:
        min_strike (float): Minimum strike price.
        max_strike (float): Maximum strike price.
        symbol (str): Stock ticker symbol.

    Returns:
        tuple: Lower and upper strike price range (middle 40%).
    """
    import modules.yfinance as yfinance  # Assuming custom module for yfinance
    
    # Step 1: Get the current price of the stock
    price = yfinance.get_current_price(symbol)
    
    # Step 2: Calculate the 20% delta (half of 40%)
    delta = price * 0.25
    
    # Step 3: Determine the lower and upper bounds of the middle 40%
    lower_bound = price - delta
    upper_bound = price + delta
    
    # Step 4: Ensure the bounds are within the given min and max strike prices
    lower_bound = max(lower_bound, min_strike)
    upper_bound = min(upper_bound, max_strike)
    
    # Print the results
    # print(f"Current Price: {price}")
    # print(f"Middle 50% Range: {lower_bound:.2f} to {upper_bound:.2f}")
    
    return lower_bound, upper_bound



if __name__ == "__main__":
    start_client(("AAPL","MSFT","GOOG","AMZN","TSLA"))
