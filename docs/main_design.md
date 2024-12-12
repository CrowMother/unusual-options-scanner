# OverAll Design

## Design Specifications

- Real-time / near real-time unusual options scanning
- Use of minimal paid API
- Modular structure with focus on database-driven workflows

## Overall Workflow

### 1. Create a List of Stocks Meeting Overall Specifications
- **Purpose:** Identify valid stocks to monitor based on certain criteria such as market cap and trading volume.
- **Steps:**
    - Retrieve stocks from the **Dow Jones** and **Nasdaq** indices using `yfinance` module.
    - Filter stocks using the following thresholds:
        - Minimum Average Volume: **400,000**
        - Minimum Market Capitalization: **1,000,000,000** (1 billion)
    - Check if the `stocks` table in the database is empty:
        - If empty, fetch the filtered stocks and add them to the `stocks` table in the database.
        - If not empty, skip fetching and notify the user.
- **Storage:** All valid stocks are stored in the database under the **`stocks` table**.

### 2. Create Options Chain Table
- **Purpose:** Fetch and store options chain data for all the valid stocks identified in Step 1.
- **Steps:**
    - Delete and recreate the `options` table to ensure a clean slate.
    - Table schema:
        ```sql
        id INTEGER PRIMARY KEY AUTOINCREMENT
        symbol TEXT
        expirationDate TEXT
        strikePrice REAL
        callPut TEXT
        openInterest INTEGER
        lastPullTime TEXT
        ```
    - Check if the `options` table is empty and confirm its state.
    - Fetch options chain data for each stock using the **Schwab API** (`schwab` module).
    - Store the fetched option chain data into the `options` table.
- **Storage:** Option chain data for each stock is stored in the database under the **`options` table**.

### 3. Create Polygon Listeners for Each Option Chain
- **Purpose:** Set up real-time monitoring for unusual market orders.
- **Steps:**
    - Retrieve all option contract symbols from the `options` table.
    - Format each symbol for use with the Polygon API:
        - Remove spaces using `modules.utils.remove_spaces()`.
        - Prepend `T.O:` to each symbol for proper Polygon formatting.
    - Combine formatted symbols into a list to prepare for real-time streaming.
    - Start a WebSocket client using the **Polygon API** (`modules.polygon_api.start_client()`) to monitor market data.

### 4. Upload Relevant Data to Webhook
- **Purpose:** Send filtered data to a webhook address for further processing.
- **Steps:**
    - Identify relevant option data based on real-time monitoring.
    - Pull the required data from the database.
    - Send the data to the webhook address (implementation placeholder in this version).

---

## Modules Used

1. **`my_database` (Database Module):**
   - Handles all database-related operations, such as table creation, deletion, data insertion, and querying.
2. **`yfinance`:**
   - Provides access to stock data from indices like Dow Jones and Nasdaq.
   - Includes methods like `get_dow()` and `get_nasdaq()` for stock retrieval.
   - Allows filtering stocks using volume and market cap thresholds.
3. **`schwab` (Schwab API Integration):**
   - Retrieves options chain data for stocks.
   - Handles filtering and storing option data in the database.
4. **`modules.polygon_api` (Polygon API Integration):**
   - Sets up a WebSocket client to stream real-time market data.
5. **`modules.utils`:**
   - Utility functions for formatting option contract symbols (e.g., `remove_spaces`, `prepend_string`).

---

## Key Functions in the Program

### `main()`
The entry point of the program. It performs the following steps:
1. **Initialize the database:**
    ```python
    database = db.Database()
    ```
2. **Check and populate the `stocks` table:**
    - Fetch Dow Jones and Nasdaq stocks.
    - Filter based on average volume and market capitalization.
3. **Create and populate the `options` table:**
    - Fetch options chain data using the Schwab API.
    - Store the data in the database.
4. **Format option contracts for Polygon API:**
    - Clean and prepare option symbols for real-time streaming.
5. **Start the Polygon WebSocket client:**
    - Monitor real-time market orders.

---

## Summary
This program performs real-time unusual options scanning using a modular design. It combines data from **YFinance** for stock filtering, **Schwab** for options chain retrieval, and **Polygon API** for real-time market data monitoring. The results are stored in a database for further analysis and sent to a webhook endpoint for additional processing.
