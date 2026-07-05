from data.market_data import candles

previous_low = candles[-2]["low"]
current_close = candles[-1]["close"]

print("====== Change Of Character ======")
print(f"Previous Low  : {previous_low:.2f}")
print(f"Current Close : {current_close:.2f}")

if current_close < previous_low:
    print("\nCHoCH : BEARISH")
else:
    print("\nCHoCH : NO CHANGE")
