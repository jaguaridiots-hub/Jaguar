"""
Jaguar Take Profit Engine
Version 0.1.0-alpha
"""

class TakeProfit:

    def __init__(self, entry_price, stop_loss, rr=2):
        self.entry = entry_price
        self.stop = stop_loss
        self.rr = rr

    def calculate(self):

        risk = self.entry - self.stop
        target = self.entry + (risk * self.rr)

        print("====== Jaguar Take Profit ======")
        print()

        print("Entry Price :", self.entry)
        print("Stop Loss  :", self.stop)
        print("Risk       :", round(risk, 2))
        print("RR Ratio   :", str(self.rr) + ":1")
        print("Target     :", round(target, 2))


if __name__ == "__main__":

    TakeProfit(
        entry_price=103.2,
        stop_loss=98.94,
        rr=2
    ).calculate()
