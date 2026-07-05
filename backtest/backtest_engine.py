import csv

FILE = "trade_history.csv"

wins = 0
losses = 0
open_trades = 0
total = 0

with open(FILE, "r") as f:
    reader = csv.DictReader(f)

    for row in reader:

        total += 1

        result = row["Result"].upper()

        if result == "WIN":
            wins += 1

        elif result == "LOSS":
            losses += 1

        else:
            open_trades += 1

closed = wins + losses

if closed > 0:
    winrate = round((wins / closed) * 100, 2)
else:
    winrate = 0

print("\n====== JAGUAR BACKTEST ENGINE ======\n")

print("Total Trades :", total)
print("Closed Trades:", closed)
print("Open Trades  :", open_trades)
print("Wins         :", wins)
print("Losses       :", losses)
print("Win Rate     :", f"{winrate}%")
