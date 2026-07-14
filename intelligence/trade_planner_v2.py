"""
Jaguar Quant X Enterprise
Trade Planner V3.0

Canonical structure-aware trade planning engine.

Authority chain:

    Institutional Decision Matrix
        ->
    Structural Zone
        ->
    Trade Planner
        ->
    Risk Manager
        ->
    Execution Gateway

Purpose:
- Accept only IDM ENTER_LONG / ENTER_SHORT authority
- Consume canonical Structural Zone contract
- Build entry from confirmed execution location
- Build stop from structural invalidation
- Use ATR only as a structural safety buffer
- Derive targets from realized trade risk
- Produce a normalized enterprise trade contract

IMPORTANT:
This engine does not approve trades.
It does not create directional evidence.
It does not override IDM.
It only converts an approved institutional setup
into a structure-aware trade plan.
"""


class TradePlannerV2:

    name = "Trade Planner V3"

    # ==================================================
    # SAFE HELPERS
    # ==================================================

    @staticmethod
    def _dictionary(value):

        if isinstance(
            value,
            dict,
        ):
            return value

        return {}

    @staticmethod
    def _float(
        value,
        default=0.0,
    ):

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

            return float(
                default
            )

    @staticmethod
    def _unique(values):

        return list(
            dict.fromkeys(
                values
            )
        )

    # ==================================================
    # EMPTY TRADE CONTRACT
    # ==================================================

    @staticmethod
    def _empty_trade(
        decision="WAIT",
        reason="IDM has not authorized a trade.",
    ):

        return {

            "direction": "NONE",

            "decision": decision,

            "entry": None,

            "stop_loss": None,

            "targets": [],

            "risk": 0.0,

            "risk_reward": 0.0,

            "zone_type": "NONE",

            "zone_low": 0.0,

            "zone_high": 0.0,

            "zone_lifecycle": "UNKNOWN",

            "location_quality": "NONE",

            "readiness": "WAITING",

            "status": "NO TRADE",

            "ready": False,

            "reasons": [
                reason
            ],

        }

    # ==================================================
    # PROCESS
    # ==================================================

    def process(self, state):

        # ==================================================
        # READ IDM CONTRACT
        # ==================================================

        idm = self._dictionary(
            getattr(
                state,
                "idm",
                {},
            )
        )

        decision = str(
            idm.get(
                "decision",
                "WAIT",
            )
        ).upper().strip()

        # ==================================================
        # IDM AUTHORITY GATE
        # ==================================================

        if decision not in (
            "ENTER_LONG",
            "ENTER_SHORT",
        ):

            state.trade = self._empty_trade(
                decision=decision,
                reason=(
                    "IDM has not authorized "
                    "an executable trade."
                ),
            )

            return state

        # ==================================================
        # READ STRUCTURAL ZONE CONTRACT
        # ==================================================

        structural_zone = self._dictionary(
            getattr(
                state,
                "structural_zone",
                {},
            )
        )

        zone_status = str(
            structural_zone.get(
                "zone_status",
                "NONE",
            )
        ).upper().strip()

        zone_type = str(
            structural_zone.get(
                "zone_type",
                "NONE",
            )
        ).upper().strip()

        zone_direction = str(
            structural_zone.get(
                "zone_direction",
                "NEUTRAL",
            )
        ).upper().strip()

        zone_lifecycle = str(
            structural_zone.get(
                "zone_lifecycle",
                "UNKNOWN",
            )
        ).upper().strip()

        zone_low = self._float(
            structural_zone.get(
                "zone_low",
                0.0,
            )
        )

        zone_high = self._float(
            structural_zone.get(
                "zone_high",
                0.0,
            )
        )

        interacting = bool(
            structural_zone.get(
                "interacting",
                False,
            )
        )

        location_quality = str(
            structural_zone.get(
                "location_quality",
                "NONE",
            )
        ).upper().strip()

        readiness = str(
            structural_zone.get(
                "readiness",
                "WAITING",
            )
        ).upper().strip()

        # ==================================================
        # BASIC MARKET FACTS
        # ==================================================

        price = self._float(
            getattr(
                state,
                "price",
                0.0,
            )
        )

        atr = self._float(
            getattr(
                state,
                "atr",
                0.0,
            )
        )

        # ==================================================
        # EXPECTED DIRECTION
        # ==================================================

        if decision == "ENTER_LONG":

            direction = "BULLISH"

        else:

            direction = "BEARISH"

        # ==================================================
        # STRUCTURAL CONTRACT VALIDATION
        # ==================================================

        reasons = []

        if zone_status != "AVAILABLE":

            state.trade = self._empty_trade(
                decision=decision,
                reason=(
                    "IDM authorized direction but "
                    "no structural zone is available."
                ),
            )

            return state

        if zone_direction != direction:

            state.trade = self._empty_trade(
                decision=decision,
                reason=(
                    "Structural zone direction conflicts "
                    "with IDM trade direction."
                ),
            )

            return state

        if zone_low <= 0 or zone_high <= 0:

            state.trade = self._empty_trade(
                decision=decision,
                reason=(
                    "Structural zone boundaries "
                    "are invalid."
                ),
            )

            return state

        if zone_low > zone_high:

            zone_low, zone_high = (
                zone_high,
                zone_low,
            )

        if zone_lifecycle in (
            "MITIGATED",
            "FILLED",
            "INVALID",
            "BROKEN",
        ):

            state.trade = self._empty_trade(
                decision=decision,
                reason=(
                    "Structural execution zone "
                    "is no longer valid."
                ),
            )

            return state

        if readiness != "CONFIRMED":

            state.trade = self._empty_trade(
                decision=decision,
                reason=(
                    "Structural execution location "
                    "is not confirmed."
                ),
            )

            return state

        if not interacting:

            state.trade = self._empty_trade(
                decision=decision,
                reason=(
                    "Price is not interacting with "
                    "the approved structural zone."
                ),
            )

            return state

        if price <= 0:

            state.trade = self._empty_trade(
                decision=decision,
                reason=(
                    "Current market price is invalid."
                ),
            )

            return state

        if atr <= 0:

            state.trade = self._empty_trade(
                decision=decision,
                reason=(
                    "ATR is unavailable for structural "
                    "risk buffering."
                ),
            )

            return state

        # ==================================================
        # ENTRY
        #
        # IDM already requires confirmed zone interaction.
        # Therefore current interacting market price is the
        # canonical executable reference price.
        # ==================================================

        entry = price

        # ==================================================
        # STRUCTURAL INVALIDATION BUFFER
        #
        # Structure defines invalidation.
        # ATR only protects the structural boundary from
        # ordinary market noise.
        # ==================================================

        ATR_BUFFER_MULTIPLIER = 0.25

        structural_buffer = (
            atr
            * ATR_BUFFER_MULTIPLIER
        )

        if direction == "BULLISH":

            stop = (
                zone_low
                - structural_buffer
            )

        else:

            stop = (
                zone_high
                + structural_buffer
            )

        # ==================================================
        # STOP VALIDATION
        # ==================================================

        if (
            direction == "BULLISH"
            and stop >= entry
        ):

            state.trade = self._empty_trade(
                decision=decision,
                reason=(
                    "Bullish structural stop is not "
                    "below entry."
                ),
            )

            return state

        if (
            direction == "BEARISH"
            and stop <= entry
        ):

            state.trade = self._empty_trade(
                decision=decision,
                reason=(
                    "Bearish structural stop is not "
                    "above entry."
                ),
            )

            return state

        # ==================================================
        # REALIZED STRUCTURAL RISK
        # ==================================================

        risk = abs(
            entry
            - stop
        )

        if risk <= 0:

            state.trade = self._empty_trade(
                decision=decision,
                reason=(
                    "Trade risk distance is invalid."
                ),
            )

            return state

        # ==================================================
        # R-MULTIPLE TARGETS
        # ==================================================

        if direction == "BULLISH":

            tp1 = (
                entry
                + risk
            )

            tp2 = (
                entry
                + (
                    2 * risk
                )
            )

            tp3 = (
                entry
                + (
                    3 * risk
                )
            )

        else:

            tp1 = (
                entry
                - risk
            )

            tp2 = (
                entry
                - (
                    2 * risk
                )
            )

            tp3 = (
                entry
                - (
                    3 * risk
                )
            )

        # ==================================================
        # PLAN REASONS
        # ==================================================

        reasons.extend([

            (
                f"IDM authorized "
                f"{decision}."
            ),

            (
                f"{zone_type.replace('_', ' ').title()} "
                f"structural zone confirmed."
            ),

            (
                "Price is interacting with "
                "the approved execution location."
            ),

            (
                "Stop loss is placed beyond structural "
                "invalidation with ATR buffer."
            ),

            (
                "Targets are derived from structural "
                "risk using R multiples."
            ),

        ])

        reasons = self._unique(
            reasons
        )

        # ==================================================
        # ENTERPRISE TRADE CONTRACT
        # ==================================================

        state.trade = {

            "direction": direction,

            "decision": decision,

            "entry": round(
                entry,
                2,
            ),

            "stop_loss": round(
                stop,
                2,
            ),

            "targets": [

                round(
                    tp1,
                    2,
                ),

                round(
                    tp2,
                    2,
                ),

                round(
                    tp3,
                    2,
                ),

            ],

            "risk": round(
                risk,
                2,
            ),

            "risk_reward": 2.0,

            "zone_type": zone_type,

            "zone_low": round(
                zone_low,
                2,
            ),

            "zone_high": round(
                zone_high,
                2,
            ),

            "zone_lifecycle": zone_lifecycle,

            "location_quality": location_quality,

            "readiness": readiness,

            "status": "READY",

            "ready": True,

            "reasons": reasons,

        }

        # ==================================================
        # DEBUG
        # ==================================================

        print()

        print(
            "========== TRADE PLANNER DEBUG =========="
        )

        print(
            "Decision       :",
            decision,
        )

        print(
            "Direction      :",
            direction,
        )

        print(
            "Zone Type      :",
            zone_type,
        )

        print(
            "Zone Lifecycle :",
            zone_lifecycle,
        )

        print(
            "Zone Low       :",
            round(
                zone_low,
                2,
            ),
        )

        print(
            "Zone High      :",
            round(
                zone_high,
                2,
            ),
        )

        print(
            "Interacting    :",
            interacting,
        )

        print(
            "Readiness      :",
            readiness,
        )

        print(
            "Entry          :",
            round(
                entry,
                2,
            ),
        )

        print(
            "Stop Loss      :",
            round(
                stop,
                2,
            ),
        )

        print(
            "Risk           :",
            round(
                risk,
                2,
            ),
        )

        print(
            "TP1            :",
            round(
                tp1,
                2,
            ),
        )

        print(
            "TP2            :",
            round(
                tp2,
                2,
            ),
        )

        print(
            "TP3            :",
            round(
                tp3,
                2,
            ),
        )

        print(
            "========================================="
        )

        return state
