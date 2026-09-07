"""
Jaguar Position Size Calculator
Version 0.1.0-alpha
"""

class PositionSize:

    def __init__(self, capital, risk_percent, stop_loss):
        self.capital = capital
        self.risk_percent = risk_percent
        self.stop_loss = stop_loss

    def calculate(self):

        risk_amount = self.capital * self.risk_percent / 100
        position_size = risk_amount / self.stop_loss

        print("====== Jaguar Position Size ======")
        print()

        print("Capital        :", self.capital)
        print("Risk Percent   :", str(self.risk_percent) + "%")
        print("Stop Loss      :", self.stop_loss)
        print("Risk Amount    :", round(risk_amount, 2))
        print("Position Size  :", round(position_size, 2), "Units")


if __name__ == "__main__":

    PositionSize(
        capital=100000,
        risk_percent=1,
        stop_loss=2.5
    ).calculate()
