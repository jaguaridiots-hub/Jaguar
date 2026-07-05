from historical.data_loader import load_data
from historical.patterns import detect_pattern

candles = load_data()

print("\n========== JAGUAR PATTERN ==========\n")
print(detect_pattern(candles))
