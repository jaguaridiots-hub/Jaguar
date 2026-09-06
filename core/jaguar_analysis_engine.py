
"""
Jaguar Quant X
Canonical Analysis Engine
Version : 3.0
"""

class JaguarAnalysisEngine:

    def __init__(self, kernel):
        self.kernel = kernel

    def run(self, symbol):

        state = self.kernel.get_state()

        from market.live_loader import update_state
        from indicators.indicator_engine import update_market_state

        state = update_state(
            state,
            symbol,
        )

        state = update_market_state(state)

        from engine.institutional_master import analyze

        report = analyze(state)

        return {
            "state": state,
            "report": report,
        }
