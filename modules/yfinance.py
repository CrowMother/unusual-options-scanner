import yfinance as yf
from yahoo_fin import stock_info as si
from tenacity import retry, stop_after_attempt, wait_exponential
import concurrent.futures
import logging
import time
from datetime import datetime
from modules import my_database as db

database = db.Database()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

def get_dow():
    return si.tickers_dow()

def get_nasdaq():
    return si.tickers_nasdaq()

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=5, max=10))
def get_current_price(symbol):
    ticker = yf.Ticker(symbol)
    return ticker.history(period="1d").iloc[-1]['Close']

# Retry with exponential backoff for throttling errors
@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=5, max=18))
def filter_by_values(ticker, min_avg_volume, min_market_cap):
    """
    Filters a single ticker based on average volume and market cap.
    """
    try:
        logging.info(f"Processing: {ticker}")
        #sleep program to prevent throttling
        time.sleep(1)
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Extract market cap and average daily volume
        market_cap = info.get('marketCap', 0)
        avg_volume = info.get('averageVolume', 0)

        # Check if the ticker meets the criteria
        if market_cap > min_market_cap and avg_volume > min_avg_volume:
            logging.info(f"Valid: {ticker}, Market Cap: {market_cap}, Avg Volume: {avg_volume}")
            return ticker
    except Exception as e:
        logging.error(f"Error processing {ticker}: {e}")
        raise e  # Ensure retry logic triggers
    return None

def filter_batch(tickers, min_avg_volume=400000, min_market_cap=1000000000):
    """
    Filters a batch of tickers using concurrency with controlled requests.
    """
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        # Submit tasks concurrently without delays
        futures = {executor.submit(filter_by_values, ticker, min_avg_volume, min_market_cap): ticker for ticker in tickers}

        # Process completed futures
        for future in concurrent.futures.as_completed(futures):
            ticker = futures[future]
            try:
                result = future.result()
                if result:  # Append only valid results
                    results.append(result)
            except Exception as e:
                logging.error(f"Exception for {ticker}: {e}")
    
    return results

if __name__ == "__main__":
    tickers = ["AAPL", "MSFT", "GOOG", "AMZN", "TSLA", "INVALID"]  # Replace with a valid list of tickers
    start_time = datetime.now()

    valid_tickers = filter_batch(tickers, min_avg_volume=400000, min_market_cap=1000000000)

    end_time = datetime.now()
    duration = end_time - start_time

    print("\nFiltered Tickers:")
    print(valid_tickers)
    print(f"Execution Time: {duration}")
