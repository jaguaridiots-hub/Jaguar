from engine.market_context import phase

print("\n====== Jaguar Exit Quality ======\n")

if phase == "BUY CLIMAX":
    exit_action = "TAKE PROFIT"
    confidence = "HIGH"

elif phase == "HEALTHY TREND":
    exit_action = "HOLD"
    confidence = "HIGH"

elif phase == "PULLBACK":
    exit_action = "ACCUMULATE"
    confidence = "MEDIUM"

else:
    exit_action = "WAIT"
    confidence = "LOW"

print("Exit Action :", exit_action)
print("Confidence  :", confidence)
