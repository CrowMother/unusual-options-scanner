from polygon import WebSocketClient
from polygon.websocket.models import WebSocketMessage, Market
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed
import modules
import json

from modules.utils import app

# Initialize WebSocket client
client = WebSocketClient(modules.utils.get_secret("POLYGON_API_KEY"), feed=modules.utils.get_secret("POLYGON_FEED"), market=Market.Options)

# Initialize database and fetch tickers
database = modules.my_database.Database()
TICKERS = database.get_all_symbols()

# Thread pool for concurrent message processing
executor = ThreadPoolExecutor(max_workers=10)  # Adjust max_workers for your CPU capacity and workload


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
    client.subscribe("T.*")  # Subscribe to all trades (filtering done in process_message)
    while True:
        client.run(handle_msg)
    


def filter_message(msg, symbol, full_symbol, database_thread):

    if symbol not in TICKERS:
        return False
    if not min_size(msg):
        return False
    if not min_price(msg):
        return False
    if not greater_than_open_interest(msg, full_symbol, database_thread):
        return False
    

    return True
    

def min_price(msg):
    minimum_price = int(modules.utils.get_secret("MINIMUM_PRICE"))
    return (msg.price * msg.size) * 100 >= minimum_price

def min_size(msg):
    minimum_size = int(modules.utils.get_secret("MINIMUM_SIZE"))
    return msg.size >= minimum_size

def greater_than_open_interest(msg, full_symbol, database_thread):
    open_interest = database_thread.get_open_interest(full_symbol)
    return open_interest is not None and msg.size > open_interest
    

if __name__ == "__main__":
    start_client()
