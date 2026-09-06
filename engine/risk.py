"""
Jaguar Risk Management Engine
Version 0.1.0-alpha
"""

class RiskManager:

    def __init__(self, capital, risk_percent):
        self.capital = capital
        self.risk = risk_percent

    def calculate(self):

        risk_amount = self.capital * self.risk / 100

        print("====== Jaguar Risk Manager ======")
        print()

        print("Capital        :", self.capital)
        print("Risk Percent   :", str(self.risk) + "%")
        print("Risk Amount    :", round(risk_amount, 2))

if __name__ == "__main__":

    RiskManager(
        capital=100000,
        risk_percent=1
    ).calculate()
