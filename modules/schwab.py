import schwabdev
import datetime
from tenacity import retry, stop_after_attempt, wait_exponential
import concurrent.futures


from modules import utils

client = schwabdev.Client(utils.get_secret("SCHWAB_APP_KEY"), utils.get_secret("SCHWAB_APP_SECRET"))


@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=10, max=30))
def get_option_chain_data(symbol):
    try:
        print(f"Processing: {symbol}")
        response = client.option_chains(symbol)
        if response.status_code == 200:
            # Parse the JSON content
            orders = response.json()
            return orders
        else:
            print(f"Error {response.status_code} for {symbol}")
            return None
    except Exception as e:
        print(f"Error processing {symbol}: {e}")
        raise  # Allow retry to handle errors


def get_one_option_chains(stock):
    """
    Retrieves option chain data for a list of stocks using the Schwab API.

    Args:
        stocks (list): List of stock symbols

    Returns:
        dict: Dictionary containing option chain data for the first successful stock
    """
    print("Getting option chain data for stocks...")
    try:
        result = get_option_chain_data(stock)
        if result:
            print(f"Completed: {stock}")
            return result
    except Exception as e:
        print(f"Error for {stock}: {e}")

    print("No valid option chain data found.")
    return None

def store_option_chain_data(option_chain_data, db):
    """
    Store all option chain data (calls and puts) into the database with a bulk insert.
    """
    # Extract call and put expiration maps
    call_expiration = option_chain_data['callExpDateMap']
    put_expiration = option_chain_data['putExpDateMap']

    # Collect all option chain records for bulk insert
    all_option_data = []
    all_option_data.extend(pull_sub_data(call_expiration))
    all_option_data.extend(pull_sub_data(put_expiration))

    # Bulk insert into database
    db.bulk_add_chain(all_option_data)


def pull_sub_data(expirations):
    """
    Extract all option chain data for a given expiration map.

    :param expirations: The option expiration map (calls or puts)
    :return: A list of records for bulk insertion
    """
    all_data = []  # List to store all records

    for expiration in expirations.items():
        strikes = expiration[1]
        for strike in strikes.items():
            strike_price = strike[0]
            subData = strike[1][0]

            # Grab all the data needed for the database
            description = subData['description']
            expirationDate = subData['expirationDate']
            openInterest = subData['openInterest']
            lastPullTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            callPut = subData['putCall']
            symbol = subData['symbol']

            symbol = utils.remove_spaces(symbol)

            # Append the record as a tuple or dictionary
            all_data.append((symbol, expirationDate, strike_price, callPut, openInterest, lastPullTime))
    
    return all_data
            



if __name__ == "__main__":
    stocks = ["AAPL", "MSFT", "GOOG", "AMZN", "TSLA"]  # Replace with your stock list
    option_chain_results = get_one_option_chains(stocks)
    print("Final Results:")
    print(option_chain_results)