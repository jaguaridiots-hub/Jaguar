# strategy/regime_engine.py

class RegimeEngine:
    """Classifies market regime based on ADX and Bollinger Band width."""

    def run(self, state, bus):

        # Read indicators from the correct source (state.indicators)
        tech = state.indicators or {}

        # Extract numeric values, handling both plain numbers and dicts with 'value' key
        adx_val = tech.get("adx")
        adx = adx_val.get("value", 20) if isinstance(adx_val, dict) else adx_val or 20

        atr_val = tech.get("atr")
        atr = atr_val.get("value", 0) if isinstance(atr_val, dict) else atr_val or 0

        bb_width_val = tech.get("bb_width")
        bb_width = bb_width_val.get("value", 0) if isinstance(bb_width_val, dict) else bb_width_val or 0

        # Regime logic
        regime = "RANGE"
        score = 0
        reasons = []

        if adx >= 30:
            regime = "TREND"
            score += 20
            reasons.append("Strong Trend")
        elif adx <= 20:
            regime = "RANGE"
            reasons.append("Range Market")
        else:
            regime = "RANGE"   # default for 20 < adx < 30

        if bb_width > 50:
            regime = "BREAKOUT"
            score += 10
            reasons.append("Volatility Expansion")
        elif bb_width < 20:
            regime = "COMPRESSION"
            reasons.append("Low Volatility")

        # Store the result
        state.regime = {
            "regime": regime,
            "score": score,
            "atr": atr,
            "adx": adx,
            "bb_width": bb_width,
            "reasons": reasons,
        }

        return state
