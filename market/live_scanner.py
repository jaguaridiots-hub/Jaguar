from market.watchlist import WATCHLIST

print("\n========== Jaguar LIVE Scanner ==========\n")

results = []

for symbol in WATCHLIST:

    technical = 0
    smartmoney = 0
    probability = 0

    # EMA
    technical += 3

    # RSI
    technical -= 1

    # Volume
    technical += 2

    # Smart Money
    smartmoney += 2

    total = technical + smartmoney

    probability = min(95, 50 + total * 5)

    if probability >= 90:
        signal = "🟢 STRONG BUY"
    elif probability >= 80:
        signal = "🟢 BUY"
    elif probability >= 70:
        signal = "🟡 WATCH"
    else:
        signal = "🔴 NO TRADE"

    results.append((probability, symbol, signal))

results.sort(reverse=True)

for p, s, sig in results:
    print(f"{s:12} {p}%   {sig}")

best = results[0]

print("\n============================")
print("BEST TRADE TODAY")
print("============================")
print(best[1])
print(best[0], "%")
print(best[2])
