capital = 10000

risk_per_trade = 2
max_daily_loss = 6
max_weekly_loss = 12
max_open_trades = 3

daily_loss = capital * max_daily_loss / 100
weekly_loss = capital * max_weekly_loss / 100

print("====== Jaguar Portfolio Risk Manager ======")
print(f"Capital            : ₹{capital}")
print(f"Risk / Trade       : {risk_per_trade}%")
print(f"Max Daily Loss     : ₹{daily_loss:.2f}")
print(f"Max Weekly Loss    : ₹{weekly_loss:.2f}")
print(f"Maximum Trades     : {max_open_trades}")

print()

print("Rules")
print("-------------------------------")
print("✓ Stop trading after daily loss")
print("✓ Maximum 3 open trades")
print("✓ Never risk more than 2%")
print("✓ Always use Stop Loss")
print("✓ Protect capital first")
