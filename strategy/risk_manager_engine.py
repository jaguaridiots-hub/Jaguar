# strategy/risk_manager_engine.py
class RiskManagerEngine:

    def run(self, state, bus):
        bus.publish("RISK_ANALYSIS")

        trade = state.trade_plan

        if trade is None:
            state.risk = {
                "capital": 0,
                "risk_percent": 0,
                "max_loss": 0,
                "position_size": 0,
                "exposure": 0,
                "status": "NO TRADE"
            }
            bus.publish("RISK_READY")
            return state

        # ============================================================
        # MODE-SPECIFIC RISK PERCENTAGE
        # ============================================================
        mode = getattr(state, "mode", "SWING")  # default to SWING

        if mode == "SCALP":
            risk_percent = 0.5   # tighter risk for scalping
        elif mode == "CLASSIC":
            risk_percent = 1.5   # higher risk for longer-term plays
        else:  # SWING
            risk_percent = 1.0   # balanced

        capital = 100000.0  # could be dynamic from portfolio later
        max_loss = capital * risk_percent / 100

        entry = trade.get("entry")
        stop = trade.get("stop")

        position_size = 0
        exposure = 0
        status = "NO TRADE"

        if (
            entry is not None and
            stop is not None and
            entry != stop
        ):
            risk_per_unit = abs(entry - stop)
            position_size = max_loss / risk_per_unit
            exposure = position_size * entry

            if exposure <= capital:
                status = "SAFE"
            else:
                status = "HIGH RISK"

        state.risk = {
            "capital": capital,
            "risk_percent": risk_percent,
            "max_loss": round(max_loss, 2),
            "position_size": round(position_size, 4),
            "exposure": round(exposure, 2),
            "status": status,
            "mode": mode  # track which mode was used
        }

        print(f"📊 RISK: {status} | Position Size: {round(position_size, 4)} | Mode: {mode}")

        bus.publish("RISK_READY")
        return state
