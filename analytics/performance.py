import csv

FILE = "trade_history.csv"

total = 0
wins = 0
losses = 0
open_trades = 0

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
    win_rate = round((wins / closed) * 100, 2)
else:
    win_rate = 0

print("\n========== JAGUAR PERFORMANCE ==========\n")

print("Total Trades   :", total)
print("Closed Trades  :", closed)
print("Open Trades    :", open_trades)

print()

print("Wins           :", wins)
print("Losses         :", losses)

print()

print("Win Rate       :", str(win_rate) + "%")

print()

if win_rate >= 80:
    grade = "A+"

elif win_rate >= 70:
    grade = "A"

elif win_rate >= 60:
    grade = "B"

elif win_rate >= 50:
    grade = "C"

else:
    grade = "D"

print("Performance Grade :", grade)

print("\n========================================")
