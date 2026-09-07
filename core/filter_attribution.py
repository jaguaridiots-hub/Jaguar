# core/filter_attribution.py
"""
Runtime filter attribution instrumentation.
Counts every candle, candidate setup, and rejection reason.
"""

class FilterAttribution:
    def __init__(self):
        self.reset()

    def reset(self):
        self.candles_evaluated = 0
        self.candidate_setups = 0
        self.filters = {
            "Regime": 0,
            "SMC": 0,
            "Volume": 0,
            "Session": 0,
            "ExecutionTrigger": 0,
            "ExecutionConfirmation": 0,
            "Validator": 0,
            "RiskManager": 0,
            "MasterDecision": 0,
            "TradePlanner": 0,
        }
        self.executed_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.rejection_reasons = {}  # candidate_id -> list of reasons

    def count_candle(self):
        self.candles_evaluated += 1

    def count_candidate_setup(self):
        """Increment candidate setup counter."""
        self.candidate_setups += 1

    def count_candidate(self, state):
        self.candidate_setups += 1
        reasons = []
        candidate_id = self.candidate_setups

        # ---- Regime Filter ----
        regime = getattr(state, "regime", {})
        if regime.get("regime") == "COMPRESSION":
            reasons.append("Regime")
            self.filters["Regime"] += 1

        # ---- SMC Filter ----
        smc = getattr(state, "smc", {})
        if smc.get("signal") == "NEUTRAL":
            reasons.append("SMC")
            self.filters["SMC"] += 1

        # ---- Volume Filter ----
        volume = getattr(state, "volume", 0)
        if volume == 0:
            reasons.append("Volume")
            self.filters["Volume"] += 1

        # ---- Session Filter ----
        session = getattr(state, "session", {})
        if session.get("session") not in ["LONDON", "NY", "ASIA"]:
            reasons.append("Session")
            self.filters["Session"] += 1

        # ---- Execution Trigger ----
        trigger = getattr(state, "execution_trigger", {})
        if not trigger.get("confirmed", False):
            reasons.append("ExecutionTrigger")
            self.filters["ExecutionTrigger"] += 1

        # ---- Execution Confirmation ----
        confirmation = getattr(state, "execution_confirmation", {})
        if not confirmation.get("confirmed", False):
            reasons.append("ExecutionConfirmation")
            self.filters["ExecutionConfirmation"] += 1

        # ---- Trade Validator ----
        validator = getattr(state, "trade_validator", {})
        if not validator.get("approved", True):
            reasons.append("Validator")
            self.filters["Validator"] += 1

        # ---- Risk Manager ----
        risk = getattr(state, "risk", {})
        if risk.get("status") == "HIGH RISK":
            reasons.append("RiskManager")
            self.filters["RiskManager"] += 1

        # ---- Master Decision ----
        master = getattr(state, "master_decision", {})
        if master.get("decision") in ["REJECT", "WAIT"]:
            reasons.append("MasterDecision")
            self.filters["MasterDecision"] += 1

        # ---- Trade Planner ----
        trade_plan = getattr(state, "trade_plan", {})
        if trade_plan is None or not trade_plan:
            reasons.append("TradePlanner")
            self.filters["TradePlanner"] += 1

        self.rejection_reasons[candidate_id] = reasons

    def count_executed_trade(self):
        self.executed_trades += 1

    def count_winning_trade(self):
        self.winning_trades += 1

    def count_losing_trade(self):
        self.losing_trades += 1

    def generate_report(self):
        lines = []
        lines.append("="*60)
        lines.append("JAGUAR FILTER ATTRIBUTION REPORT")
        lines.append("="*60)
        lines.append(f"\nCandles Evaluated : {self.candles_evaluated}")
        lines.append(f"Candidate Setups  : {self.candidate_setups}")
        lines.append("\nFilter Rejections:")
        for name, count in self.filters.items():
            if count > 0:
                lines.append(f"  {name:25} : {count}")
        lines.append(f"\nExecuted Trades  : {self.executed_trades}")
        lines.append(f"Winning Trades   : {self.winning_trades}")
        lines.append(f"Losing Trades    : {self.losing_trades}")
        lines.append("\n" + "="*60)

        # Unique rejections per candidate
        unique_rejections = set()
        for reasons in self.rejection_reasons.values():
            unique_rejections.update(reasons)
        if unique_rejections:
            lines.append("\nFilters Applied (at least once):")
            for f in sorted(unique_rejections):
                lines.append(f"  - {f}")

        lines.append("="*60)
        return "\n".join(lines)

    def print_report(self):
        print(self.generate_report())


# Global instance
_filter_attribution = None

def get_attribution():
    global _filter_attribution
    if _filter_attribution is None:
        _filter_attribution = FilterAttribution()
    return _filter_attribution

def reset_attribution():
    global _filter_attribution
    _filter_attribution = FilterAttribution()
