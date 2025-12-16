# Quant Analytics Dashboard

A real-time trading analytics application connecting to Binance Futures WebSocket.

## Architecture

The application follows a modular architecture:

1.  **Ingestion (`ingestion.py`)**: Connects to Binance WebSocket (`wss://fstream.binance.com`) and subscribes to trade streams for BTCUSDT and ETHUSDT.
2.  **Storage (`storage.py`)**: Uses SQLite (`market_data.db`) to persist tick data. SQLite is chosen for its simplicity and file-based nature, allowing concurrent access from the ingestion process (writer) and dashboard process (reader).
3.  **Analytics (`analytics.py`)**: Contains stateless functions for:
    *   OHLCV Resampling
    *   Log Returns
    *   Hedge Ratio (OLS Regression)
    *   Spread Calculation
    *   Z-Score
    *   Rolling Correlation
4.  **Dashboard (`dashboard.py`)**: A Streamlit application that polls the database, runs analytics on-the-fly, and renders interactive charts using Plotly.
5.  **Entry Point (`app.py`)**: Orchestrates the application by launching the ingestion service as a background process and the Streamlit dashboard as the main interface.

## Setup & Run

1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

2.  Run the application:
    ```bash
    python app.py
    ```

3.  The dashboard will open automatically in your browser (usually http://localhost:8501).

## libraries Used

*   **Streamlit**: Frontend dashboard.
*   **Pandas**: Data manipulation and resampling.
*   **NumPy**: Numerical operations.
*   **Statsmodels**: OLS regression for Hedge Ratio.
*   **Plotly**: Interactive charting.
*   **Websocket-client**: Real-time data connection.
*   **SQLite3**: Local data storage.

## Extensions

*   **New Analytics**: Add functions to `analytics.py` (e.g., RSI, Bollinger Bands).
*   **New Symbols**: Update `SYMBOLS` in `config.py`.
*   **Production**: Move from SQLite to TimescaleDB or InfluxDB for higher throughput. Use a message queue (Redis/Kafka) between ingestion and storage.
