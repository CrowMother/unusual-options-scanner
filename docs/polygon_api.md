# Polygon WebSocket Client for Options Trade Filtering and Processing

## Overview

This script establishes a connection to the **Polygon WebSocket API** to subscribe to option trade messages. Incoming messages are processed through various filters, and relevant trades are sent to a webhook for further use. The script leverages concurrency to handle multiple messages efficiently, integrates with a database to fetch symbol data, and calculates strike price ranges dynamically.

---

## Key Features

1. **WebSocket Integration**  
   - Utilizes `polygon` library to subscribe to real-time option trade data.
   - Filters and processes relevant messages based on configurable criteria.

2. **Database Integration**  
   - Retrieves option symbols, open interest, and strike price ranges from a custom database module.

3. **Concurrent Processing**  
   - Processes messages using `ThreadPoolExecutor` to maximize efficiency.

4. **Dynamic Filtering**  
   Messages are filtered based on:
   - Symbol inclusion in a predefined ticker list.
   - Minimum price and size thresholds.
   - Comparison of trade size to open interest.
   - Strike price range based on stock's current price.

5. **Webhook Integration**  
   - Processed and validated messages are sent as JSON data to a webhook.

---

## Code Structure

### 1. **Dependencies**  
The script imports necessary modules:
   - `polygon.websocket` for WebSocket communication.
   - Custom `modules` for database interaction, utilities, and webhook handling.
   - `ThreadPoolExecutor` for concurrent processing.

### 2. **Initialization**  
- A **WebSocket client** is created with API key and feed from a secret manager.  
- Database connection is initialized to fetch all option symbols (`TICKERS`).

### 3. **Message Processing**

**`process_message(msg)`**  
Processes individual WebSocket messages by:
   - Extracting and validating the symbol.
   - Running the message through a series of filters.
   - Fetching open interest for comparisons.
   - Sending the formatted JSON data to a webhook.

### 4. **Message Handling**

**`handle_msg(msgs)`**  
Handles a batch of messages concurrently:
   - Submits messages to a thread pool for processing.
   - Waits for threads to complete while handling exceptions.

### 5. **WebSocket Client Management**

**`start_client()`**  
   - Subscribes to all option trade messages (`T.*` filter).
   - Continuously runs the WebSocket client, passing received messages to `handle_msg`.

### 6. **Message Filtering**

**`filter_message(msg, symbol, full_symbol, database_thread)`**  
Applies multiple filters to determine message relevance:
   - Symbol existence.
   - Minimum trade size and price thresholds.
   - Trade size exceeding open interest.
   - Trade within calculated strike price range.

### 7. **Strike Price Calculation**

**`calculate_range(min_strike, max_strike, symbol)`**  
   - Calculates the middle 40% range around the stock's current price.
   - Ensures the calculated range is bounded within the min/max strike prices.

---

## Filters Used

1. **Minimum Price (`min_price`)**  
   Ensures the trade value (price \* size) exceeds a minimum threshold.

2. **Minimum Size (`min_size`)**  
   Filters trades with sizes below a configurable minimum.

3. **Open Interest Comparison (`greater_than_open_interest`)**  
   Ensures the trade size exceeds the current open interest.

4. **Strike Price Range (`within_strike_price_range`)**  
   Verifies the trade is within the dynamically calculated strike price range.

---

## Configuration

The following parameters are fetched from the secret manager:
- `POLYGON_API_KEY`: API Key for Polygon WebSocket.
- `POLYGON_FEED`: WebSocket feed type (e.g., options).
- `MINIMUM_PRICE`: Minimum trade price threshold.
- `MINIMUM_SIZE`: Minimum trade size threshold.

---

## Execution

To run the script:

```bash
python script_name.py
