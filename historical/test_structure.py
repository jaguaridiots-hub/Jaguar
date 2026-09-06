from historical.data_loader import load_data
from historical.market_structure import market_structure

candles = load_data()

print("\n====== JAGUAR MARKET STRUCTURE ======\n")
print(market_structure(candles))
