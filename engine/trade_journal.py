import os
import csv
from datetime import datetime


class TradeJournal:

    def __init__(self):
        self.file = "logs/trades.csv"

        os.makedirs("logs", exist_ok=True)

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

        # No trade -> don't save
        if not plan:
            return

        if not isinstance(plan, dict):
            return

        if plan.get("Direction") in [None, "", "NO TRADE", "BLOCKED"]:
            return

        with open(self.file, "a", newline="") as f:
            writer = csv.writer(f)

            writer.writerow([
                datetime.now().strftime("%Y-%m-%d"),
                datetime.now().strftime("%H:%M:%S"),
                getattr(state, "symbol", ""),
                plan.get("Direction", "NO TRADE"),
                plan.get("Entry", ""),
                plan.get("StopLoss", ""),
                plan.get("TP1", ""),
                getattr(state, "ai_score", 0),
                getattr(state, "confidence", ""),
                getattr(state, "probability", 0),
            ])
