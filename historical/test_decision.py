from historical.data_loader import load_data
from historical.decision import decision

candles = load_data()

print("\n========= JAGUAR V10 AI DECISION =========\n")

print(decision(candles))
