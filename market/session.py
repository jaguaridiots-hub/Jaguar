"""
Jaguar Market Session
Version: 0.1.0-alpha
"""

from datetime import datetime


class MarketSession:

    def __init__(self):
        self.time = datetime.now()

    def show(self):
        hour = self.time.hour

        if 0 <= hour < 8:
            session = "Sydney"

        elif 8 <= hour < 12:
            session = "Tokyo"

        elif 12 <= hour < 17:
            session = "London"

        elif 17 <= hour < 22:
            session = "New York"

        else:
            session = "Market Closed"

        print("====== Market Session ======")
        print("Time    :", self.time)
        print("Session :", session)


if __name__ == "__main__":
    MarketSession().show()
