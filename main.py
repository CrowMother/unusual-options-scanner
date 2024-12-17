from modules import my_database as db
from modules import yfinance
from modules import schwab as s
import modules
import modules.polygon_api

def main():
    """
    The main function is the entry point of the program. It initializes a Database instance, fetches a list of valid Dow Jones stocks with a minimum average volume and market capitalization, and adds them to the database.

    :return: None
    """
    database = db.Database()  # Initialize the Database instance


    #step 1 - get list of valid stocks over the min values

    #check if the database is empty, if it is, fetch and add stocks
    database.delete_table("stocks")
    modules.utils.build_database_from_file("stocks.txt", database)

    if database.is_stocks_table_empty():
        print ("stocks table is empty")
    else:
        print("stocks table is not empty")

    #for testing delete the old table
    database.delete_table("options")
    database.create_table("options", ["id INTEGER PRIMARY KEY AUTOINCREMENT", "symbol TEXT", "expirationDate TEXT", "strikePrice REAL", "callPut TEXT", "openInterest INTEGER", "lastPullTime TEXT"])

    #check if table is empty
    if database.is_options_table_empty():
        print("options table is empty")

    #step 2 get the schwab option chain data
    stocks = database.get_stocks()

    for stock in stocks:
        #get option chain for each stock
        option_chain = s.get_one_option_chains(stock)
        #store each option chain
        s.store_option_chain_data(option_chain, database)

    option_chain = ""
    stocks = ""

    #step 3 create polygon listeners for each option chain in the database

    #step 3.1 pull the option symbol from database
    option_contracts = database.get_all_symbols()

    contracts_string = []
    #step 3.2 format the option contract for polygon listener
    for contract in option_contracts:
        # contract = modules.utils.remove_last_char(contract)
        contract = modules.utils.remove_spaces(contract)
        contract = modules.utils.prepend_string(contract, "T.O:")

        #combine into a string
        contracts_string.append(str(contract))


    #Start websocket to get all market orders then filter out the ones that I am looking for
    modules.polygon_api.start_client()
    


if __name__ == "__main__":
    main()