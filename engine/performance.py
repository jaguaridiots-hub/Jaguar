import csv
import os

class Performance:

    def summary(self):

        file = "logs/trades.csv"

        if not os.path.exists(file):
            return {
                "Trades": 0,
                "Wins": 0,
                "Losses": 0,
                "WinRate": 0
            }

        with open(file) as f:
            rows = list(csv.DictReader(f))

        trades = len(rows)

        return {
            "Trades": trades,
            "Wins": 0,
            "Losses": 0,
            "WinRate": 0
        }
