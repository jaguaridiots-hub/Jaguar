from engine.master_ai import total
from engine.market_regime import regime

probability = 50

# Master AI contribution
probability += total * 5

# Market Regime contribution
if regime == "BUY THE DIP":
    probability += 15
elif regime == "SELL THE RALLY":
    probability += 15
else:
    probability -= 10

# Clamp to 0–100
probability = max(0, min(100, probability))

print("\n====== Jaguar Probability Engine ======\n")
print("Probability :", probability, "%")

if probability >= 90:
    grade = "A+"
elif probability >= 80:
    grade = "A"
elif probability >= 70:
    grade = "B"
elif probability >= 60:
    grade = "C"
else:
    grade = "NO TRADE"

print("Trade Grade :", grade)
