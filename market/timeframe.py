"""
Jaguar Timeframe Model
Version: 0.1.0-alpha
"""


class TimeFrame:

    def __init__(self, name, minutes):
        self.name = name
        self.minutes = minutes

    def show(self):
        print("====== Timeframe ======")
        print("Name    :", self.name)
        print("Minutes :", self.minutes)


if __name__ == "__main__":

    tf = TimeFrame("15m", 15)

    tf.show()
