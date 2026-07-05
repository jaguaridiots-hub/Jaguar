import csv
import os
from datetime import datetime

class TradeJournal:

    def __init__(self):
        self.file = "logs/trades.csv"

        if not os.path.exists(self.file):
            with open(self.file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Date",
                    "Time",
                    "Symbol",
                    "Direction",
                    "Entry",
                    "StopLoss",
                    "TP1",
                    "AI Score",
                    "Confidence",
                    "Probability"
                ])

    def save(self, state, plan):

        with open(self.file, "a", newline="") as f:
            writer = csv.writer(f)

            writer.writerow([
                datetime.now().strftime("%Y-%m-%d"),
                datetime.now().strftime("%H:%M:%S"),
                state.symbol,
                plan["Direction"],
                plan["Entry"],
                plan["StopLoss"],
                plan["TP1"],
                state.ai_score,
                state.confidence,
                state.probability
            ])
