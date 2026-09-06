"""
Jaguar Gann Square of 9
Version 0.1.0-alpha
"""

import math
from data.market_data import candles


class SquareOf9:
    def __init__(self, price):
        self.price = price

    def calculate(self):
        root = math.sqrt(self.price)

        print("====== Gann Square of 9 ======")
        print("Price       :", round(self.price, 2))
        print("Square Root :", round(root, 4))
        print()

        print("90°  :", round((root + 0.25) ** 2, 2))
        print("180° :", round((root + 0.50) ** 2, 2))
        print("270° :", round((root + 0.75) ** 2, 2))
        print("360° :", round((root + 1.00) ** 2, 2))


if __name__ == "__main__":
    price = candles[-1]["close"]
    SquareOf9(price).calculate()
