"""
Jaguar Quant X Enterprise
Jaguar Brain V5
"""

class JaguarBrainV5:

    name = "Jaguar Brain V5"

    def process(self, state):

        narrative = []
        conflicts = []
        summary = ""

        # ==========================
        # Trend
        # ==========================

        if state.trend == "BULLISH":
            narrative.append(
                "Higher timeframe trend is bullish."
            )

        elif state.trend == "BEARISH":
            narrative.append(
                "Higher timeframe trend is bearish."
            )

        # ==========================
        # Structure
        # ==========================

        if state.bos:
            narrative.append(
                "Break of Structure confirmed."
            )

        if state.choch:
            narrative.append(
                "Change of Character detected."
            )

        # ==========================
        # Liquidity
        # ==========================

        if state.liquidity:
            narrative.append(
                "Liquidity sweep completed."
            )

        # ==========================
        # Order Block
        # ==========================

        if state.order_block:
            narrative.append(
                "Fresh Order Block respected."
            )

        # ==========================
        # Fair Value Gap
        # ==========================

        if state.fvg:
            narrative.append(
                "Fair Value Gap present."
            )

        # ==========================
        # Momentum
        # ==========================

        if state.rsi < 40:
            conflicts.append(
                "Weak RSI momentum."
            )

        elif state.rsi > 70:
            conflicts.append(
                "Market may be overbought."
            )

        # ==========================
        # Regime
        # ==========================

        regime = state.regime

        if regime == "UNKNOWN":

            if state.bos:
                regime = "TRENDING"

            else:
                regime = "RANGING"

        # ==========================
        # Summary
        # ==========================

        if state.institutional["score"] >= 80:

            summary = (
                "Institutional conditions are strong."
            )

        elif state.institutional["score"] >= 60:

            summary = (
                "Institutional conditions are moderate."
            )

        else:

            summary = (
                "Institutional conditions are weak."
            )

        # ==========================
        # Output
        # ==========================

        state.brain = {

            "context": {

                "trend": state.trend,

                "regime": regime

            },

            "narrative": narrative,

            "conflicts": conflicts,

            "summary": summary

        }

        return state
