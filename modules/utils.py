import os
from dotenv import load_dotenv
import logging
import re
from flask import Flask, request, jsonify
import requests

FILE_PATH = ""
app = Flask(__name__)
streamer = None
SERVER_URL = ""


def set_file_path(file_path):
    """
    Sets the file path for the .env file containing the API keys.
    
    Parameters
    ----------
    file_path : str
        The path to the .env file.
    
    Returns
    -------
    bool
        True if the file path is set successfully, False otherwise.
    """
    
    try:
        global FILE_PATH
        FILE_PATH = file_path

    except Exception as e:
        return False
    
    finally:
        return True

def get_secret(key):
    """
    Retrieves a secret from a .env file.

    Parameters
    ----------
    key : str
        The key to look up in the .env file.

    Returns
    -------
    str
        The value associated with the given key if found, None otherwise.

    Raises
    ------
    Exception
        If the key is not found in the .env file.
    """
    try:
        if FILE_PATH == "":
            set_file_path("config/.env")
        load_dotenv(FILE_PATH)
        value = os.getenv(key)
        if value == None:
            #throw error if key not found
            raise Exception ("Key not found / is None")
        return os.getenv(key)

    except Exception as e:
        logging.error(f"Error getting secret from {FILE_PATH}: {e}")
        return None
        
def remove_spaces(string):
    """
    Removes all spaces from a given string.

    Parameters
    ----------
    string : str
        The string to remove spaces from.

    Returns
    -------
    str
        The string with all spaces removed.
    """
    
    return string.replace(" ", "")

def list_to_string(list, delimiter=", "):
    """
    Converts a list of strings into a single string with each element separated by a given delimiter.

    Parameters
    ----------
    list : list
        The list of strings to convert.
    delimiter : str
        The delimiter to use between each string in the list. Defaults to ", " if not provided.

    Returns
    -------
    str
        The string representation of the list with the given delimiter.
    """
    return delimiter.join(list)

def combine_strings(str1, str2, delimiter=", "):
    """
    Combines two strings into one string with a given delimiter.

    Parameters
    ----------
    str1 : str
        The first string to combine.
    str2 : str
        The second string to combine.
    delimiter : str
        The delimiter to use between the two strings. Defaults to ", " if not provided.

    Returns
    -------
    str
        The combined string with the given delimiter.
    """
    return delimiter.join([str1, str2])

def prepend_string(string, prefix):
    """
    Prepends a prefix string to the given string.

    Parameters
    ----------
    string : str
        The string to prepend the prefix to.
    prefix : str
        The prefix to prepend to the given string.

    Returns
    -------
    str
        The string with the prefix prepended.
    """
    return prefix + string

def remove_last_char(string):
    """
    Removes the last character from a given string.

    Parameters
    ----------
    string : str
        The string from which to remove the last character.

    Returns
    -------
    str
        The string with the last character removed.
    """
    return string[:-1]

def remove_numbers(string):
    """
    Removes all numbers from a given string.

    Parameters
    ----------
    string : str
        The string from which to remove numbers.

    Returns
    -------
    str
        The string with all numbers removed.
    """
    return ''.join([i for i in string if not i.isdigit()])

def extract_symbol(option_string: str) -> str:
    """
    Extracts the stock symbol (alphabetic characters) from an option contract string.
    """
    match = re.search(r'[A-Z]+', option_string)
    return match.group(0) if match else None

def send_to_webhook(data):
    """
    Sends the given data to the configured webhook URL.

    :param data: The data to send to the webhook as a JSON serializable object.
    :return: "OK" if the request was successful, "ERROR" if not.
    """

    with app.app_context():
        try:
            global SERVER_URL
            if SERVER_URL == "":
                SERVER_URL = get_secret("SERVER_URL")

            print(f"sending data to: {SERVER_URL}")
            response = requests.post(f"{SERVER_URL}", json=data)  # Remove json.dumps
            response.raise_for_status()  # Handle HTTP errors
            return "OK"
        except requests.exceptions.RequestException as e:
            print(f"Connection with server lost! {str(e)}")
            # internally log the trade data below
            return "ERROR"
        
def jsonify_data(price, size, timestamp, symbol, open_interest, full_symbol):
    """
    Converts the given parameters into a JSON serializable dictionary format.

    Parameters
    ----------
    price : float
        The price of the option trade.
    size : int
        The size of the option trade.
    timestamp : str
        The timestamp of the trade.
    symbol : str
        The symbol of the option contract.
    open_interest : int
        The open interest for the option contract.
    full_symbol : str
        The full symbol identifier of the option contract.

    Returns
    -------
    dict
        A dictionary containing the trade information formatted as JSON.
    """
    data = {
        "price": price,
        "size": size,
        "timestamp": timestamp,
        "symbol": symbol,
        "openInterest": open_interest,
        "fullSymbol": full_symbol
    }
    return data

def extract_symbol_and_date(option_string):
    """
    Extracts the symbol and date (portion before the first 'C' or 'P' after numbers).

    Args:
        option_string (str): The option string to parse.

    Returns:
        str: The extracted symbol and date.
    """
    # Find position of the first number
    first_number = next((i for i, char in enumerate(option_string) if char.isdigit()), None)
    
    # Ensure we start searching for 'C' or 'P' only after the first number
    if first_number is not None:
        first_c_or_p = next((i + first_number for i, char in enumerate(option_string[first_number:]) 
                             if char in ['C', 'P']), None)
        
        # Return the part of the string before 'C' or 'P'
        if first_c_or_p is not None:
            return option_string[:first_c_or_p + 1]
    
    # Return the original string if no match
    return option_string

def extract_strike_price(option_string):
    """
    Extracts the strike price from an option string.

    Args:
        option_string (str): The option string to parse.

    Returns:
        float: The extracted strike price.
    """
    # Find position of the first number
    first_number = next((i for i, char in enumerate(option_string) if char.isdigit()), None)
    
    # Ensure we start searching for 'C' or 'P' only after the first number
    if first_number is not None:
        first_c_or_p = next((i + first_number for i, char in enumerate(option_string[first_number:]) 
                             if char in ['C', 'P']), None)
        
        # Return the part of the string before 'C' or 'P'
        if first_c_or_p is not None:
            return float(option_string[first_c_or_p + 1:])
    
    # Return the original string if no match
    return None

def log_trade_to_file(msg, symbol, full_symbol, database_thread):
    """
    Logs the trade data to a file.

    Parameters
    ----------
    msg : WebSocketMessage
        The WebSocket message containing the trade data.
    symbol : str
        The symbol of the option contract.
    full_symbol : str
        The full symbol identifier of the option contract.
    database_thread : Database
        The database thread object.

    Returns
    -------
    None
    """ 
    with open("trades.txt", "a") as f:
        f.write(f"{msg.price} {msg.size} {msg.timestamp} {symbol} {full_symbol} {database_thread.get_open_interest(full_symbol)}\n")


def build_database_from_file(file_path, database_thread):
    """
    Builds the database from a file of option symbols.

    Parameters
    ----------
    file_path : str
        The path to the file containing the option symbols.
    database_thread : Database
        The database thread object.

    Returns
    -------
    None
    """
    database_thread.create_table("stocks", ["symbol TEXT PRIMARY KEY", "marketCap INTEGER", "averageVolume INTEGER"])

    with open(file_path, "r") as f:
        for line in f:
            symbol = line.strip()
            database_thread.add_stock(symbol)