"""
Jaguar Quant X Enterprise
Risk Manager V3.0

Enterprise trade-risk validation and position-sizing layer.

Purpose:
- Revalidate IDM trade authority
- Validate trade contract integrity
- Validate directional trade geometry
- Validate structural execution readiness
- Validate minimum risk-reward
- Calculate controlled position size
- Produce a normalized enterprise risk contract

IMPORTANT:
This engine does not create trades.
This engine does not modify trade levels.
This engine does not override structural stops.
This engine only validates and sizes authorized trade plans.
"""


import math


class RiskManagerV2:

    name = "Risk Manager V3"

    # ==================================================
    # CONFIGURATION
    # ==================================================

    DEFAULT_CAPITAL = 100000.0

    BASE_RISK_PERCENT = 1.0

    HIGH_PRIORITY_RISK = 1.0

    MEDIUM_PRIORITY_RISK = 0.75

    LOW_PRIORITY_RISK = 0.50

    MIN_RISK_REWARD = 1.50

    MAX_RISK_PERCENT = 1.0

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

            result = float(
                value
            )

            if not math.isfinite(
                result
            ):
                return float(
                    default
                )

            return result

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
    # EMPTY RISK CONTRACT
    # ==================================================

    @classmethod
    def _empty_risk(
        cls,
        decision="WAIT",
        reason="Risk validation not available.",
        reasons=None,
        warnings=None,
    ):

        return {

            "approved": False,

            "decision": decision,

            "position_size": 0.0,

            "risk_percent": 0.0,

            "risk_amount": 0.0,

            "capital": 0.0,

            "entry": None,

            "stop_loss": None,

            "stop_distance": 0.0,

            "risk_reward": 0.0,

            "minimum_risk_reward": (
                cls.MIN_RISK_REWARD
            ),

            "priority": "LOW",

            "structural_readiness": "UNKNOWN",

            "reason": reason,

            "reasons": cls._unique(
                reasons or []
            ),

            "warnings": cls._unique(
                warnings or []
            ),

            "status": "REJECTED",

        }

    # ==================================================
    # CAPITAL
    # ==================================================

    @classmethod
    def _capital(cls, state):

        account = cls._dictionary(
            getattr(
                state,
                "account",
                {},
            )
        )

        capital = cls._float(
            account.get(
                "capital",
                account.get(
                    "equity",
                    cls.DEFAULT_CAPITAL,
                ),
            ),
            cls.DEFAULT_CAPITAL,
        )

        if capital <= 0:

            return cls.DEFAULT_CAPITAL

        return capital

    # ==================================================
    # RISK PERCENT
    # ==================================================

    @classmethod
    def _risk_percent(
        cls,
        priority,
    ):

        if priority == "HIGH":

            risk_percent = (
                cls.HIGH_PRIORITY_RISK
            )

        elif priority == "MEDIUM":

            risk_percent = (
                cls.MEDIUM_PRIORITY_RISK
            )

        else:

            risk_percent = (
                cls.LOW_PRIORITY_RISK
            )

        return min(
            risk_percent,
            cls.MAX_RISK_PERCENT,
        )

    # ==================================================
    # PROCESS
    # ==================================================

    def process(self, state):

        trade = self._dictionary(
            getattr(
                state,
                "trade",
                {},
            )
        )

        idm = self._dictionary(
            getattr(
                state,
                "idm",
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

        reasons = []

        warnings = []

        # ==================================================
        # READ AUTHORITY CONTRACT
        # ==================================================

        decision = str(
            idm.get(
                "decision",
                "WAIT",
            )
        ).upper().strip()

        priority = str(
            idm.get(
                "priority",
                "LOW",
            )
        ).upper().strip()

        trade_status = str(
            trade.get(
                "status",
                "NO TRADE",
            )
        ).upper().strip()

        structural_readiness = str(
            structural_zone.get(
                "readiness",
                "UNKNOWN",
            )
        ).upper().strip()

        # ==================================================
        # IDM AUTHORITY GATE
        # ==================================================

        if decision not in (
            "ENTER_LONG",
            "ENTER_SHORT",
        ):

            state.risk = self._empty_risk(
                decision=decision,
                reason=(
                    "IDM has not authorized "
                    "an executable trade."
                ),
                reasons=[
                    "Risk approval blocked by IDM authority."
                ],
            )

            return state

        # ==================================================
        # TRADE STATUS GATE
        # ==================================================

        if trade_status != "READY":

            state.risk = self._empty_risk(
                decision=decision,
                reason=(
                    "Trade planner has not produced "
                    "a ready trade plan."
                ),
                reasons=[
                    "Risk approval requires a READY trade."
                ],
            )

            return state

        # ==================================================
        # STRUCTURAL READINESS GATE
        # ==================================================

        if structural_readiness != "CONFIRMED":

            state.risk = self._empty_risk(
                decision=decision,
                reason=(
                    "Structural execution location "
                    "is not confirmed."
                ),
                reasons=[
                    (
                        "Risk approval requires confirmed "
                        "structural readiness."
                    )
                ],
                warnings=[
                    (
                        "Structural readiness is "
                        f"{structural_readiness}."
                    )
                ],
            )

            return state

        # ==================================================
        # READ TRADE CONTRACT
        # ==================================================

        entry = self._float(
            trade.get(
                "entry",
                0.0,
            )
        )

        stop = self._float(
            trade.get(
                "stop_loss",
                0.0,
            )
        )

        targets = trade.get(
            "targets",
            [],
        )

        if not isinstance(
            targets,
            list,
        ):

            targets = []

        targets = [

            self._float(
                target,
                0.0,
            )

            for target in targets

            if self._float(
                target,
                0.0,
            ) > 0

        ]

        reported_rr = self._float(
            trade.get(
                "risk_reward",
                0.0,
            )
        )

        # ==================================================
        # BASIC CONTRACT VALIDATION
        # ==================================================

        validation_errors = []

        if entry <= 0:

            validation_errors.append(
                "Trade entry is invalid."
            )

        if stop <= 0:

            validation_errors.append(
                "Trade stop loss is invalid."
            )

        if not targets:

            validation_errors.append(
                "Trade targets are missing."
            )

        if validation_errors:

            state.risk = self._empty_risk(
                decision=decision,
                reason=(
                    "Trade contract failed "
                    "risk validation."
                ),
                reasons=validation_errors,
            )

            return state

        # ==================================================
        # DIRECTIONAL GEOMETRY
        # ==================================================

        if decision == "ENTER_LONG":

            if stop >= entry:

                validation_errors.append(
                    "Long trade stop must be below entry."
                )

            invalid_targets = [
                target
                for target in targets
                if target <= entry
            ]

            if invalid_targets:

                validation_errors.append(
                    "Long trade targets must be above entry."
                )

        elif decision == "ENTER_SHORT":

            if stop <= entry:

                validation_errors.append(
                    "Short trade stop must be above entry."
                )

            invalid_targets = [
                target
                for target in targets
                if target >= entry
            ]

            if invalid_targets:

                validation_errors.append(
                    "Short trade targets must be below entry."
                )

        if validation_errors:

            state.risk = self._empty_risk(
                decision=decision,
                reason=(
                    "Trade geometry failed "
                    "risk validation."
                ),
                reasons=validation_errors,
            )

            return state

        # ==================================================
        # STOP DISTANCE
        # ==================================================

        stop_distance = abs(
            entry
            - stop
        )

        if stop_distance <= 0:

            state.risk = self._empty_risk(
                decision=decision,
                reason=(
                    "Stop distance is invalid."
                ),
                reasons=[
                    "Entry and stop loss cannot be equal."
                ],
            )

            return state

        # ==================================================
        # TRUE RISK-REWARD VALIDATION
        # ==================================================

        primary_target = (
            targets[1]
            if len(targets) >= 2
            else targets[0]
        )

        reward_distance = abs(
            primary_target
            - entry
        )

        calculated_rr = round(
            reward_distance
            / stop_distance,
            2,
        )

        if (
            reported_rr > 0
            and abs(
                reported_rr
                - calculated_rr
            ) > 0.10
        ):

            warnings.append(
                (
                    "Planner risk-reward differs "
                    "from risk-manager calculation."
                )
            )

        if (
            calculated_rr
            < self.MIN_RISK_REWARD
        ):

            state.risk = self._empty_risk(
                decision=decision,
                reason=(
                    "Trade risk-reward is below "
                    "enterprise minimum."
                ),
                reasons=[
                    (
                        "Calculated risk-reward "
                        f"{calculated_rr} is below "
                        f"{self.MIN_RISK_REWARD}."
                    )
                ],
                warnings=warnings,
            )

            return state

        # ==================================================
        # CAPITAL AND RISK BUDGET
        # ==================================================

        capital = self._capital(
            state
        )

        risk_percent = self._risk_percent(
            priority
        )

        risk_amount = (
            capital
            * (
                risk_percent
                / 100.0
            )
        )

        # ==================================================
        # POSITION SIZE
        # ==================================================

        position_size = (
            risk_amount
            / stop_distance
        )

        if (
            not math.isfinite(
                position_size
            )
            or position_size <= 0
        ):

            state.risk = self._empty_risk(
                decision=decision,
                reason=(
                    "Position size calculation "
                    "is invalid."
                ),
                reasons=[
                    "Risk sizing failed."
                ],
                warnings=warnings,
            )

            return state

        position_size = round(
            position_size,
            8,
        )

        # ==================================================
        # APPROVAL REASONS
        # ==================================================

        reasons.extend([

            "IDM trade authority confirmed.",

            "Trade planner contract is READY.",

            "Structural execution location confirmed.",

            "Directional trade geometry validated.",

            (
                "Risk-reward satisfies "
                "enterprise minimum."
            ),

            "Position size calculated from stop distance.",

        ])

        reasons = self._unique(
            reasons
        )

        warnings = self._unique(
            warnings
        )

        # ==================================================
        # ENTERPRISE RISK CONTRACT
        # ==================================================

        state.risk = {

            "approved": True,

            "decision": decision,

            "position_size": position_size,

            "risk_percent": round(
                risk_percent,
                4,
            ),

            "risk_amount": round(
                risk_amount,
                2,
            ),

            "capital": round(
                capital,
                2,
            ),

            "entry": round(
                entry,
                8,
            ),

            "stop_loss": round(
                stop,
                8,
            ),

            "stop_distance": round(
                stop_distance,
                8,
            ),

            "risk_reward": calculated_rr,

            "minimum_risk_reward": (
                self.MIN_RISK_REWARD
            ),

            "priority": priority,

            "structural_readiness": (
                structural_readiness
            ),

            "reason": "Risk Approved",

            "reasons": reasons,

            "warnings": warnings,

            "status": "APPROVED",

        }

        # ==================================================
        # DEBUG
        # ==================================================

        print()

        print(
            "========== ENTERPRISE RISK DEBUG =========="
        )

        print(
            "Decision             :",
            decision,
        )

        print(
            "Priority             :",
            priority,
        )

        print(
            "Trade Status          :",
            trade_status,
        )

        print(
            "Structural Readiness  :",
            structural_readiness,
        )

        print(
            "Capital              :",
            capital,
        )

        print(
            "Risk Percent         :",
            risk_percent,
        )

        print(
            "Risk Amount          :",
            round(
                risk_amount,
                2,
            ),
        )

        print(
            "Entry                :",
            entry,
        )

        print(
            "Stop Loss            :",
            stop,
        )

        print(
            "Stop Distance        :",
            round(
                stop_distance,
                8,
            ),
        )

        print(
            "Risk Reward          :",
            calculated_rr,
        )

        print(
            "Position Size        :",
            position_size,
        )

        print(
            "Approved             :",
            True,
        )

        print(
            "==========================================="
        )

        return state
