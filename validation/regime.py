# validation/regime.py
def classify_regime(price, ma_200):
    """Classify market regime based on price relative to 200-day moving average."""
    if price > ma_200 * 1.05:
        return "BULL"
    elif price < ma_200 * 0.95:
        return "BEAR"
    else:
        return "RANGE"
