from engine.market_context import trend, phase

print("\n====== Jaguar Entry Quality ======\n")

score = 0

if trend == "STRONG BULL":
    score += 3

if phase == "HEALTHY TREND":
    score += 3
elif phase == "PULLBACK":
    score += 4
elif phase == "BUY CLIMAX":
    score -= 2

if score >= 6:
    grade = "A+"
elif score >= 4:
    grade = "A"
elif score >= 2:
    grade = "B"
else:
    grade = "C"

print("Entry Score :", score)
print("Entry Grade :", grade)
