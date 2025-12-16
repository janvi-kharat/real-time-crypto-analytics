import sys
import subprocess
import time
import multiprocessing
from ingestion import BinanceIngester
from storage import DataStore
from config import SYMBOLS

def start_ingestion_service():
    """
    Function to run in a separate process.
    Initializes DataStore and BinanceIngester, then keeps running.
    """
    print("Starting Ingestion Service...")
    # Re-initialize store in this process
    store = DataStore()
    ingester = BinanceIngester(SYMBOLS, store)
    ingester.start()
    
    try:
        # Keep the process alive and let the ingester thread do its work
        while True:
            time.sleep(1)
            # Optional: Prune old data periodically here
            if int(time.time()) % 3600 == 0:
                store.cleanup_old_data()
    except KeyboardInterrupt:
        print("Ingestion Service stopping...")
        ingester.stop()
        ingester.join()

if __name__ == "__main__":
    print("Starting Quant Analytics App...")
    
    # 1. Start Ingestion Process
    ingestion_process = multiprocessing.Process(target=start_ingestion_service)
    ingestion_process.daemon = True # Ensure it dies if main process dies hard
    ingestion_process.start()
    
    # Give it a moment to initialize
    time.sleep(2)
    
    # 2. Start Dashboard (Streamlit)
    print("Launching Dashboard...")
    try:
        # Run streamlit as a subprocess
        subprocess.run([sys.executable, "-m", "streamlit", "run", "dashboard.py"])
    except KeyboardInterrupt:
        print("\nStopping Application...")
    finally:
        if ingestion_process.is_alive():
            print("Terminating Ingestion Process...")
            ingestion_process.terminate()
            ingestion_process.join()
        print("Done.")
