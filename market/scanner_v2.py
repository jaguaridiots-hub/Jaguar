from market.watchlist import WATCHLIST
import random

print("\n========== Jaguar Market Scanner ==========\n")

results = []

for symbol in WATCHLIST:

    probability = random.randint(50,95)

    if probability >= 90:
        signal = "🟢 STRONG BUY"
    elif probability >= 80:
        signal = "🟢 BUY"
    elif probability >= 70:
        signal = "🟡 WATCH"
    else:
        signal = "🔴 NO TRADE"

    results.append((probability,symbol,signal))

results.sort(reverse=True)

for p,s,sg in results:
    print(f"{s:12} {p}%   {sg}")

best = results[0]

print("\n==============================")
print("Best Opportunity")
print("==============================")

print(best[1])
print(best[0],"%")
print(best[2])
