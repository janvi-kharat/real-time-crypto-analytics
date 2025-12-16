import websocket
import json
import threading
import time
import sys
from config import SYMBOLS
from storage import DataStore

class BinanceIngester(threading.Thread):
    def __init__(self, symbols, data_store: DataStore):
        super().__init__()
        self.symbols = [s.lower() for s in symbols]
        self.data_store = data_store
        self.running = True
        self.ws = None
        self.reconnect_delay = 5

    def run(self):
        while self.running:
            try:
                # Construct data stream URL
                # Format: wss://fstream.binance.com/stream?streams=<streamName1>/<streamName2>
                # Trade stream name: <symbol>@trade
                streams = "/".join([f"{s}@trade" for s in self.symbols])
                url = f"wss://fstream.binance.com/stream?streams={streams}"
                
                print(f"Connecting to {url}...")
                self.ws = websocket.WebSocketApp(
                    url,
                    on_open=self._on_open,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close
                )
                self.ws.run_forever()
            except Exception as e:
                print(f"Connection error: {e}")
                
            if self.running:
                print(f"Reconnecting in {self.reconnect_delay}s...")
                time.sleep(self.reconnect_delay)

    def stop(self):
        self.running = False
        if self.ws:
            self.ws.close()

    def _on_open(self, ws):
        print("WebSocket connected.")

    def _on_message(self, ws, message):
        try:
            data = json.loads(message)
            # data structure from combined stream: {"stream": "...", "data": {...}}
            if 'data' in data:
                payload = data['data']
                # Payload fields:
                # e: event type, E: event time, s: symbol, p: price, q: quantity, T: trade time, ...
                tick = {
                    'timestamp': payload['T'] / 1000.0, # ms to seconds
                    'symbol': payload['s'],
                    'price': float(payload['p']),
                    'quantity': float(payload['q'])
                }
                self.data_store.store_tick(tick)
        except Exception as e:
            print(f"Error parsing message: {e}")

    def _on_error(self, ws, error):
        print(f"WebSocket error: {error}")

    def _on_close(self, ws, close_status_code, close_msg):
        print("WebSocket connection closed.")

if __name__ == "__main__":
    # Test ingestion
    store = DataStore()
    ingester = BinanceIngester(SYMBOLS, store)
    ingester.start()
    
    try:
        while True:
            time.sleep(5)
            # Print sample stats
            for s in SYMBOLS:
                df = store.get_latest_data(s, 5)
                if not df.empty:
                    print(f"{s}: {df.iloc[-1].to_dict()}")
    except KeyboardInterrupt:
        print("Stopping...")
        ingester.stop()
        ingester.join()
