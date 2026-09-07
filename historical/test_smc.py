from historical.data_loader import load_data
from historical.smc import break_of_structure, change_of_character

candles = load_data()

print("\n========== JAGUAR V9 SMC ==========\n")

print("Break Of Structure :", break_of_structure(candles))
print("Change Of Character:", change_of_character(candles))
