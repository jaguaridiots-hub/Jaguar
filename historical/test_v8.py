from historical.data_loader import load_data
from historical.indicators import calculate_indicators

candles = load_data()

ind = calculate_indicators(candles)

print("\n========== JAGUAR V8 ==========\n")

for k,v in ind.items():
    print(k,":",v)
