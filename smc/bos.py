from data.market_data import candles

previous_high = candles[-2]["high"]
current_close = candles[-1]["close"]

print("====== Break Of Structure ======")
print(f"Previous High : {previous_high:.2f}")
print(f"Current Close : {current_close:.2f}")

if current_close > previous_high:
    print("\nBOS : BULLISH")
else:
    print("\nBOS : NO BREAK")
