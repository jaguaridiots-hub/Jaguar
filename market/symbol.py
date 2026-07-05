"""
Jaguar Symbol Model
Version: 0.1.0-alpha
"""

from dataclasses import dataclass


@dataclass
class Symbol:
    ticker: str
    exchange: str
    asset_type: str

    def show(self):
        print("====== Symbol ======")
        print(f"Ticker    : {self.ticker}")
        print(f"Exchange  : {self.exchange}")
        print(f"Asset Type: {self.asset_type}")


if __name__ == "__main__":

    btc = Symbol(
        ticker="BTCUSDT",
        exchange="Binance",
        asset_type="Crypto"
    )

    btc.show()
