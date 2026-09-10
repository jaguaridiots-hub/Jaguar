"""
Jaguar Quant X Enterprise
Execution Gateway V3

Final enterprise execution authorization authority.

Authority chain:
1. Institutional Decision Matrix
2. Structural Execution Readiness
3. Trade Plan Integrity
4. Direction Consistency
5. Trade Geometry
6. Risk Approval
7. Position Size
8. Entry Freshness
9. Spread Guard
10. Session Guard
11. Execution Authorization

IMPORTANT:
This gateway does not create trade evidence.
It does not repair malformed plans.
It does not override IDM.
It does not calculate position size.
It does not execute broker orders.

It only authorizes or blocks execution.

The gateway fails closed.
"""


import hashlib
from config.config_manager import config


class ExecutionGatewayV2:

    name = "Execution Gateway V3"

    # ==================================================
    # SAFE HELPERS
    # ==================================================

    @staticmethod
    def _dictionary(value):

        if isinstance(value, dict):
            return value

        return {}

    @staticmethod
    def _float(value, default=0.0):

        try:
            return float(
                value
                if value is not None
                else default
            )

        except (
            TypeError,
            ValueError,
        ):
            return float(default)

    @staticmethod
    def _reasons(value):

        if not isinstance(value, list):
            return []

        return [
            str(reason)
            for reason in value
        ]

    @staticmethod
    def _block(
        state,
        status,
        gate,
        reason,
    ):

        state.execution = {

            "ready": False,

            "approved": False,

            "status": status,

            "gate": gate,

            "reason": reason,

            "mode": config.get_execution_mode(),

            "broker": "Paper",


            "decision": "WAIT",

            "entry": None,

            "stop_loss": None,

            "targets": [],

            "position_size": 0.0,

            "risk_percent": 0.0,

            "authorization_id": None,

        }

        return state

    # ==================================================
    # PROCESS
    # ==================================================

    def process(self, state):

        # ==================================================
        # SAFE STATE CONTRACTS
        # ==================================================

        idm = self._dictionary(
            getattr(
                state,
                "idm",
                {},
            )
        )

        trade = self._dictionary(
            getattr(
                state,
                "trade",
                {},
            )
        )

        risk = self._dictionary(
            getattr(
                state,
                "risk",
                {},
            )
        )

        market = self._dictionary(
            getattr(
                state,
                "market",
                {},
            )
        )

        structural_zone = self._dictionary(
            getattr(
                state,
                "structural_zone",
                {},
            )
        )

        # ==================================================
        # 0. MARKET DATA INTEGRITY GATE
        # ==================================================
        # Synthetic/offline fallback data must NEVER be
        # eligible for live execution.
        # ==================================================

        market_metadata = self._dictionary(
            getattr(
                state,
                "market_metadata",
                {},
            )
        )

        source = str(
            market_metadata.get(
                "source",
                "",
            )
        ).lower().strip()

        synthetic = (
            market_metadata.get("synthetic") is True
            or source == "offline_fallback"
        )

        live_data_valid = (
            market_metadata.get("live_data_valid") is True
        )

        execution_allowed = (
            market_metadata.get("execution_allowed") is True
        )

        if synthetic:
            return self._block(
                state,
                "BLOCKED",
                "MARKET_DATA",
                "Execution blocked: synthetic/offline market data.",
            )

        if not live_data_valid:
            return self._block(
                state,
                "BLOCKED",
                "MARKET_DATA",
                "Execution blocked: live market data failed integrity validation.",
            )

        if not execution_allowed:
            return self._block(
                state,
                "BLOCKED",
                "MARKET_DATA",
                "Execution blocked: market data is not execution-authorized.",
            )

        decision = str(
            idm.get(
                "decision",
                "WAIT",
            )
        ).upper().strip()

        # ==================================================
        # 1. IDM AUTHORITY GATE
        # ==================================================

        if decision == "AVOID":

            reasons = self._reasons(
                idm.get(
                    "reasons",
                    [],
                )
            )

            reason = (
                reasons[0]
                if reasons
                else "IDM rejected trade"
            )

            return self._block(
                state,
                "BLOCKED",
                "IDM",
                reason,
            )

        if decision == "WAIT":

            reasons = self._reasons(
                idm.get(
                    "reasons",
                    [],
                )
            )

            missing = self._reasons(
                idm.get(
                    "missing",
                    [],
                )
            )

            reason = (
                reasons[0]
                if reasons
                else "IDM awaiting confirmation"
            )

            if missing:

                missing_text = ", ".join(
                    str(item)
                    .replace("_", " ")
                    .lower()
                    for item in missing
                )

                reason = (
                    f"{reason} Missing: "
                    f"{missing_text}."
                )

            return self._block(
                state,
                "WAIT",
                "IDM",
                reason,
            )

        if decision not in (
            "ENTER_LONG",
            "ENTER_SHORT",
        ):

            return self._block(
                state,
                "BLOCKED",
                "IDM",
                "Unknown institutional decision",
            )

        # ==================================================
        # 2. STRUCTURAL EXECUTION READINESS GATE
        # ==================================================

        structural_readiness = str(
            structural_zone.get(
                "readiness",
                "WAITING",
            )
        ).upper().strip()

        structural_direction = str(
            structural_zone.get(
                "direction",
                "NEUTRAL",
            )
        ).upper().strip()

        zone_direction = str(
            structural_zone.get(
                "zone_direction",
                "NEUTRAL",
            )
        ).upper().strip()

        location_quality = str(
            structural_zone.get(
                "location_quality",
                "NONE",
            )
        ).upper().strip()

        if structural_readiness != "CONFIRMED":

            return self._block(
                state,
                "WAIT",
                "STRUCTURAL_ZONE",
                (
                    "Structural execution location "
                    f"is not confirmed: "
                    f"{structural_readiness}"
                ),
            )

        expected_direction = (
            "BULLISH"
            if decision == "ENTER_LONG"
            else "BEARISH"
        )

        if structural_direction != expected_direction:

            return self._block(
                state,
                "BLOCKED",
                "STRUCTURAL_DIRECTION",
                (
                    "Structural direction conflicts "
                    "with IDM decision"
                ),
            )

        if zone_direction != expected_direction:

            return self._block(
                state,
                "BLOCKED",
                "ZONE_DIRECTION",
                (
                    "Execution zone direction conflicts "
                    "with IDM decision"
                ),
            )

        if location_quality != "INTERACTING":

            return self._block(
                state,
                "WAIT",
                "EXECUTION_LOCATION",
                (
                    "Price is not interacting with "
                    "the confirmed structural zone"
                ),
            )

        # ==================================================
        # 3. TRADE PLAN STATUS GATE
        # ==================================================

        if trade.get("status") != "READY":

            return self._block(
                state,
                "BLOCKED",
                "TRADE_PLANNER",
                "Trade plan not ready",
            )

        # ==================================================
        # 4. TRADE PLAN CONTRACT
        # ==================================================

        entry_raw = trade.get("entry")

        stop_raw = trade.get("stop_loss")

        targets = trade.get(
            "targets",
            [],
        )

        if (
            entry_raw is None
            or stop_raw is None
            or not isinstance(targets, list)
            or len(targets) == 0
        ):

            return self._block(
                state,
                "BLOCKED",
                "TRADE_PLANNER",
                "Invalid trade plan contract",
            )

        entry = self._float(
            entry_raw,
            0.0,
        )

        stop_loss = self._float(
            stop_raw,
            0.0,
        )

        normalized_targets = [
            self._float(
                target,
                0.0,
            )
            for target in targets
        ]

        if (
            entry <= 0
            or stop_loss <= 0
            or any(
                target <= 0
                for target in normalized_targets
            )
        ):

            return self._block(
                state,
                "BLOCKED",
                "TRADE_PLANNER",
                "Trade plan contains invalid prices",
            )

        # ==================================================
        # 5. TRADE DIRECTION CONSISTENCY
        # ==================================================

        trade_side = str(
            trade.get(
                "side",
                expected_direction,
            )
        ).upper().strip()

        valid_long_sides = (
            "LONG",
            "BUY",
            "BULLISH",
        )

        valid_short_sides = (
            "SHORT",
            "SELL",
            "BEARISH",
        )

        if (
            decision == "ENTER_LONG"
            and trade_side not in valid_long_sides
        ):

            return self._block(
                state,
                "BLOCKED",
                "TRADE_DIRECTION",
                (
                    "Trade plan direction conflicts "
                    "with ENTER_LONG"
                ),
            )

        if (
            decision == "ENTER_SHORT"
            and trade_side not in valid_short_sides
        ):

            return self._block(
                state,
                "BLOCKED",
                "TRADE_DIRECTION",
                (
                    "Trade plan direction conflicts "
                    "with ENTER_SHORT"
                ),
            )

        # ==================================================
        # 6. TRADE GEOMETRY GATE
        # ==================================================

        if decision == "ENTER_LONG":

            if stop_loss >= entry:

                return self._block(
                    state,
                    "BLOCKED",
                    "TRADE_GEOMETRY",
                    (
                        "Long stop loss must be "
                        "below entry"
                    ),
                )

            if any(
                target <= entry
                for target in normalized_targets
            ):

                return self._block(
                    state,
                    "BLOCKED",
                    "TRADE_GEOMETRY",
                    (
                        "Long targets must be "
                        "above entry"
                    ),
                )

        else:

            if stop_loss <= entry:

                return self._block(
                    state,
                    "BLOCKED",
                    "TRADE_GEOMETRY",
                    (
                        "Short stop loss must be "
                        "above entry"
                    ),
                )

            if any(
                target >= entry
                for target in normalized_targets
            ):

                return self._block(
                    state,
                    "BLOCKED",
                    "TRADE_GEOMETRY",
                    (
                        "Short targets must be "
                        "below entry"
                    ),
                )

        # ==================================================
        # 7. RISK APPROVAL GATE
        # ==================================================

        if not bool(
            risk.get(
                "approved",
                False,
            )
        ):

            return self._block(
                state,
                "BLOCKED",
                "RISK_MANAGER",
                str(
                    risk.get(
                        "reason",
                        "Risk Manager rejected trade",
                    )
                ),
            )

        position_size = self._float(
            risk.get(
                "position_size",
                0.0,
            ),
            0.0,
        )

        risk_percent = self._float(
            risk.get(
                "risk_percent",
                0.0,
            ),
            0.0,
        )

        risk_amount = self._float(
            risk.get(
                "risk_amount",
                0.0,
            ),
            0.0,
        )

        if position_size <= 0:

            return self._block(
                state,
                "BLOCKED",
                "POSITION_SIZE",
                "Position size must be greater than zero",
            )

        if risk_percent <= 0:

            return self._block(
                state,
                "BLOCKED",
                "RISK_PERCENT",
                "Risk percent must be greater than zero",
            )

        # ==================================================
        # 8. ENTRY FRESHNESS GATE
        # ==================================================

        current_price = self._float(
            market.get(
                "price",
                getattr(
                    state,
                    "price",
                    0.0,
                ),
            ),
            0.0,
        )

        atr = self._float(
            getattr(
                state,
                "atr",
                0.0,
            ),
            0.0,
        )

        if current_price <= 0:

            return self._block(
                state,
                "BLOCKED",
                "MARKET_PRICE",
                "Current market price is invalid",
            )

        if atr <= 0:

            return self._block(
                state,
                "BLOCKED",
                "ATR",
                "ATR is invalid for freshness validation",
            )

        entry_distance = abs(
            current_price
            - entry
        )

        entry_distance_atr = (
            entry_distance
            / atr
        )

        max_entry_distance_atr = 0.50

        if entry_distance_atr > max_entry_distance_atr:

            return self._block(
                state,
                "WAIT",
                "ENTRY_FRESHNESS",
                (
                    "Trade plan is stale: current price "
                    f"is {entry_distance_atr:.4f} ATR "
                    "from planned entry"
                ),
            )

        # ==================================================
        # 9. SPREAD GUARD
        # ==================================================

        spread = self._float(
            getattr(
                state,
                "spread",
                0.0,
            ),
            0.0,
        )

        if spread < 0:

            return self._block(
                state,
                "BLOCKED",
                "SPREAD",
                "Spread value is invalid",
            )

        # Temporary raw spread guard.
        # Cross-asset spread normalization belongs
        # to the future Market Specification Engine.

        max_raw_spread = 5.0

        if spread > max_raw_spread:

            return self._block(
                state,
                "BLOCKED",
                "SPREAD",
                "Spread too high",
            )

        # ==================================================
        # 10. SESSION GATE
        # ==================================================

        session = self._dictionary(
            market.get(
                "session",
                {},
            )
        )

        session_name = str(
            session.get(
                "name",
                "UNKNOWN",
            )
        ).upper().strip()

        if session_name == "CLOSED":

            return self._block(
                state,
                "BLOCKED",
                "SESSION",
                "Market closed",
            )

        # ==================================================
        # 11. AUTHORIZATION ID
        # ==================================================

        symbol = str(
            market.get(
                "symbol",
                getattr(
                    state,
                    "symbol",
                    "UNKNOWN",
                ),
            )
        ).upper().strip()

        authorization_id = (

            f"{symbol}:"

            f"{decision}:"

            f"{entry:.8f}:"

            f"{stop_loss:.8f}:"

            f"{position_size:.8f}:"

            f"{risk_percent:.4f}"

        )

        # ==================================================
        # Deterministic broker-facing identity derived from the
        # canonical execution authorization identity.
        client_order_id = (
            "JQX-"
            + hashlib.sha256(
                authorization_id.encode("utf-8")
            ).hexdigest()[:32]
        )

        # 12. EXECUTION AUTHORIZATION
        # ==================================================

        state.execution = {

            "ready": True,

            "approved": True,

            "status": "EXECUTE",

            "gate": "AUTHORIZED",

            "reason": "Execution authorized",

            "mode": config.get_execution_mode(),

            "broker": "Paper",
            "symbol": symbol,

            "decision": decision,

            "entry": entry,

            "stop_loss": stop_loss,

            "targets": normalized_targets,

            "position_size": position_size,
            "risk_amount": risk_amount,

            "risk_percent": risk_percent,

            "structural_readiness": (
                structural_readiness
            ),

            "location_quality": (
                location_quality
            ),

            "entry_distance_atr": round(
                entry_distance_atr,
                4,
            ),

            "authorization_id": authorization_id,
            "client_order_id": client_order_id,

            # Canonical market identity propagated from the
            # live-loader market metadata boundary.
            "instrument_token": market_metadata.get(
                "instrument_token"
            ),

            # Canonical execution timeframe propagated from
            # MarketState rather than reconstructed downstream.
            "timeframe": str(
                getattr(
                    state,
                    "timeframe",
                    "",
                )
                or ""
            ).strip(),

        }

        # ==================================================
        # DEBUG
        # ==================================================

        print()

        print(
            "========== EXECUTION GATEWAY DEBUG =========="
        )

        print(
            "Decision          :",
            decision,
        )

        print(
            "Structural Ready  :",
            structural_readiness,
        )

        print(
            "Location Quality  :",
            location_quality,
        )

        print(
            "Entry             :",
            entry,
        )

        print(
            "Current Price     :",
            current_price,
        )

        print(
            "Entry Distance ATR:",
            round(
                entry_distance_atr,
                4,
            ),
        )

        print(
            "Position Size     :",
            position_size,
        )

        print(
            "Authorization ID  :",
            authorization_id,
        )

        print(
            "Execution         : AUTHORIZED"
        )

        print(
            "=" * 47
        )

        return state
