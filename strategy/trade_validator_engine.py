# strategy/trade_validator_engine.py
class TradeValidatorEngine:

    def run(self, state, bus):
        bus.publish("TRADE_VALIDATOR_ANALYSIS")

        blockers = []
        validation_score = 100  # start perfect, subtract for each issue

        # ---- 1. Market Regime ----
        regime = getattr(state, "regime", {})
        if regime.get("regime") == "COMPRESSION":
            validation_score -= 10
            blockers.append("Low volatility regime (COMPRESSION)")

        # ---- 2. Session ----
        session = getattr(state, "session", {})
        if session.get("session") not in ["LONDON", "NY", "ASIA"]:
            validation_score -= 5
            blockers.append("Session not institutionally active")

        # ---- 3. Order Flow ----
        orderflow = getattr(state, "orderflow", {})
        if orderflow.get("signal") not in ["BULLISH", "BEARISH"]:
            validation_score -= 10
            blockers.append("Order flow signal missing or neutral")

        # ---- 4. Volume ----
        volume = getattr(state, "volume", 0)
        if volume == 0:
            validation_score -= 15
            blockers.append("Volume is zero (live/incomplete candle)")

        # ---- 5. Risk ----
        risk = getattr(state, "risk", {})
        if risk.get("status") == "HIGH RISK":
            validation_score -= 10
            blockers.append("Risk status is HIGH RISK")

        # ---- 6. Price ----
        price = getattr(state, "price", 0)
        if price <= 0:
            validation_score -= 20
            blockers.append("Invalid price")

        # ---- Final approval: validated if score >= 60 ----
        approved = validation_score >= 60

        # ---- Store validation result (NO BUY/SELL/WAIT/REJECT) ----
        state.trade_validator = {
            "approved": approved,
            "validation_score": max(0, validation_score),
            "blockers": blockers,
        }

        bus.publish("TRADE_VALIDATOR_READY")
        return state
