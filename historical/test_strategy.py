from historical.data_loader import load_data
from historical.strategy import generate_signal

candles = load_data()

signal = generate_signal(candles)

print("\n========== JAGUAR V7 STRATEGY ==========\n")
print(signal)
