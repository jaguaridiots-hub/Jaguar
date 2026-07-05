"""
Jaguar Stop Loss Engine
Version 0.1.0-alpha
"""

class StopLoss:

    def __init__(self, entry_price, atr):
        self.entry = entry_price
        self.atr = atr

    def calculate(self):

        stop = self.entry - (self.atr * 1.5)

        print("====== Jaguar Stop Loss ======")
        print()

        print("Entry Price :", self.entry)
        print("ATR         :", self.atr)
        print("Stop Loss   :", round(stop, 2))


if __name__ == "__main__":

    StopLoss(
        entry_price=103.2,
        atr=2.84
    ).calculate()
