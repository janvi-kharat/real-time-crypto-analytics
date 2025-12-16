# Project Guide: Real-Time Crypto Analytics

## 1. What is the project?
This is a **Real-Time Trading Analytics Application**. It monitors the prices of two cryptocurrency assets (Bitcoin and Ethereum) instantly as they change. It uses a mathematical strategy called "Pairs Trading" to find potential opportunities to buy or sell.

## 2. What are we doing in this project?
1.  **Ingesting Data**: We connect to Binance (a crypto exchange) to get live price updates for BTCUSDT and ETHUSDT.
2.  **Storing Data**: We save every single price update (tick) into a local database.
3.  **Analyzing Data**: We compare the prices of BTC and ETH to see if they are moving together or drifting apart.
4.  **Displaying Results**: We show charts and alerts on a dashboard so a trader can see when to trade.

## 3. What is the logic/approach?
We use a **Pairs Trading (Statistical Arbitrage)** approach.
*   **Concept**: BTC and ETH usually move together. If Bitcoin goes up, Ethereum usually goes up.
*   **The Logic**: 
    *   We calculate the "Spread" (the difference between their prices, adjusted by a ratio).
    *   We calculate a "Z-Score" (how extreme the current spread is compared to the average).
    *   **Buy Signal**: If the spread is too low (Z-Score < -2), it means one asset is too cheap compared to the other.
    *   **Sell Signal**: If the spread is too high (Z-Score > 2), it means one asset is too expensive.

## 4. Codes Folder Structure
Here is how the project files are organized:

```text
GenCap/
├── app.py              # The main starter script (Run this!)
├── config.py           # Settings (Symbols like BTCUSDT, ETHUSDT)
├── dashboard.py        # The website/interface code (Streamlit)
├── ingestion.py        # The code that connects to Binance
├── storage.py          # The database manager
├── analytics.py        # The math/statistics formulas
├── requirements.txt    # List of libraries to install
└── README.md           # Technical documentation
```

## 5. Tech Stack (Tools Used)
*   **Language**: Python (Logic)
*   **Frontend**: Streamlit (The Dashboard UI)
*   **Database**: SQLite (Simple local file database)
*   **Live Data**: Websockets (For instant data streaming)
*   **Charts**: Plotly (Interactive graphs)
*   **Math**: Pandas & Statsmodels (For calculations)

## 6. How do you fetch real-time data?
*   We use a **WebSocket connection** in `ingestion.py`.
*   Unlike a standard web request (which asks for data once), a WebSocket keeps a phone line open with Binance.
*   Binance sends us a message the millisecond a trade happens.
*   **Key Code**: `websocket.WebSocketApp("wss://fstream.binance.com/...")`

## 7. How are you storing data?
*   We use **SQLite**, which stores data in a file named `market_data.db`.
*   Every time we receive a price, `storage.py` writes a new row to the database with the Timestamp, Symbol (BTC/ETH), Price, and Quantity.

## 8. Main Functions Used
*   **`store_tick(tick)`** (in `storage.py`): Saves a new price to the database.
*   **`get_data_since(timestamp)`** (in `storage.py`): Reads data from the database for the charts.
*   **`resample_ohlcv(df)`** (in `analytics.py`): Turns thousands of raw ticks into nice 1-second or 1-minute bars (Open, High, Low, Close).
*   **`calculate_spread_and_zscore(...)`** (in `analytics.py`): The brain of the strategy. It runs the math to find trading signals.

## 9. What input should I give on the dashboard?
On the left sidebar, you can control:
*   **Refresh Rate**: How often the screen updates (e.g., every 1 second).
*   **Timeframe**: How to group data (e.g., 1 Second bars or 1 Minute bars).
*   **Rolling Window**: How much past data to use for the average (e.g., use the last 60 data points).
*   **Z-Score Threshold**: The sensitivity of alerts (e.g., 2.0). Lower numbers give more frequent alerts.

## 10. What output am I getting?
*   **Price Chart**: Shows BTC and ETH prices side-by-side.
*   **Spread Chart**: Shows the gap between the two assets.
*   **Z-Score Chart**: Shows the trading signal.
*   **Alerts**: 
    *   🚨 **RED**: Signal to Sell.
    *   🟢 **GREEN**: Signal to Buy.
    *   🔵 **BLUE**: Market is normal (do nothing).
*   **Statistics**: Live numbers for correlation, beta (hedge ratio), and current prices.

## 11. How are the connections made?
It's a two-part system running at the same time:

**Part 1: The "Listener" (Background)**
1.  **Binance** sends data via WebSocket.
2.  `ingestion.py` catches the data.
3.  `ingestion.py` calls `storage.py` to save it to `market_data.db`.

**Part 2: The "Viewer" (Frontend)**
1.  `dashboard.py` wakes up every 1 second.
2.  It asks `storage.py`: "Give me the data from the last hour."
3.  `storage.py` reads `market_data.db` and returns a table.
4.  `dashboard.py` sends this table to `analytics.py` to do the math.
5.  `dashboard.py` draws the charts on your screen.

**`app.py`** is the manager. When you run `app.py`, it starts Part 1, waits 2 seconds, and then starts Part 2.

## 12. Which functions perform which function?
*   `ingestion.py` -> **BinanceIngester.run()**:Connects to the internet and listens for trades.
*   `storage.py` -> **DataStore.store_tick()**: Writes data to the hard drive.
*   `storage.py` -> **DataStore.get_data_since()**: Reads data for the dashboard.
*   `analytics.py` -> **calculate_spread_and_zscore()**: Calculates the "Spread" line and "Z-Score" line you see on the charts.
*   `dashboard.py` -> **st.plotly_chart()**: Draws the actual visual graphs.
