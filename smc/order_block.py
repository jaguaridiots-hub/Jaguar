from data.market_data import candles

open_price = candles[-2]["open"]
close_price = candles[-2]["close"]

print("====== Order Block ======")
print(f"Open  : {open_price:.2f}")
print(f"Close : {close_price:.2f}")

if close_price > open_price:
    print("\nBullish Order Block")
else:
    print("\nBearish Order Block")
