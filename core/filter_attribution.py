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

        # Canonical enterprise authorization attribution.
        # These counters describe the actual runtime contracts:
        # IDM -> Trade Planner -> Risk Manager -> Execution Gateway.
        self.canonical_gates = {
            "IDM": 0,
            "TradePlanner": 0,
            "RiskManager": 0,
            "ExecutionGateway": 0,
            "AuthorizationIdentity": 0,
            "Authorized": 0,
        }

        self.canonical_candidates = 0

        # IDM replay distribution.
        self.idm_decisions = {}
        self.idm_missing = {}
        self.idm_setups = {}
        self.idm_directions = {}
        self.idm_readiness = {}
        self.idm_location_quality = {}

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

    def record_canonical_gate(
        self,
        state,
    ):
        """Attribute the first blocking canonical enterprise gate."""

        idm = getattr(
            state,
            "idm",
            {},
        )
        trade = getattr(
            state,
            "trade",
            {},
        )
        risk = getattr(
            state,
            "risk",
            {},
        )
        execution = getattr(
            state,
            "execution",
            {},
        )

        if not isinstance(idm, dict):
            idm = {}

        if not isinstance(trade, dict):
            trade = {}

        if not isinstance(risk, dict):
            risk = {}

        if not isinstance(execution, dict):
            execution = {}

        decision = str(
            idm.get(
                "decision",
                "WAIT",
            )
        ).upper().strip()

        setup = str(
            idm.get(
                "setup",
                "UNKNOWN",
            )
        ).upper().strip()

        direction = str(
            idm.get(
                "direction",
                "NEUTRAL",
            )
        ).upper().strip()

        structural = idm.get(
            "structural",
            {},
        )

        if not isinstance(structural, dict):
            structural = {}

        readiness = str(
            structural.get(
                "readiness",
                "UNKNOWN",
            )
        ).upper().strip()

        location_quality = str(
            structural.get(
                "location_quality",
                "NONE",
            )
        ).upper().strip()

        self.idm_decisions[decision] = (
            self.idm_decisions.get(
                decision,
                0,
            )
            + 1
        )

        self.idm_setups[setup] = (
            self.idm_setups.get(
                setup,
                0,
            )
            + 1
        )

        self.idm_directions[direction] = (
            self.idm_directions.get(
                direction,
                0,
            )
            + 1
        )

        self.idm_readiness[readiness] = (
            self.idm_readiness.get(
                readiness,
                0,
            )
            + 1
        )

        self.idm_location_quality[location_quality] = (
            self.idm_location_quality.get(
                location_quality,
                0,
            )
            + 1
        )

        for reason in idm.get(
            "missing",
            [],
        ):
            key = str(
                reason
            ).strip()

            if not key:
                continue

            self.idm_missing[key] = (
                self.idm_missing.get(
                    key,
                    0,
                )
                + 1
            )

        replay_key = f"canonical:{self.candles_evaluated}"

        if decision not in (
            "ENTER_LONG",
            "ENTER_SHORT",
        ):
            self.filters["MasterDecision"] += 1
            self.canonical_gates["IDM"] += 1
            self.rejection_reasons[
                replay_key
            ] = [
                "IDM",
                f"decision={decision}",
                *[
                    str(reason)
                    for reason in idm.get(
                        "missing",
                        [],
                    )
                    if reason
                ],
            ]
            return

        self.canonical_candidates += 1
        self.candidate_setups += 1

        trade_status = str(
            trade.get(
                "status",
                "NO TRADE",
            )
        ).upper().strip()

        if trade_status != "READY":
            self.filters["TradePlanner"] += 1
            self.canonical_gates["TradePlanner"] += 1
            self.rejection_reasons[
                replay_key
            ] = [
                "TradePlanner",
                f"trade_status={trade_status}",
            ]
            return

        if not bool(
            risk.get(
                "approved",
                False,
            )
        ):
            self.filters["RiskManager"] += 1
            self.canonical_gates["RiskManager"] += 1
            self.rejection_reasons[
                replay_key
            ] = [
                "RiskManager",
                f"risk_status={risk.get('status', 'UNKNOWN')}",
                *[
                    str(reason)
                    for reason in risk.get(
                        "reasons",
                        [],
                    )
                    if reason
                ],
            ]
            return

        if not bool(
            execution.get(
                "approved",
                False,
            )
        ):
            self.filters["Validator"] += 1
            self.canonical_gates["ExecutionGateway"] += 1
            self.rejection_reasons[
                replay_key
            ] = [
                "ExecutionGateway",
                f"gate={execution.get('gate', 'UNKNOWN')}",
                f"status={execution.get('status', 'UNKNOWN')}",
                f"reason={execution.get('reason', 'UNKNOWN')}",
            ]
            return

        authorization_id = execution.get(
            "authorization_id"
        )

        if (
            not isinstance(
                authorization_id,
                str,
            )
            or not authorization_id.strip()
        ):
            self.filters["Validator"] += 1
            self.canonical_gates[
                "AuthorizationIdentity"
            ] += 1
            self.rejection_reasons[
                replay_key
            ] = [
                "AuthorizationIdentity",
                "missing authorization_id",
            ]
            return

        self.canonical_gates["Authorized"] += 1
        self.rejection_reasons[
            replay_key
        ] = [
            "Authorized",
            f"decision={decision}",
        ]

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
        lines.append("\nCanonical Gate Attribution:")
        for name, count in self.canonical_gates.items():
            lines.append(
                f"  {name:25} : {count}"
            )

        lines.append(
            f"\nCanonical Candidates : "
            f"{self.canonical_candidates}"
        )

        lines.append("\nIDM Decision Distribution:")
        for name, count in sorted(
            self.idm_decisions.items(),
            key=lambda item: (-item[1], item[0]),
        ):
            lines.append(
                f"  {name:30} : {count}"
            )

        lines.append("\nIDM Setup Distribution:")
        for name, count in sorted(
            self.idm_setups.items(),
            key=lambda item: (-item[1], item[0]),
        ):
            lines.append(
                f"  {name:30} : {count}"
            )

        lines.append("\nIDM Direction Distribution:")
        for name, count in sorted(
            self.idm_directions.items(),
            key=lambda item: (-item[1], item[0]),
        ):
            lines.append(
                f"  {name:30} : {count}"
            )

        lines.append("\nStructural Readiness Distribution:")
        for name, count in sorted(
            self.idm_readiness.items(),
            key=lambda item: (-item[1], item[0]),
        ):
            lines.append(
                f"  {name:30} : {count}"
            )

        lines.append("\nLocation Quality Distribution:")
        for name, count in sorted(
            self.idm_location_quality.items(),
            key=lambda item: (-item[1], item[0]),
        ):
            lines.append(
                f"  {name:30} : {count}"
            )

        lines.append("\nIDM Missing Conditions:")
        for name, count in sorted(
            self.idm_missing.items(),
            key=lambda item: (-item[1], item[0]),
        ):
            lines.append(
                f"  {name:35} : {count}"
            )

        lines.append(
            f"\nExecuted Trades  : "
            f"{self.executed_trades}"
        )
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
