import csv
import os
from datetime import datetime

LOG_FILE = "trade_history.csv"

def log_trade(
    symbol,
    timeframe,
    entry,
    stop_loss,
    take_profit,
    decision,
    probability,
    confidence,
    ai_score,
    smart_money_score
):

    file_exists = os.path.isfile(LOG_FILE)

    with open(LOG_FILE, "a", newline="") as f:

        writer = csv.writer(f)

        if not file_exists:
            writer.writerow([
                "Date",
                "Time",
                "Symbol",
                "Timeframe",
                "Entry",
                "StopLoss",
                "TakeProfit",
                "Decision",
                "Probability",
                "Confidence",
                "AI Score",
                "Smart Money",
                "Result"
            ])

        now = datetime.now()

        writer.writerow([
            now.strftime("%Y-%m-%d"),
            now.strftime("%H:%M:%S"),
            symbol,
            timeframe,
            entry,
            stop_loss,
            take_profit,
            decision,
            probability,
            confidence,
            ai_score,
            smart_money_score,
            "OPEN"
        ])

    print("Trade saved successfully.")
