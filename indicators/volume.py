def volume(candles):
    vols = [c["volume"] for c in candles]

    current = vols[-1]
    average = sum(vols[-20:]) / 20

    if current > average:
        signal = "HIGH VOLUME"
    else:
        signal = "LOW VOLUME"

    print("====== Volume ======")
    print(current)
    print(average)
    print(signal)

    return {
        "current": current,
        "average": average,
        "signal": signal
    }
