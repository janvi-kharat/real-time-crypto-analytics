import sqlite3
import pandas as pd
import threading
import time
from config import DB_PATH, HISTORY_LIMIT_HOURS

class DataStore:
    def __init__(self):
        self.db_path = DB_PATH
        self.lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    timestamp REAL,
                    symbol TEXT,
                    price REAL,
                    quantity REAL
                )
            ''')
            # Index for faster queries
            c.execute('CREATE INDEX IF NOT EXISTS idx_timestamp_symbol ON trades (timestamp, symbol)')
            conn.commit()
            conn.close()

    def store_tick(self, tick: dict):
        """
        Store a single tick.
        Tick format: {'timestamp': float, 'symbol': str, 'price': float, 'quantity': float}
        """
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('INSERT INTO trades (timestamp, symbol, price, quantity) VALUES (?, ?, ?, ?)',
                      (tick['timestamp'], tick['symbol'], tick['price'], tick['quantity']))
            conn.commit()
            conn.close()

    def get_latest_data(self, symbol: str, limit: int = 1000) -> pd.DataFrame:
        """Get latest N trades for a symbol."""
        conn = sqlite3.connect(self.db_path)
        query = f"""
            SELECT timestamp, price, quantity 
            FROM trades 
            WHERE symbol = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        """
        df = pd.read_sql_query(query, conn, params=(symbol, limit))
        conn.close()
        # Sort back to ascending for plotting/analysis
        if not df.empty:
            df = df.sort_values('timestamp').reset_index(drop=True)
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        return df

    def get_data_since(self, symbol: str, since_timestamp: float) -> pd.DataFrame:
        """Get all trades since a timestamp."""
        conn = sqlite3.connect(self.db_path)
        query = """
            SELECT timestamp, price, quantity 
            FROM trades 
            WHERE symbol = ? AND timestamp >= ?
            ORDER BY timestamp ASC
        """
        df = pd.read_sql_query(query, conn, params=(symbol, since_timestamp))
        conn.close()
        if not df.empty:
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        return df
        
    def cleanup_old_data(self):
        """Delete data older than HISTORY_LIMIT_HOURS."""
        cutoff = time.time() - (HISTORY_LIMIT_HOURS * 3600)
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('DELETE FROM trades WHERE timestamp < ?', (cutoff,))
            conn.commit()
            conn.close()
