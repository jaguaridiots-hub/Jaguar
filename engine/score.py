score = 0
details = []

def reset():
    global score, details
    score = 0
    details = []

def add(points, reason):
    global score
    score += points
    details.append((reason, points))

def report():
    print("\n====== Jaguar AI Score ======\n")

    for reason, pts in details:
        sign = "+" if pts >= 0 else ""
        print(f"{reason:<25} {sign}{pts}")

    print("\n----------------------------")
    print("Total Score :", score)

    if score >= 12:
        signal = "STRONG BUY"
        probability = 95
    elif score >= 8:
        signal = "BUY"
        probability = 80
    elif score >= 4:
        signal = "WATCHLIST"
        probability = 65
    elif score >= 0:
        signal = "WAIT"
        probability = 50
    elif score >= -4:
        signal = "SELL"
        probability = 35
    else:
        signal = "STRONG SELL"
        probability = 15

    print("Probability :", f"{probability}%")
    print("Signal      :", signal)

if __name__ == "__main__":
    add(3, "EMA Trend")
    add(2, "Volume")
    add(-2, "RSI Overbought")
    report()
