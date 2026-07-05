from datetime import datetime, timedelta

today = datetime.now()

print("====== Gann Time Cycle ======")
print("Start :", today.strftime("%Y-%m-%d"))
print()

cycles = [30, 45, 60, 90, 120, 144, 180, 360]

for days in cycles:
    future = today + timedelta(days=days)
    print(f"{days:>3} Days : {future.strftime('%Y-%m-%d')}")
