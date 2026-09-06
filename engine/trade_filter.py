from engine.market_regime import analyze as regime
from indicators.volume import signal as volume_signal


def analyze(state):
    report = regime(state)

    allow = True
    reasons = []

    # -----------------------------
    # Market Regime Filter
    # -----------------------------
    if report.get("regime") == "RANGING":
        allow = False
        reasons.append("Market is ranging")

    # -----------------------------
    # Volatility Filter
    # -----------------------------
    if report.get("volatility") == "HIGH":
        reasons.append("High volatility")

    # -----------------------------
    # Volume Filter
    # -----------------------------
    if volume_signal == "LOW VOLUME":
        reasons.append("Low Volume")

    # -----------------------------
    # Strong AI Override
    # -----------------------------
    if hasattr(state, "ai_score") and state.ai_score >= 10:
        allow = True
        reasons.append("AI Override")

    return {
        "allow_trade": allow,
        "reasons": reasons
    }


if __name__ == "__main__":
    from core.market_state import MarketState

    state = MarketState()
    state.ai_score = 10

    print(analyze(state))
