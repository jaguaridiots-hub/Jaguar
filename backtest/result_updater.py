import csv
from backtest.live_price import get_price

FILE = "trade_history.csv"

rows = []

with open(FILE, "r") as f:
    reader = csv.DictReader(f)

    for row in reader:

        if row["Result"] == "OPEN":

            symbol = row["Symbol"]

            entry = float(row["Entry"])
            sl = float(row["StopLoss"])
            tp = float(row["TakeProfit"])

            print("\nChecking:", symbol)

            price = get_price(symbol)

            print("Live Price:", price)

            if price is None:
                print("Unable to fetch live price.")
                rows.append(row)
                continue

            if price >= tp:
                row["Result"] = "WIN"

            elif price <= sl:
                row["Result"] = "LOSS"

            else:
                row["Result"] = "OPEN"

        rows.append(row)

with open(FILE, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print("\nTrade history updated successfully.")
