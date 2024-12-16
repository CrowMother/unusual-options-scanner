import sqlite3
import pandas as pd
import yfinance as yf
from yahoo_fin import stock_info as si
import datetime
import threading


class Database:
    def __init__(self):
        """
        Initializes a new instance of the Database class, establishing a connection to the SQLite database 
        and setting up the required tables if they do not already exist. The 'stocks' table stores stock 
        symbols along with their market capitalization and average trading volume. The 'options' table 
        stores option chain data including a unique identifier, symbol, expiration date, strike price, 
        call/put designation, open interest, and the last pull time.
        """
        self.conn = sqlite3.connect('database.db')
        self.cursor = self.conn.cursor()

        #create first table to store stock symbols, market cap, and average volume
        self.create_table("stocks", ["symbol TEXT PRIMARY KEY", "marketCap INTEGER", "averageVolume INTEGER"])

        #create second table to store option chain data(unique id, symbol, expiration date, strike price, call/put, open interest, last pull time)
        self.create_table("options", ["id INTEGER PRIMARY KEY AUTOINCREMENT", "symbol TEXT", "expirationDate TEXT", "strikePrice REAL", "callPut TEXT", "openInterest INTEGER", "lastPullTime DATE"]) 
        self.conn.commit()


    def add_stock(self, symbol):
        #check if stock already exists in database
        """
        Adds a stock to the 'stocks' table if it does not already exist.

        Args:
            symbol (str): Stock symbol to be added.

        Returns:
            None
        """
        self.cursor.execute('SELECT * FROM stocks WHERE symbol = ?', (symbol,))
        if self.cursor.fetchone():
            return
        self.cursor.execute('INSERT INTO stocks (symbol) VALUES (?)', (symbol,))
        self.conn.commit()

    def is_stocks_table_empty(self):
        """Returns True if the 'stocks' table is empty, False otherwise."""
        self.cursor.execute('SELECT COUNT(*) FROM stocks')
        count = self.cursor.fetchone()[0]
        return count == 0
    
    def is_options_table_empty(self):
        """Returns True if the 'options' table is empty, False otherwise."""
        self.cursor.execute('SELECT COUNT(*) FROM options')
        count = self.cursor.fetchone()[0]
        return count == 0
    
    def get_stocks(self):
        """Returns a list of all stock symbols in the 'stocks' table."""
        self.cursor.execute('SELECT symbol FROM stocks')
        return [row[0] for row in self.cursor.fetchall()]
    

    def add_chain(self, symbol, expirationDate, strike_price, callPut, openInterest, lastPullTime):
        # Single insert (for legacy purposes)
        """
        Single insert of option chain data into the database. Automatically adds the current timestamp.

        :param symbol: Stock symbol
        :param expirationDate: Expiration date
        :param strike_price: Strike price
        :param callPut: Call/Put designation
        :param openInterest: Open interest
        :param lastPullTime: Last data pull timestamp
        """
        self.cursor.execute(
            "INSERT INTO options VALUES (?, ?, ?, ?, ?, ?)",
            (symbol, expirationDate, strike_price, callPut, openInterest, lastPullTime)
        )
        self.connection.commit()

    def bulk_add_chain(self, data):
        """
        Bulk inserts option chain data into the database. Adds the current timestamp automatically.

        :param data: List of tuples containing (symbol, expirationDate, strikePrice, callPut, openInterest).
        """
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Ensure exactly 6 values per row (append the current time)
        data_with_time = [(record[0], record[1], record[2], record[3], record[4], current_time) for record in data]

        # Perform bulk insert
        self.cursor.executemany(
            "INSERT INTO options (symbol, expirationDate, strikePrice, callPut, openInterest, lastPullTime) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            data_with_time
        )
        self.conn.commit()
        print(f"Inserted {len(data)} records with the current timestamp: {current_time}.")

    def delete_table(self, table_name):
        """Deletes a table from the database.

        :param table_name: Name of the table to be deleted.
        """
        self.cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        self.conn.commit()

    def create_table(self, table_name, columns):
        """Creates a table in the database with the given name and columns.

        :param table_name: Name of the table to be created.
        :param columns: List of column definitions (e.g., ['id INTEGER PRIMARY KEY', 'name TEXT']).
        """
        self.cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(columns)})")
        self.conn.commit()

    def get_all_symbols(self):
        """
        Returns a list of all stock symbols and their corresponding option IDs in the database.

        Returns:
            List of strings in the format 'symbol id'
        """
        self.cursor.execute("SELECT symbol, id FROM options")
        return [f"{row[0]} {row[1]}" for row in self.cursor.fetchall()]

    def get_all_symbols(self):
        """
        Returns a list of all stock symbols in the database.

        Returns:
            List of strings (stock symbols)
        """
        self.cursor.execute("SELECT symbol, symbol FROM stocks")
        return [row[0] for row in self.cursor.fetchall()]
    
    def get_open_interest(self, symbol):
        """
        Retrieves the open interest for the given stock symbol from the database.

        Args:
            symbol (str): Stock symbol to query.

        Returns:
            int: Open interest value, or None if no record is found.

        Raises:
            ValueError: If the symbol is not a string.
        """
        if not isinstance(symbol, str):
            raise ValueError(f"Expected symbol as str, got {type(symbol)}")
        
        #print(f"Querying for symbol: {symbol}")  # Debugging
        try:
            self.cursor.execute("SELECT openInterest FROM options WHERE symbol = ?", (symbol,))
            result = self.cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"Error during database query: {e}")
            return None

    def get_strike_range(self, symbol):
        """
        Retrieves the minimum and maximum strike prices for a given stock symbol.

        Args:
            symbol (str): The stock symbol to query.

        Returns:
            tuple: A tuple containing (min_strikePrice, max_strikePrice), or (None, None) if no data exists.
        """
        try:
            # Execute the SQL query to get min and max strikePrice
            self.cursor.execute(
                "SELECT MIN(strikePrice), MAX(strikePrice) FROM options WHERE symbol LIKE ?",
                (f"%{symbol}%",)
            )
            result = self.cursor.fetchone()
            
            # Check if result is None (no data)
            if result is None or (result[0] is None and result[1] is None):
                return None, None
            
            return result  # (min_strikePrice, max_strikePrice)
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return None, None
        except Exception as e:
            print(f"Error: {e}")
            return None, None

