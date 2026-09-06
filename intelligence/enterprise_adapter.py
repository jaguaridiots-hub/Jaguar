"""
Jaguar Quant X Enterprise
Enterprise Adapter v2.3

Legacy Engine -> Enterprise State Contract

State-contract aware normalization layer.

Canonical contract priority:

    Existing enterprise market facts
        ->
    Raw specialist EngineResult dictionaries
        ->
    Legacy state values

IMPORTANT:
Canonical raw specialist results must never be
overwritten by legacy boolean compatibility fields.
"""

from intelligence.enterprise_pipeline import EnterprisePipeline


class EnterpriseAdapter:

    name = "Enterprise Adapter"

    def __init__(self):

        self.pipeline = EnterprisePipeline()

    # ==================================================
    # SIGNAL NORMALIZATION
    # ==================================================

    @staticmethod
    def _signal(result):

        # ==============================================
        # ENGINE RESULT DICTIONARY
        # ==============================================

        if isinstance(result, dict):

            signal = str(
                result.get(
                    "signal",
                    "NEUTRAL",
                )
            ).upper().strip()

            if signal in (
                "BULLISH",
                "BEARISH",
                "NEUTRAL",
                "SIDEWAYS",
                "UNKNOWN",
                "DISCOUNT",
                "PREMIUM",
            ):
                return signal

            return "NEUTRAL"

        # ==============================================
        # LEGACY STRING SIGNAL
        # ==============================================

        if isinstance(result, str):

            signal = result.upper().strip()

            if signal in (
                "BULLISH",
                "BEARISH",
                "NEUTRAL",
                "SIDEWAYS",
                "UNKNOWN",
                "DISCOUNT",
                "PREMIUM",
            ):
                return signal

            return "NEUTRAL"

        # ==============================================
        # LEGACY BOOLEAN FACT
        # ==============================================

        if isinstance(result, bool):

            if result:
                return "BULLISH"

            return "NEUTRAL"

        return "NEUTRAL"

    # ==================================================
    # ACTIVE FACT NORMALIZATION
    # ==================================================

    @staticmethod
    def _active(result):

        if isinstance(result, bool):

            return result

        return EnterpriseAdapter._signal(
            result
        ) in (
            "BULLISH",
            "BEARISH",
        )

    # ==================================================
    # METADATA NORMALIZATION
    # ==================================================

    @staticmethod
    def _metadata(result):

        if not isinstance(result, dict):

            return {}

        metadata = result.get(
            "metadata",
            {},
        )

        if isinstance(metadata, dict):

            return metadata

        return {}

    # ==================================================
    # CANONICAL MARKET RESULT
    # ==================================================

    @staticmethod
    def _market_result(
        market,
        key,
        legacy_value,
        default,
    ):

        """
        Preserve an existing canonical raw EngineResult.

        Priority:

        1. Existing market result dictionary
        2. Existing market result string
        3. Legacy state value
        4. Default

        Boolean market values are not considered canonical
        raw specialist results because they may originate
        from legacy compatibility fields.
        """

        existing = market.get(
            key,
            None,
        )

        if isinstance(existing, dict):

            return existing

        if isinstance(existing, str):

            return existing

        if isinstance(legacy_value, dict):

            return legacy_value

        if isinstance(legacy_value, str):

            return legacy_value

        if isinstance(legacy_value, bool):

            return legacy_value

        return default

    # ==================================================
    # PROCESS
    # ==================================================

    def process(self, state):

        # ==================================================
        # ENSURE ENTERPRISE CONTAINERS
        # ==================================================

        if (
            not hasattr(state, "metadata")
            or not isinstance(
                state.metadata,
                dict,
            )
        ):

            state.metadata = {}

        if (
            not hasattr(state, "market")
            or not isinstance(
                state.market,
                dict,
            )
        ):

            state.market = {}

        # ==================================================
        # SYNC BASIC METADATA
        # ==================================================

        state.metadata["symbol"] = getattr(
            state,
            "symbol",
            "",
        )

        state.metadata["timeframe"] = getattr(
            state,
            "timeframe",
            "",
        )

        # ==================================================
        # SYNC BASIC MARKET DATA
        # ==================================================

        state.market["price"] = float(
            getattr(
                state,
                "price",
                0.0,
            )
            or 0.0
        )

        state.market["support"] = float(
            getattr(
                state,
                "support",
                0.0,
            )
            or 0.0
        )

        state.market["resistance"] = float(
            getattr(
                state,
                "resistance",
                0.0,
            )
            or 0.0
        )

        # ==================================================
        # READ LEGACY COMPATIBILITY STATE
        # ==================================================

        legacy_regime = getattr(
            state,
            "regime",
            "UNKNOWN",
        )

        legacy_bos = getattr(
            state,
            "bos",
            False,
        )

        legacy_choch = getattr(
            state,
            "choch",
            False,
        )

        legacy_liquidity = getattr(
            state,
            "liquidity",
            False,
        )

        legacy_order_block = getattr(
            state,
            "order_block",
            False,
        )

        legacy_fvg = getattr(
            state,
            "fvg",
            False,
        )

        fibonacci_result = getattr(
            state,
            "fibonacci",
            {},
        )

        gann_result = getattr(
            state,
            "gann",
            {},
        )

        # ==================================================
        # PRESERVE CANONICAL RAW SPECIALIST RESULTS
        # ==================================================

        regime_result = self._market_result(
            state.market,
            "regime_result",
            legacy_regime,
            "UNKNOWN",
        )

        bos_result = self._market_result(
            state.market,
            "bos_result",
            legacy_bos,
            False,
        )

        choch_result = self._market_result(
            state.market,
            "choch_result",
            legacy_choch,
            False,
        )

        liquidity_result = self._market_result(
            state.market,
            "liquidity_result",
            legacy_liquidity,
            False,
        )

        order_block_result = self._market_result(
            state.market,
            "order_block_result",
            legacy_order_block,
            False,
        )

        fvg_result = self._market_result(
            state.market,
            "fvg_result",
            legacy_fvg,
            False,
        )

        # ==================================================
        # NORMALIZE REGIME
        # ==================================================

        regime_signal = self._signal(
            regime_result
        )

        if regime_signal in (
            "BULLISH",
            "BEARISH",
            "SIDEWAYS",
        ):

            state.trend = regime_signal

        else:

            state.trend = "UNKNOWN"

        # ==================================================
        # NORMALIZE MARKET STRUCTURE FACTS
        # ==================================================

        bos_signal = self._signal(
            bos_result
        )

        choch_signal = self._signal(
            choch_result
        )

        liquidity_signal = self._signal(
            liquidity_result
        )

        order_block_signal = self._signal(
            order_block_result
        )

        fvg_signal = self._signal(
            fvg_result
        )

        bos_active = self._active(
            bos_result
        )

        choch_active = self._active(
            choch_result
        )

        liquidity_active = self._active(
            liquidity_result
        )

        order_block_active = self._active(
            order_block_result
        )

        fvg_active = self._active(
            fvg_result
        )

        # ==================================================
        # FIBONACCI ZONE NORMALIZATION
        # ==================================================

        discount = False

        premium = False

        fib_signal = self._signal(
            fibonacci_result
        )

        fib_reasons = []

        if isinstance(
            fibonacci_result,
            dict,
        ):

            fib_reasons = fibonacci_result.get(
                "reasons",
                [],
            )

        if not isinstance(
            fib_reasons,
            list,
        ):

            fib_reasons = []

        fib_text = " ".join(
            str(reason).upper()
            for reason in fib_reasons
        )

        if (
            "DISCOUNT" in fib_text
            or fib_signal == "DISCOUNT"
        ):

            discount = True

        if (
            "PREMIUM" in fib_text
            or fib_signal == "PREMIUM"
        ):

            premium = True

        # ==================================================
        # PRESERVE LEGACY COMPATIBILITY
        # ==================================================






        state.discount = discount

        state.premium = premium

        # ==================================================
        # ENTERPRISE MARKET CONTRACT
        # ==================================================

        state.market["trend"] = state.trend

        state.market["regime"] = regime_signal

        # ==================================================
        # CANONICAL RAW SPECIALIST RESULTS
        #
        # NEVER replace these with compatibility booleans.
        # ==================================================

        state.market[
            "regime_result"
        ] = regime_result

        state.market[
            "bos_result"
        ] = bos_result

        state.market[
            "choch_result"
        ] = choch_result

        state.market[
            "liquidity_result"
        ] = liquidity_result

        state.market[
            "order_block_result"
        ] = order_block_result

        state.market[
            "fvg_result"
        ] = fvg_result

        state.market[
            "fibonacci_result"
        ] = fibonacci_result

        state.market[
            "gann_result"
        ] = gann_result

        # ==================================================
        # NORMALIZED SIGNAL CONTRACT
        # ==================================================

        state.market[
            "bos_signal"
        ] = bos_signal

        state.market[
            "choch_signal"
        ] = choch_signal

        state.market[
            "liquidity_signal"
        ] = liquidity_signal

        state.market[
            "order_block_signal"
        ] = order_block_signal

        state.market[
            "fvg_signal"
        ] = fvg_signal

        # ==================================================
        # NORMALIZED BOOLEAN FACT CONTRACT
        # ==================================================

        state.market[
            "bos"
        ] = bos_active

        state.market[
            "choch"
        ] = choch_active

        state.market[
            "liquidity"
        ] = liquidity_active

        state.market[
            "order_block"
        ] = order_block_active

        state.market[
            "fvg"
        ] = fvg_active

        state.market[
            "discount"
        ] = discount

        state.market[
            "premium"
        ] = premium

        # ==================================================
        # RUN ENTERPRISE PIPELINE
        # ==================================================

        state = self.pipeline.run(
            state
        )

        # ==================================================
        # ENTERPRISE OUTPUT CONTRACT
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

        idm = getattr(
            state,
            "idm",
            {},
        )

        if not isinstance(
            idm,
            dict,
        ):

            idm = {}

        # ==================================================
        # PRESERVE LEGACY / CONFLUENCE DECISION CONTRACT
        # ==================================================

        legacy_ai_score = getattr(
            state,
            "ai_score",
            0,
        )

        legacy_confidence = getattr(
            state,
            "confidence",
            "D",
        )

        legacy_probability = getattr(
            state,
            "probability",
            0,
        )

        legacy_decision = getattr(
            state,
            "decision",
            "⚪ NO TRADE",
        )

        # ==================================================
        # EXPLICIT ENTERPRISE METRICS
        # ==================================================

        state.institutional_score = institutional.get(
            "score",
            0,
        )

        state.institutional_grade = institutional.get(
            "grade",
            "F",
        )

        state.institutional_confidence = institutional.get(
            "confidence",
            0,
        )

        state.idm_decision = idm.get(
            "decision",
            "WAIT",
        )

        state.idm_priority = idm.get(
            "priority",
            "LOW",
        )

        # ==================================================
        # RESTORE CANONICAL MARKET-BIAS CONTRACT
        # ==================================================

        state.ai_score = legacy_ai_score

        state.confidence = legacy_confidence

        state.probability = legacy_probability


        # ==================================================
        # SYNC TRADE PLAN
        # ==================================================

        trade = getattr(
            state,
            "trade",
            {},
        )

        if (
            isinstance(
                trade,
                dict,
            )
            and trade.get(
                "status"
            ) == "READY"
        ):

            state.entry = float(
                trade.get(
                    "entry",
                    0.0,
                )
                or 0.0
            )

            state.stoploss = float(
                trade.get(
                    "stop_loss",
                    0.0,
                )
                or 0.0
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

            if len(targets) > 0:

                state.tp1 = targets[0]

            if len(targets) > 1:

                state.tp2 = targets[1]

            if len(targets) > 2:

                state.tp3 = targets[2]

        return state
