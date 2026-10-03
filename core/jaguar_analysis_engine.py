from core.event_bus import EventBus

"""
Jaguar Quant X
Canonical Analysis Engine
Version : 3.0
"""

class JaguarAnalysisEngine:

    def __init__(self, kernel):
        self.kernel = kernel

    def run(self, symbol):

        state = self.kernel.get_state()

        from market.live_loader import update_state
        from indicators.indicator_engine import update_market_state

        state = update_state(
            state,
            symbol,
        )

        state = update_market_state(state)

        # ------------------------------------------------------------
        # Canonical MTF context hydration
        #
        # V3 intentionally keeps the lightweight live-loader path for
        # the active timeframe.  MTF, however, requires canonical
        # MarketProvider candles for 15m / 1h / 4h / 1d.
        #
        # Preserve the already hydrated live market snapshot while
        # temporarily exposing a timeframe map to the existing
        # TimeframeIndicatorEngineRunner and MTFEngineRunner.
        #
        # Higher-timeframe provider failures are fail-closed: the
        # unavailable timeframe is omitted rather than replaced with
        # synthetic data.
        # ------------------------------------------------------------

        from core.timeframe_indicator_engine import (
            TimeframeIndicatorEngineRunner,
        )
        from core.mtf_engine import MTFEngineRunner
        from core.trading_kernel import TradingKernel

        original_market = state.market
        original_timeframes = getattr(
            state,
            "timeframes",
            None,
        )

        active_interval = (
            getattr(state, "interval", None)
            or "15m"
        )

        active_market = (
            original_market
            if isinstance(original_market, dict)
            else {}
        )

        active_candles = active_market.get(
            "candles",
            [],
        )

        mtf_market = {}

        if active_candles:
            mtf_market[active_interval] = {
                "symbol": symbol,
                "interval": active_interval,
                "candles": active_candles,
            }

        trading_kernel = TradingKernel(symbol)

        for timeframe in ("15m", "1h", "4h", "1d"):
            if timeframe == active_interval:
                continue

            try:
                mtf_market[timeframe] = trading_kernel.load(
                    timeframe
                )
            except Exception as exc:
                print(
                    f"[MTF] {timeframe} unavailable: {exc}"
                )

        # Preserve the canonical MTF candle snapshot for dashboard
        # presentation after the analytical market context is restored.
        # This is read-only presentation data; it does not alter IDM,
        # risk, execution, or authorization state.
        state._dashboard_mtf_market = {
            timeframe: {
                "symbol": data.get("symbol"),
                "interval": data.get("interval"),
                "candles": data.get("candles", []),
            }
            for timeframe, data in mtf_market.items()
            if isinstance(data, dict)
        }

        state.market = mtf_market
        state.timeframes = {
            timeframe: {
                "symbol": data.get("symbol"),
                "interval": data.get("interval"),
                "candles": data.get("candles", []),
            }
            for timeframe, data in mtf_market.items()
            if isinstance(data, dict)
        }

        try:
            state = TimeframeIndicatorEngineRunner().run(
                state,
                EventBus(),
            )

            state = MTFEngineRunner().run(
                state,
                EventBus(),
            )
        finally:
            # Never allow MTF presentation hydration to replace the
            # V3 canonical active-market snapshot.
            state.market = original_market

            if original_timeframes is None:
                try:
                    delattr(state, "timeframes")
                except AttributeError:
                    pass
            else:
                state.timeframes = original_timeframes

        # Keep the lightweight API analysis path intact while restoring
        # the canonical Session Engine state required by the dashboard.
        from strategy.session_engine import SessionEngine

        SessionEngine().run(state, EventBus())

        from engine.institutional_master import analyze

        report = analyze(state)

        return {
            "state": state,
            "report": report,
        }
