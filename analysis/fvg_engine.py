# ============================================
# Jaguar Quant X
# Fair Value Gap Engine
# Version 2.0
# Real Detection
# ============================================

from data.market_data import get_klines


LOOKBACK = 100


def fvg_score():

    candles = get_klines(limit=LOOKBACK)

    score = 0
    reasons = []

    bullish_gap = False
    bearish_gap = False

    gap_low = None
    gap_high = None

    for i in range(2, len(candles)):

        c1 = candles[i - 2]
        c2 = candles[i - 1]
        c3 = candles[i]

        # ----------------------------
        # Bullish Fair Value Gap
        # ----------------------------

        if c1["high"] < c3["low"]:

            bullish_gap = True
            gap_low = c1["high"]
            gap_high = c3["low"]

        # ----------------------------
        # Bearish Fair Value Gap
        # ----------------------------

        elif c1["low"] > c3["high"]:

            bearish_gap = True
            gap_low = c3["high"]
            gap_high = c1["low"]

    current = candles[-1]["close"]

    # =======================================
    # Score only if price is inside the gap
    # =======================================

    if bullish_gap:

        if gap_low <= current <= gap_high:

            score += 3

            reasons.append(
                f"Bullish FVG {round(gap_low,2)}-{round(gap_high,2)}"
            )

    if bearish_gap:

        if gap_low <= current <= gap_high:

            score -= 3

            reasons.append(
                f"Bearish FVG {round(gap_low,2)}-{round(gap_high,2)}"
            )

    return score, reasons
