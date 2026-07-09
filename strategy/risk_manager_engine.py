class RiskManagerEngine:

    def run(self, state, bus):

        bus.publish("RISK_ANALYSIS")

        trade = state.trade_plan

        capital = 100000.0
        risk_percent = 1.0

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

            "status": status
        }

        bus.publish("RISK_READY")

        return state
