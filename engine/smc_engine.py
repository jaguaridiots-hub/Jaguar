from analysis.support_resistance_engine import support_resistance


def analyze(state):
    reasons = []
    score = 0

    price = state.price
    ema20 = state.ema20
    ema50 = state.ema50

    levels = support_resistance()

    support = levels["support"]
    resistance = levels["resistance"]

    # -----------------------------
    # Break of Structure (BOS)
    # -----------------------------
    if price > ema20 > ema50:
        bos = "BULLISH"
        score += 2
        reasons.append("Bullish BOS")

    elif price < ema20 < ema50:
        bos = "BEARISH"
        score -= 2
        reasons.append("Bearish BOS")

    else:
        bos = "NONE"

    # -----------------------------
    # Change of Character
    # -----------------------------
    choch = False

    if bos == "BULLISH" and price < ema20:
        choch = True
        reasons.append("Bearish CHoCH")

    elif bos == "BEARISH" and price > ema20:
        choch = True
        reasons.append("Bullish CHoCH")

    # -----------------------------
    # Order Block
    # -----------------------------
    if abs(price - support) < abs(price - resistance):
        order_block = "BULLISH"
        score += 1
        reasons.append("Bullish Order Block")
    else:
        order_block = "BEARISH"
        score -= 1
        reasons.append("Bearish Order Block")

    # -----------------------------
    # Liquidity
    # -----------------------------
    if abs(price - support) < state.atr:
        liquidity = "EQUAL LOW"
        score += 1
        reasons.append("Equal Low Liquidity")

    elif abs(price - resistance) < state.atr:
        liquidity = "EQUAL HIGH"
        score -= 1
        reasons.append("Equal High Liquidity")

    else:
        liquidity = "NONE"

    # -----------------------------
    # Fair Value Gap
    # -----------------------------
    fvg = abs(resistance - support) > state.atr * 2

    if fvg:
        score += 1
        reasons.append("Fair Value Gap")

    # -----------------------------
    # Premium / Discount
    # -----------------------------
    midpoint = (support + resistance) / 2

    premium = False
    discount = False

    if price > midpoint:
        premium = True
        reasons.append("Premium Zone")
    else:
        discount = True
        score += 1
        reasons.append("Discount Zone")

    return {
        "bos": bos,
        "choch": choch,
        "order_block": order_block,
        "fvg": fvg,
        "liquidity": liquidity,
        "premium": premium,
        "discount": discount,
        "score": score,
        "reasons": reasons
    }


if __name__ == "__main__":
    from core.market_state import MarketState

    state = MarketState()

    state.price = 63000
    state.ema20 = 62950
    state.ema50 = 62800
    state.atr = 180

    print(analyze(state))
