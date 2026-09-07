"""
Jaguar Quant X Enterprise
Institutional Decision Matrix V3.0

Structural-zone aware institutional decision engine.

Canonical authority model:

    Institutional Score
            +
    Jaguar Brain
            +
    Structural Zone Intelligence
            |
            v
    Institutional Decision Matrix

The IDM does not create market evidence.

It interprets normalized enterprise facts and classifies
the current market opportunity into:

- CONTINUATION
- REVERSAL
- STRUCTURAL_WAIT
- CONFLICT
- AVOID

Structural Zone Engine is the canonical synthesized
structure and execution-location intelligence layer.

Raw specialist engine signals remain supporting evidence.
"""


class InstitutionalDecisionMatrix:

    name = "Institutional Decision Matrix V3"

    # ==================================================
    # SIGNAL NORMALIZATION
    # ==================================================

    @staticmethod
    def _signal(value):

        if isinstance(value, dict):

            signal = str(
                value.get(
                    "signal",
                    "NEUTRAL",
                )
            ).upper().strip()

        elif isinstance(value, str):

            signal = value.upper().strip()

        else:

            signal = "NEUTRAL"

        if signal in (
            "BULLISH",
            "BEARISH",
            "NEUTRAL",
            "SIDEWAYS",
            "UNKNOWN",
        ):

            return signal

        return "NEUTRAL"

    # ==================================================
    # MARKET
    # ==================================================

    @staticmethod
    def _market(state):

        market = getattr(
            state,
            "market",
            {},
        )

        if not isinstance(
            market,
            dict,
        ):

            return {}

        return market

    # ==================================================
    # MARKET SIGNAL
    # ==================================================

    @classmethod
    def _market_signal(
        cls,
        state,
        key,
    ):

        market = cls._market(
            state
        )

        signal_key = (
            f"{key}_signal"
        )

        if signal_key in market:

            return cls._signal(
                market.get(
                    signal_key
                )
            )

        result_key = (
            f"{key}_result"
        )

        if result_key in market:

            return cls._signal(
                market.get(
                    result_key
                )
            )

        return cls._signal(
            market.get(
                key,
                "NEUTRAL",
            )
        )

    # ==================================================
    # STRUCTURAL ZONE CONTRACT
    # ==================================================

    @classmethod
    def _structural_zone(
        cls,
        state,
    ):

        structural_zone = getattr(
            state,
            "structural_zone",
            None,
        )

        if isinstance(
            structural_zone,
            dict,
        ):

            return structural_zone

        market = cls._market(
            state
        )

        structural_zone = market.get(
            "structural_zone",
            {},
        )

        if isinstance(
            structural_zone,
            dict,
        ):

            return structural_zone

        return {}

    # ==================================================
    # SAFE FLOAT
    # ==================================================

    @staticmethod
    def _float(
        value,
        default=0.0,
    ):

        try:

            return float(
                value
                or default
            )

        except (
            TypeError,
            ValueError,
        ):

            return float(
                default
            )

    # ==================================================
    # UNIQUE VALUES
    # ==================================================

    @staticmethod
    def _unique(values):

        return list(
            dict.fromkeys(
                values
            )
        )

    # ==================================================
    # PROCESS
    # ==================================================

    def process(self, state):

        # ==================================================
        # ENTERPRISE INPUTS
        # ==================================================

        institutional = getattr(
            state,
            "institutional",
            {},
        )

        if not isinstance(
            institutional,
            dict,
        ):

            institutional = {}

        brain = getattr(
            state,
            "brain",
            {},
        )

        if not isinstance(
            brain,
            dict,
        ):

            brain = {}

        structural_zone = self._structural_zone(
            state
        )

        # ==================================================
        # INSTITUTIONAL FACTS
        # ==================================================

        score = self._float(
            institutional.get(
                "score",
                0,
            )
        )

        confidence = self._float(
            institutional.get(
                "confidence",
                0,
            )
        )

        direction = str(
            institutional.get(
                "direction",
                "NEUTRAL",
            )
        ).upper().strip()

        trend = str(
            getattr(
                state,
                "trend",
                "UNKNOWN",
            )
        ).upper().strip()

        raw_regime = getattr(
            state,
            "regime",
            "UNKNOWN",
        )

        if isinstance(raw_regime, dict):
            regime = str(
                raw_regime.get(
                    "REGIME",
                    raw_regime.get(
                        "regime",
                        "UNKNOWN",
                    ),
                )
            ).upper().strip()
        else:
            regime = str(
                raw_regime
            ).upper().strip()

        conflicts = brain.get(
            "conflicts",
            [],
        )

        if not isinstance(
            conflicts,
            list,
        ):

            conflicts = []

        institutional_execution_conflicts = institutional.get(
            "execution_conflicts",
            [],
        )

        if not isinstance(
            institutional_execution_conflicts,
            list,
        ):
            institutional_execution_conflicts = []

        # ==================================================
        # INSTITUTIONAL QUALITY GATE
        # ==================================================
        # A structurally valid setup is not automatically
        # executable. Continuation entries require strong
        # institutional evidence.
        #
        # D/F quality must remain WAIT even when structural
        # execution conditions are otherwise satisfied.
        # ==================================================

        institutional_grade = str(
            institutional.get(
                "grade",
                "F",
            )
        ).upper().strip()

        institutional_quality_ok = (
            institutional_grade in (
                "A+",
                "A",
                "B",
                "C",
            )
            and score >= 60
            and confidence >= 65
        )

        conflicts = list(
            dict.fromkeys(
                conflicts
                + institutional_execution_conflicts
            )
        )

        # ==================================================
        # RAW SPECIALIST SIGNALS
        #
        # Supporting evidence only.
        # ==================================================

        bos = self._market_signal(
            state,
            "bos",
        )

        choch = self._market_signal(
            state,
            "choch",
        )

        liquidity = self._market_signal(
            state,
            "liquidity",
        )

        order_block = self._market_signal(
            state,
            "order_block",
        )

        fvg = self._market_signal(
            state,
            "fvg",
        )

        discount = bool(
            getattr(
                state,
                "discount",
                False,
            )
        )

        premium = bool(
            getattr(
                state,
                "premium",
                False,
            )
        )

        # ==================================================
        # CANONICAL STRUCTURAL ZONE FACTS
        # ==================================================

        structural_direction = str(
            structural_zone.get(
                "direction",
                "NEUTRAL",
            )
        ).upper().strip()

        structure_state = str(
            structural_zone.get(
                "structure_state",
                "UNDEFINED",
            )
        ).upper().strip()

        trigger_status = str(
            structural_zone.get(
                "trigger_status",
                "NONE",
            )
        ).upper().strip()

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

        interacting = bool(
            structural_zone.get(
                "interacting",
                False,
            )
        )

        distance_atr = self._float(
            structural_zone.get(
                "distance_atr",
                0.0,
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
        # CANONICAL EXECUTION TRIGGER FACTS
        # ==================================================

        execution_trigger_data = structural_zone.get(
            "execution_trigger",
            {},
        )

        if not isinstance(
            execution_trigger_data,
            dict,
        ):
            execution_trigger_data = {}

        execution_trigger = str(
            execution_trigger_data.get(
                "status",
                "NONE",
            )
        ).upper().strip()

        trigger_confirmed = bool(
            execution_trigger_data.get(
                "confirmed",
                False,
            )
        )

        trigger_source = str(
            execution_trigger_data.get(
                "source",
                "NONE",
            )
        ).upper().strip()

        trigger_direction = str(
            execution_trigger_data.get(
                "direction",
                "NEUTRAL",
            )
        ).upper().strip()

        trigger_lifecycle = str(
            execution_trigger_data.get(
                "lifecycle",
                "UNKNOWN",
            )
        ).upper().strip()

        trigger_reason = str(
            execution_trigger_data.get(
                "reason",
                "No execution trigger confirmed",
            )
        ).strip()

        # ==================================================
        # OUTPUT DEFAULTS
        # ==================================================

        decision = "WAIT"

        priority = "LOW"

        setup = "STRUCTURAL_WAIT"

        reasons = []

        confirmed = []

        missing = []

        # ==================================================
        # STRUCTURAL SEMANTICS
        # ==================================================

        structural_trigger = (
            trigger_status
            in (
                "BOS_CONFIRMED",
                "CHOCH_CONFIRMED",
            )
        )

        structure_confirmed = (
            structure_state
            in (
                "STRUCTURE_BREAK",
                "CHARACTER_CHANGE",
                "PROTECTED",
            )
        )

        zone_available = (
            zone_status == "AVAILABLE"
        )

        zone_aligned = (
            zone_direction == direction
            and direction
            in (
                "BULLISH",
                "BEARISH",
            )
        )

        zone_valid = (
            zone_lifecycle
            not in (
                "MITIGATED",
                "FILLED",
                "INVALID",
                "INVALIDATED",
                "BROKEN",
            )
        )
        location_confirmed = (
            readiness == "CONFIRMED"
        )

        location_active = (
            readiness
            in (
                "CONFIRMED",
                "ZONE_INTERACTION",
            )
        )

        location_near = (
            readiness == "APPROACHING"
            or location_quality
            in (
                "NEAR",
                "APPROACHING",
            )
        )

        structural_alignment = (
            structural_direction == direction
            and direction
            in (
                "BULLISH",
                "BEARISH",
            )
        )

        trigger_fresh = bool(
            execution_trigger_data.get(
                "fresh",
                False,
            )
        )

        execution_trigger_confirmed = (
            execution_trigger == "CONFIRMED"
            and trigger_confirmed
            and trigger_fresh
            and trigger_source in (
                "LIQUIDITY",
                "ORDER_BLOCK",
                "FVG",
            )
            and trigger_direction == direction
            and direction in (
                "BULLISH",
                "BEARISH",
            )
        )

        execution_trigger_conflict = (
            execution_trigger
            in (
                "CONFIRMED",
                "DIRECTION_CONFLICT",
            )
            and trigger_direction
            in (
                "BULLISH",
                "BEARISH",
            )
            and direction
            in (
                "BULLISH",
                "BEARISH",
            )
            and trigger_direction != direction
        )

        # ==================================================
        # CONFIRMED FACTS
        # ==================================================

        if trend == direction:

            confirmed.append(
                "TREND"
            )

        if regime == direction:

            confirmed.append(
                "REGIME"
            )

        if structural_alignment:

            confirmed.append(
                "STRUCTURAL_DIRECTION"
            )

        if structure_confirmed:

            confirmed.append(
                "STRUCTURE"
            )

        if structural_trigger:

            confirmed.append(
                trigger_status
            )

        if zone_available:

            confirmed.append(
                "ZONE_AVAILABLE"
            )

        if zone_aligned:

            confirmed.append(
                "ZONE_ALIGNED"
            )

        if zone_valid:

            confirmed.append(
                "ZONE_VALID"
            )

        if interacting:

            confirmed.append(
                "ZONE_INTERACTION"
            )

        if location_confirmed:

            confirmed.append(
                "LOCATION_CONFIRMED"
            )

        elif location_near:

            confirmed.append(
                "LOCATION_APPROACHING"
            )

        if execution_trigger_confirmed:

            confirmed.append(
                "EXECUTION_TRIGGER"
            )

            confirmed.append(
                f"{trigger_source}_TRIGGER"
            )

        # ==================================================
        # DIRECTION CONFLICT
        # ==================================================

        direction_conflict = False


        # Confirmed CHOCH has structural authority over the prior trend.

        # Therefore a confirmed reversal is not a trend conflict.

        confirmed_reversal_direction = (
            choch in (
                "BULLISH",
                "BEARISH",
            )
            and trigger_status == "CHOCH_CONFIRMED"
            and choch == direction
        )

        if not confirmed_reversal_direction:


            if (

                trend == "BULLISH"

                and direction == "BEARISH"

            ):


                direction_conflict = True


            elif (

                trend == "BEARISH"

                and direction == "BULLISH"

            ):


                direction_conflict = True


        structural_conflict = (
            structural_direction
            in (
                "BULLISH",
                "BEARISH",
            )
            and direction
            in (
                "BULLISH",
                "BEARISH",
            )
            and structural_direction
            != direction
        )

        zone_conflict = (
            zone_available
            and zone_direction
            in (
                "BULLISH",
                "BEARISH",
            )
            and direction
            in (
                "BULLISH",
                "BEARISH",
            )
            and zone_direction
            != direction
        )

        # ==================================================
        # STRUCTURAL DIRECTION PENDING
        # ==================================================
        #
        # Institutional evidence may establish a directional
        # bias before canonical market structure confirms the
        # same direction.
        #
        # A confirmed execution-zone reaction is not sufficient
        # to authorize execution while structural direction is
        # unresolved.
        #
        # This state is WAIT, not CONFLICT and not AVOID.
        # ==================================================

        if (
            readiness == "NO_DIRECTION"
            or execution_trigger == "AWAITING_DIRECTION"
        ):

            setup = "STRUCTURAL_WAIT"

            decision = "WAIT"

            priority = (
                "HIGH"
                if (
                    zone_available
                    and zone_aligned
                    and zone_valid
                    and location_active
                    and trigger_direction
                    in (
                        "BULLISH",
                        "BEARISH",
                    )
                    and trigger_direction == direction
                )
                else "MEDIUM"
            )

            missing.append(
                "STRUCTURAL_DIRECTION"
            )

            if not structure_confirmed:

                missing.append(
                    "STRUCTURAL_CONFIRMATION"
                )

            if not structural_trigger:

                missing.append(
                    "STRUCTURAL_TRIGGER"
                )

            reasons.append(
                "Institutional direction is established, "
                "but canonical structural direction is "
                "awaiting confirmation."
            )

            if (
                zone_available
                and zone_aligned
                and zone_valid
                and location_active
                and trigger_direction
                in (
                    "BULLISH",
                    "BEARISH",
                )
                and trigger_direction == direction
            ):

                confirmed.append(
                    "ALIGNED_EXECUTION_LOCATION"
                )

                reasons.append(
                    "Aligned execution-zone reaction is "
                    "confirmed, but entry remains blocked "
                    "until structural direction is established."
                )

        # ==================================================
        # CONFLICT
        # ==================================================

        elif (
            direction_conflict
            or structural_conflict
            or zone_conflict
            or readiness == "CONFLICT"
        ):

            setup = "CONFLICT"

            decision = "WAIT"

            priority = "LOW"

            if direction_conflict:

                missing.append(
                    "DIRECTION_ALIGNMENT"
                )

                reasons.append(
                    "Institutional direction conflicts "
                    "with market trend."
                )

            if structural_conflict:

                missing.append(
                    "STRUCTURAL_DIRECTION"
                )

                reasons.append(
                    "Structural direction conflicts "
                    "with institutional direction."
                )

            if zone_conflict:

                missing.append(
                    "ZONE_ALIGNMENT"
                )

                reasons.append(
                    "Structural zone direction conflicts "
                    "with institutional direction."
                )

        # ==================================================
        # INVALID STRUCTURAL LOCATION
        # ==================================================

        elif readiness == "INVALID_ZONE":

            setup = "STRUCTURAL_WAIT"

            decision = "WAIT"

            priority = "LOW"

            missing.append(
                "VALID_ZONE"
            )

            reasons.append(
                "Structural trigger exists but the "
                "selected execution zone is invalid."
            )

        # ==================================================
        # BULLISH CONTINUATION
        # ==================================================

        elif (
            direction == "BULLISH"
            and structural_alignment
            and structure_confirmed
            and structural_trigger
        ):

            setup = "CONTINUATION"

            confirmed.extend([
                "BULLISH_TREND",
                "BULLISH_REGIME",
                "BULLISH_DIRECTION",
            ])

            # ----------------------------------------------
            # EXECUTABLE STRUCTURAL CONTINUATION
            # ----------------------------------------------

            if (
                structural_alignment
                and structural_trigger
                and structure_confirmed
                and zone_available
                and zone_aligned
                and zone_valid
                and location_active
                and execution_trigger_confirmed
                and trend == "BULLISH"
                and regime in ("BREAKOUT", "TREND")
                and institutional_quality_ok
                and len(conflicts) == 0
                and len(institutional_execution_conflicts) == 0
                and direction == "BULLISH"
            ):

                decision = "ENTER_LONG"

                priority = "HIGH"

                reasons.append(
                    "Bullish continuation confirmed by "
                    "macro structure, active execution "
                    "location, and directional execution "
                    "trigger."
                )

            # ----------------------------------------------
            # EXECUTION TRIGGER DIRECTION CONFLICT
            # ----------------------------------------------

            elif (
                structural_alignment
                and zone_available
                and zone_aligned
                and zone_valid
                and location_active
                and execution_trigger_conflict
            ):

                decision = "WAIT"

                priority = "HIGH"

                missing.append(
                    "EXECUTION_TRIGGER_ALIGNMENT"
                )

                reasons.append(
                    "Bullish execution location is active "
                    "but the execution trigger direction "
                    "conflicts with institutional direction."
                )

            # ----------------------------------------------
            # ACTIVE LOCATION / EXECUTION TRIGGER PENDING
            # ----------------------------------------------

            elif (
                structural_alignment
                and structural_trigger
                and structure_confirmed
                and zone_available
                and zone_aligned
                and zone_valid
                and location_active
                and not execution_trigger_confirmed
            ):

                decision = "WAIT"

                priority = "HIGH"

                missing.append(
                    "EXECUTION_TRIGGER"
                )

                reasons.append(
                    "Bullish execution location is active "
                    "but execution trigger confirmation "
                    "is incomplete."
                )

            # ----------------------------------------------
            # APPROACHING EXECUTION LOCATION
            # ----------------------------------------------

            elif (
                structural_alignment
                and zone_available
                and zone_aligned
                and zone_valid
                and location_near
            ):

                decision = "WAIT"

                priority = "MEDIUM"

                missing.append(
                    "ZONE_INTERACTION"
                )

                reasons.append(
                    "Bullish structure is confirmed and "
                    "price is approaching the execution "
                    "location."
                )

            # ----------------------------------------------
            # CONFIRMED STRUCTURE / DISTANT VALID LOCATION
            # ----------------------------------------------

            elif (
                structural_alignment
                and structure_confirmed
                and zone_available
                and zone_aligned
                and zone_valid
                and not location_active
                and not location_near
                and not structural_trigger
            ):

                decision = "WAIT"

                priority = "LOW"

                missing.extend([
                    "EXECUTION_LOCATION_CONFIRMATION",
                    "STRUCTURAL_TRIGGER",
                ])

                reasons.append(
                    "Bullish structure is established and an aligned "
                    "valid execution zone exists, but price has not "
                    "reached the execution location and BOS / CHOCH "
                    "confirmation is pending."
                )
            # STRUCTURE CONFIRMED / NO LOCATION
            # ----------------------------------------------

            elif (
                structural_alignment
                and structural_trigger
                and structure_confirmed
                and (
                    not zone_available
                    or not zone_aligned
                    or not zone_valid
                )
            ):

                decision = "WAIT"

                priority = "MEDIUM"

                missing.append(
                    "EXECUTION_LOCATION"
                )

                reasons.append(
                    "Bullish structure is confirmed but "
                    "no valid aligned structural execution "
                    "location is active."
                )

            else:

                decision = "WAIT"

                priority = "MEDIUM"

                missing.append(
                    "STRUCTURAL_CONFIRMATION"
                )

                reasons.append(
                    "Bullish continuation bias awaiting "
                    "structural confirmation."
                )

        # ==================================================
        # BEARISH CONTINUATION
        # ==================================================

        elif (
            direction == "BEARISH"
            and structural_alignment
            and structure_confirmed
            and structural_trigger
        ):

            setup = "CONTINUATION"

            confirmed.extend([
                "STRUCTURAL_DIRECTION",
                "STRUCTURE",
                "STRUCTURAL_TRIGGER",
            ])

            # ----------------------------------------------
            # EXECUTABLE STRUCTURAL CONTINUATION
            # ----------------------------------------------

            if (
                structural_alignment
                and structural_trigger
                and structure_confirmed
                and zone_available
                and zone_aligned
                and zone_valid
                and location_active
                and execution_trigger_confirmed
                and institutional_quality_ok
                and len(conflicts) == 0
                and len(institutional_execution_conflicts) == 0
            ):

                decision = "ENTER_SHORT"

                priority = "HIGH"

                reasons.append(
                    "Bearish continuation confirmed by "
                    "macro structure, active execution "
                    "location, and directional execution "
                    "trigger."
                )

            # ----------------------------------------------
            # EXECUTION TRIGGER DIRECTION CONFLICT
            # ----------------------------------------------

            elif (
                structural_alignment
                and zone_available
                and zone_aligned
                and zone_valid
                and location_active
                and execution_trigger_conflict
            ):

                decision = "WAIT"

                priority = "HIGH"

                missing.append(
                    "EXECUTION_TRIGGER_ALIGNMENT"
                )

                reasons.append(
                    "Bearish execution location is active "
                    "but the execution trigger direction "
                    "conflicts with institutional direction."
                )

            # ----------------------------------------------
            # ACTIVE LOCATION / EXECUTION TRIGGER PENDING
            # ----------------------------------------------

            elif (
                structural_alignment
                and structural_trigger
                and structure_confirmed
                and zone_available
                and zone_aligned
                and zone_valid
                and location_active
                and not execution_trigger_confirmed
            ):

                decision = "WAIT"

                priority = "HIGH"

                missing.append(
                    "EXECUTION_TRIGGER"
                )

                reasons.append(
                    "Bearish execution location is active "
                    "but execution trigger confirmation "
                    "is incomplete."
                )

            # ----------------------------------------------
            # APPROACHING EXECUTION LOCATION
            # ----------------------------------------------

            elif (
                structural_alignment
                and zone_available
                and zone_aligned
                and zone_valid
                and location_near
            ):

                decision = "WAIT"

                priority = "MEDIUM"

                missing.append(
                    "ZONE_INTERACTION"
                )

                reasons.append(
                    "Bearish structure is confirmed and "
                    "price is approaching the execution "
                    "location."
                )
            # ----------------------------------------------
            # CONFIRMED STRUCTURE / DISTANT VALID LOCATION
            # ----------------------------------------------

            elif (
                structural_alignment
                and structure_confirmed
                and zone_available
                and zone_aligned
                and zone_valid
                and not location_active
                and not location_near
                and not structural_trigger
            ):

                decision = "WAIT"

                priority = "LOW"

                missing.extend([
                    "EXECUTION_LOCATION_CONFIRMATION",
                    "STRUCTURAL_TRIGGER",
                ])

                reasons.append(
                    "Bearish structure is established and an aligned "
                    "valid execution zone exists, but price has not "
                    "reached the execution location and BOS / CHOCH "
                    "confirmation is pending."
                )
            # ----------------------------------------------
            # STRUCTURE CONFIRMED / NO LOCATION
            # ----------------------------------------------

            elif (
                structural_alignment
                and structural_trigger
                and structure_confirmed
                and (
                    not zone_available
                    or not zone_aligned
                    or not zone_valid
                )
            ):

                decision = "WAIT"

                priority = "MEDIUM"

                missing.append(
                    "EXECUTION_LOCATION"
                )

                reasons.append(
                    "Bearish structure is confirmed but "
                    "no valid aligned structural execution "
                    "location is active."
                )

            else:

                decision = "WAIT"

                priority = "MEDIUM"

                if not structural_alignment:

                    missing.append(
                        "STRUCTURAL_DIRECTION"
                    )

                    reasons.append(
                        "Bearish continuation bias awaiting "
                        "structural direction alignment."
                    )

                elif not structure_confirmed:

                    missing.append(
                        "STRUCTURAL_CONFIRMATION"
                    )

                    reasons.append(
                        "Bearish continuation bias awaiting "
                        "structural confirmation."
                    )

                elif not structural_trigger:

                    missing.append(
                        "STRUCTURAL_TRIGGER"
                    )

                    reasons.append(
                        "Bearish structure is established but "
                        "BOS / CHOCH confirmation is pending."
                    )

                elif not zone_available:

                    missing.append(
                        "EXECUTION_LOCATION"
                    )

                    reasons.append(
                        "Bearish structure is confirmed but "
                        "no structural execution location "
                        "is available."
                    )

                elif not zone_aligned:

                    missing.append(
                        "ZONE_ALIGNMENT"
                    )

                    reasons.append(
                        "Bearish structure is confirmed but "
                        "the available execution location "
                        "is not directionally aligned."
                    )

                elif not zone_valid:

                    missing.append(
                        "VALID_ZONE"
                    )

                    reasons.append(
                        "Bearish structure is confirmed but "
                        "the aligned execution location "
                        "is no longer valid."
                    )

                elif not location_active:

                    missing.append(
                        "EXECUTION_LOCATION_CONFIRMATION"
                    )

                    reasons.append(
                        "Bearish structure is confirmed and "
                        "an aligned execution location exists, "
                        "but price has not reached the active "
                        "execution area."
                    )

                elif not execution_trigger_confirmed:

                    missing.append(
                        "EXECUTION_TRIGGER"
                    )

                    reasons.append(
                        "Bearish execution location is active "
                        "but execution trigger confirmation "
                        "is incomplete."
                    )

                else:

                    missing.append(
                        "SETUP_CONFIRMATION"
                    )

                    reasons.append(
                        "Bearish continuation setup remains "
                        "incomplete."
                    )
        # ==================================================
        # BULLISH REVERSAL
        # ==================================================

        elif (
            direction == "BULLISH"
            and (
                choch == "BULLISH"
                or trigger_status == "CHOCH_CONFIRMED"
            )
        ):

            setup = "REVERSAL"

            confirmed.extend([
                "BULLISH_CHOCH",
                "BULLISH_DIRECTION",
            ])

            if (
                structural_alignment
                and structure_state == "CHARACTER_CHANGE"
                and trigger_status == "CHOCH_CONFIRMED"
                and zone_available
                and zone_aligned
                and zone_valid
                and location_confirmed
                and score >= 40
                and confidence >= 45
                and len(conflicts) == 0
            ):

                decision = "ENTER_LONG"

                priority = "HIGH"

                reasons.append(
                    "Bullish institutional reversal "
                    "confirmed at active structural "
                    "execution location."
                )

            elif (
                structural_alignment
                and structure_state == "CHARACTER_CHANGE"
                and zone_available
                and zone_aligned
                and zone_valid
                and location_near
            ):

                decision = "WAIT"

                priority = "HIGH"

                missing.append(
                    "ZONE_INTERACTION"
                )

                reasons.append(
                    "Bullish reversal structure is "
                    "confirmed and price is approaching "
                    "the execution location."
                )

            else:

                decision = "WAIT"

                priority = "MEDIUM"

                if not structural_alignment:

                    missing.append(
                        "STRUCTURAL_DIRECTION"
                    )

                    reasons.append(
                        "Bullish continuation bias awaiting "
                        "structural direction alignment."
                    )

                elif not structure_confirmed:

                    missing.append(
                        "STRUCTURAL_CONFIRMATION"
                    )

                    reasons.append(
                        "Bullish continuation bias awaiting "
                        "structural confirmation."
                    )

                elif not structural_trigger:

                    missing.append(
                        "STRUCTURAL_TRIGGER"
                    )

                    reasons.append(
                        "Bullish structure is established but "
                        "BOS / CHOCH confirmation is pending."
                    )

                elif not zone_available:

                    missing.append(
                        "EXECUTION_LOCATION"
                    )

                    reasons.append(
                        "Bullish structure is confirmed but "
                        "no structural execution location "
                        "is available."
                    )

                elif not zone_aligned:

                    missing.append(
                        "ZONE_ALIGNMENT"
                    )

                    reasons.append(
                        "Bullish structure is confirmed but "
                        "the available execution location "
                        "is not directionally aligned."
                    )

                elif not zone_valid:

                    missing.append(
                        "VALID_ZONE"
                    )

                    reasons.append(
                        "Bullish structure is confirmed but "
                        "the aligned execution location "
                        "is no longer valid."
                    )

                elif not location_active:

                    missing.append(
                        "EXECUTION_LOCATION_CONFIRMATION"
                    )

                    reasons.append(
                        "Bullish structure is confirmed and "
                        "an aligned execution location exists, "
                        "but price has not reached the active "
                        "execution area."
                    )

                elif not execution_trigger_confirmed:

                    missing.append(
                        "EXECUTION_TRIGGER"
                    )

                    reasons.append(
                        "Bullish execution location is active "
                        "but execution trigger confirmation "
                        "is incomplete."
                    )

                else:

                    missing.append(
                        "SETUP_CONFIRMATION"
                    )

                    reasons.append(
                        "Bullish continuation setup remains "
                        "incomplete."
                    )
        # ==================================================
        # BEARISH REVERSAL
        # ==================================================

        elif (
            direction == "BEARISH"
            and (
                choch == "BEARISH"
                or trigger_status == "CHOCH_CONFIRMED"
            )
        ):

            setup = "REVERSAL"

            confirmed.extend([
                "BEARISH_CHOCH",
                "BEARISH_DIRECTION",
            ])

            if (
                structural_alignment
                and structure_state == "CHARACTER_CHANGE"
                and trigger_status == "CHOCH_CONFIRMED"
                and zone_available
                and zone_aligned
                and zone_valid
                and location_confirmed
                and score >= 40
                and confidence >= 45
                and len(conflicts) == 0
            ):

                decision = "ENTER_SHORT"

                priority = "HIGH"

                reasons.append(
                    "Bearish institutional reversal "
                    "confirmed at active structural "
                    "execution location."
                )

            elif (
                structural_alignment
                and structure_state == "CHARACTER_CHANGE"
                and zone_available
                and zone_aligned
                and zone_valid
                and location_near
            ):

                decision = "WAIT"

                priority = "HIGH"

                missing.append(
                    "ZONE_INTERACTION"
                )

                reasons.append(
                    "Bearish reversal structure is "
                    "confirmed and price is approaching "
                    "the execution location."
                )

            else:

                decision = "WAIT"

                priority = "MEDIUM"

                missing.append(
                    "REVERSAL_LOCATION_CONFIRMATION"
                )

                reasons.append(
                    "Bearish reversal detected but "
                    "execution-location confirmation "
                    "is incomplete."
                )

        # ==================================================
        # STRUCTURAL WATCH / DEVELOPING SETUP
        # ==================================================
        #
        # Canonical directional structure is established,
        # but BOS / CHOCH confirmation is still pending.
        #
        # An aligned valid execution zone may already exist
        # and price may be approaching or interacting with it.
        #
        # This state is neither an entry nor an avoid state.
        # It represents a developing institutional setup.
        # ==================================================

        elif (
            direction in (
                "BULLISH",
                "BEARISH",
            )
            and structural_alignment
            and structure_state in (
                "PROTECTED",
                "DIRECTIONAL",
            )
            and not structure_confirmed
            and not structural_trigger
            and zone_available
            and zone_aligned
            and zone_valid
        ):

            setup = "STRUCTURAL_WATCH"

            decision = "WAIT"

            if location_active:

                priority = "HIGH"

                confirmed.extend([
                    "STRUCTURAL_DIRECTION",
                    "ALIGNED_EXECUTION_LOCATION",
                    "ACTIVE_EXECUTION_LOCATION",
                ])

                missing.append(
                    "STRUCTURAL_TRIGGER"
                )

                reasons.append(
                    f"{direction.title()} canonical structure "
                    "is established at an active aligned "
                    "execution location, but BOS / CHOCH "
                    "confirmation is still pending."
                )

            elif location_near:

                priority = "MEDIUM"

                confirmed.extend([
                    "STRUCTURAL_DIRECTION",
                    "ALIGNED_EXECUTION_LOCATION",
                ])

                missing.extend([
                    "ZONE_INTERACTION",
                    "STRUCTURAL_TRIGGER",
                ])

                reasons.append(
                    f"{direction.title()} canonical structure "
                    "is established and price is approaching "
                    "an aligned execution location. "
                    "BOS / CHOCH confirmation is pending."
                )

            else:

                priority = "LOW"

                confirmed.append(
                    "STRUCTURAL_DIRECTION"
                )

                missing.extend([
                    "EXECUTION_LOCATION_CONFIRMATION",
                    "STRUCTURAL_TRIGGER",
                ])

                reasons.append(
                    f"{direction.title()} canonical structure "
                    "is established, but price has not reached "
                    "the aligned execution location and "
                    "BOS / CHOCH confirmation is pending."
                )

        # ==================================================
        # AVOID
        # ==================================================

        elif (
            score < 20
            or direction == "NEUTRAL"
        ):

            setup = "AVOID"

            decision = "AVOID"

            priority = "LOW"

            # ----------------------------------------------
            # DIAGNOSTIC EVIDENCE ACCOUNTING
            # ----------------------------------------------

            if direction not in (
                "BULLISH",
                "BEARISH",
            ):

                missing.append(
                    "DIRECTION"
                )

            if not structural_alignment:

                missing.append(
                    "STRUCTURAL_DIRECTION"
                )

            if not structure_confirmed:

                missing.append(
                    "STRUCTURAL_CONFIRMATION"
                )

            if not structural_trigger:

                missing.append(
                    "STRUCTURAL_TRIGGER"
                )

            if not zone_available:

                missing.append(
                    "EXECUTION_LOCATION"
                )

            elif not zone_aligned:

                missing.append(
                    "ZONE_ALIGNMENT"
                )

            elif not zone_valid:

                missing.append(
                    "VALID_ZONE"
                )

            if not location_active:

                if location_near:

                    missing.append(
                        "ZONE_INTERACTION"
                    )

                else:

                    missing.append(
                        "EXECUTION_LOCATION_CONFIRMATION"
                    )

            if not execution_trigger_confirmed:

                if execution_trigger_conflict:

                    missing.append(
                        "EXECUTION_TRIGGER_ALIGNMENT"
                    )

                elif execution_trigger == "AWAITING_DIRECTION":

                    missing.append(
                        "STRUCTURAL_DIRECTION"
                    )

                else:

                    missing.append(
                        "EXECUTION_TRIGGER"
                    )


            if score < 20:

                missing.append(
                    "INSTITUTIONAL_EVIDENCE"
                )

            reasons.append(
                "Institutional evidence is insufficient."
            )

        # ==================================================
        # BRAIN CONFLICT PROTECTION
        # ==================================================

        if (
            len(conflicts) > 0
            and decision in (
                "ENTER_LONG",
                "ENTER_SHORT",
            )
        ):

            decision = "WAIT"

            priority = "MEDIUM"

            missing.append(
                "CONFLICT_CLEARANCE"
            )

            reasons.append(
                "Brain conflict protection blocked entry."
            )

        # ==================================================
        # UNIQUE OUTPUT
        # ==================================================

        reasons = self._unique(
            reasons
        )

        confirmed = self._unique(
            confirmed
        )

        missing = self._unique(
            missing
        )


        # ==================================================
        # APPROVAL CONTRACT
        # ==================================================

        approved = (
            decision
            in (
                "ENTER_LONG",
                "ENTER_SHORT",
            )
        )

        # ==================================================
        # STATE OUTPUT
        # ==================================================

        state.idm = {

            "decision": decision,

            "priority": priority,

            "setup": setup,

            "approved": approved,

            "score": score,

            "confidence": confidence,

            "direction": direction,

            "confirmed": confirmed,

            "missing": missing,

            "conflicts": conflicts,

            "structural": {

                "direction": structural_direction,

                "structure_state": structure_state,

                "trigger_status": trigger_status,

                "execution_trigger": execution_trigger,

                "trigger_source": trigger_source,

                "trigger_direction": trigger_direction,

                "execution_trigger_confirmed":
                    execution_trigger_confirmed,

                "zone_status": zone_status,

                "zone_type": zone_type,

                "zone_direction": zone_direction,

                "zone_lifecycle": zone_lifecycle,

                "interacting": interacting,

                "distance_atr": distance_atr,

                "location_quality": location_quality,

                "readiness": readiness,

            },

            "raw_signals": {

                "bos": bos,

                "choch": choch,

                "liquidity": liquidity,

                "order_block": order_block,

                "fvg": fvg,

                "discount": discount,

                "premium": premium,

            },

            "reasons": reasons,

        }

        return state
