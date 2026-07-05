"""
Jaguar Market Data Engine
Version: 0.1.0-alpha
"""

from datetime import datetime


class MarketDataEngine:

    def __init__(self):
        self.engine_name = "Jaguar Market Data Engine"
        self.version = "0.1.0-alpha"
        self.connected = False

    def connect(self):
        self.connected = True
        print(f"[{datetime.now()}]")
        print("Market Data Engine Connected")

    def status(self):
        if self.connected:
            print("Status : ONLINE")
        else:
            print("Status : OFFLINE")


if __name__ == "__main__":

    engine = MarketDataEngine()

    engine.connect()

    engine.status()
