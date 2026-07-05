from historical.data_loader import load_data
from historical.strategy import check_signal

print("\n========== JAGUAR TRADE ENGINE V6 ==========\n")

candles = load_data()

balance = 10000

wins = 0
losses = 0
trades = 0

position = None

for i in range(200, len(candles)):

    candle = candles[i]

    if position is None:

        signal = check_signal(candles, i)

        if signal is not None:

            position = signal
            trades += 1

    else:

        high = candle["high"]
        low = candle["low"]

        if position["signal"] == "BUY":

            if low <= position["sl"]:
                balance -= position["entry"] - position["sl"]
                losses += 1
                position = None

            elif high >= position["tp"]:
                balance += position["tp"] - position["entry"]
                wins += 1
                position = None

        else:

            if high >= position["sl"]:
                balance -= position["sl"] - position["entry"]
                losses += 1
                position = None

            elif low <= position["tp"]:
                balance += position["entry"] - position["tp"]
                wins += 1
                position = None

print("Trades :", trades)
print("Wins   :", wins)
print("Losses :", losses)

if trades:
    print("Win Rate :", round(wins / trades * 100, 2), "%")

print("Balance :", round(balance, 2))
