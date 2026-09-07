"""
Jaguar Candle Model
Version: 0.1.0-alpha
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Candle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

    def show(self):
        print("====== Candle ======")
        print(f"Time   : {self.timestamp}")
        print(f"Open   : {self.open}")
        print(f"High   : {self.high}")
        print(f"Low    : {self.low}")
        print(f"Close  : {self.close}")
        print(f"Volume : {self.volume}")


if __name__ == "__main__":
    candle = Candle(
        timestamp=datetime.now(),
        open=100.0,
        high=105.0,
        low=98.5,
        close=103.2,
        volume=12500,
    )

    candle.show()
