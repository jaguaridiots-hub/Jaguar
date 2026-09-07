"""
Jaguar Risk Reward Calculator
Version 0.1.0-alpha
"""

class RiskReward:

    def __init__(self, entry, stop, target):
        self.entry = entry
        self.stop = stop
        self.target = target

    def calculate(self):

        risk = abs(self.entry - self.stop)
        reward = abs(self.target - self.entry)
        rr = reward / risk if risk != 0 else 0

        print("====== Jaguar Risk / Reward ======")
        print()

        print("Entry  :", self.entry)
        print("Stop   :", self.stop)
        print("Target :", self.target)
        print()

        print("Risk   :", round(risk, 2))
        print("Reward :", round(reward, 2))
        print("R:R    :", round(rr, 2), ":1")


if __name__ == "__main__":

    RiskReward(
        entry=103.2,
        stop=98.94,
        target=111.72
    ).calculate()
