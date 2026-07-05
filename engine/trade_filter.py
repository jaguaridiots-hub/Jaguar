from engine.market_regime import analyze as regime
from indicators.volume import signal as volume_signal


def analyze(state):

    report = regime(state)

    allow = True
    reasons = []

    if report["regime"] == "RANGING":
        allow = False
        reasons.append("Market is ranging")

    if report["volatility"] == "HIGH":
        allow = False
        reasons.append("High volatility")

    if volume_signal == "LOW VOLUME":
        allow = False
        reasons.append("Low volume")

    return {
        "allow_trade": allow,
        "reasons": reasons
    }
