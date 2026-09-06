from data.market_data import candles

previous_high = candles[-2]["high"]
current_high = candles[-1]["high"]

print("====== Liquidity Sweep ======")
print(f"Previous High : {previous_high:.2f}")
print(f"Current High  : {current_high:.2f}")

if current_high > previous_high:
    print("\nLiquidity Grab : YES")
    print("Smart Money may have taken liquidity.")
else:
    print("\nLiquidity Grab : NO")
