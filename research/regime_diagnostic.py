# research/regime_diagnostic.py
import json
import os
import tempfile
from datetime import datetime
from collections import Counter, defaultdict
from core.backtest_engine import BacktestEngine
from core.trade import Trade
from core.trade_simulator import TradeSimulator
from core.filter_attribution import get_attribution
from research.recorder import record_trade_close, record_decision_snapshot
from research.database import update_decision_outcome, update_decision_stage

class RegimeDiagnosticEngine(BacktestEngine):
    """Replays each candle and logs regime engine inputs/outputs."""

    def replay(self, state, candles):
        import json

        log_file = getattr(self, '_log_path', None)
        simulator = TradeSimulator()
        attribution = get_attribution()

        full_candles_by_tf = {}
        for tf, market in state.market.items():
            full_candles_by_tf[tf] = market.get("candles", [])[:]

        regime_log = []

        for index in range(200, len(candles) - 1):
            candle = candles[index]
            replay_time = candle["time"]
            attribution.count_candle()

            for tf, market in state.market.items():
                full_list = full_candles_by_tf[tf]
                historical_tf = [c for c in full_list if c.get("time", 0) <= replay_time]
                market["candles"] = historical_tf
            state.market_current = state.market.get(state.interval)
            if hasattr(state, 'indicators'):
                state.indicators = None
            state.price = candle["close"]
            state.high = candle["high"]
            state.low = candle["low"]
            state.volume = candle["volume"]

            self.registry.run(state, self.bus, skip={"BacktestEngine", "YahooMarketEngine"})

            if state.market_current:
                full_current = full_candles_by_tf[state.interval]
                state.market_current["candles"] = [c for c in full_current if c.get("time", 0) <= replay_time]

            # Capture regime output and relevant indicators
            regime = getattr(state, "regime", {})
            adx_data = None
            atr_data = None
            ind = state.indicators if hasattr(state, "indicators") else {}
            if isinstance(ind, dict):
                adx_data = ind.get("adx")
                atr_data = ind.get("atr")

            # Extract numeric values (they may be dicts with 'value' key)
            def _num(x):
                if isinstance(x, (int, float)):
                    return x
                if isinstance(x, dict):
                    return x.get("value", 0)
                return 0

            entry = {
                "index": index,
                "timestamp": replay_time,
                "price": candle["close"],
                "regime": regime.get("regime", "UNKNOWN") if isinstance(regime, dict) else str(regime),
                "regime_score": regime.get("score", 0) if isinstance(regime, dict) else 0,
                "regime_reasons": regime.get("reasons", []) if isinstance(regime, dict) else [],
                "adx": _num(adx_data),
                "atr": _num(atr_data),
            }
            regime_log.append(entry)

        # Write log
        if log_file:
            with open(log_file, 'w') as f:
                json.dump(regime_log, f, indent=2)

        # Analyze
        total = len(regime_log)
        regimes = Counter(e["regime"] for e in regime_log)
        adx_vals = [e["adx"] for e in regime_log if e["adx"]]
        atr_vals = [e["atr"] for e in regime_log if e["atr"]]

        # Reasons for COMPRESSION (first 5 examples)
        compression_reasons = []
        for e in regime_log:
            if e["regime"] == "COMPRESSION":
                compression_reasons.append(e["regime_reasons"])

        # Print report
        print("\n" + "=" * 70)
        print("  REGIME DIAGNOSTIC")
        print("=" * 70)
        print(f"  Candles analysed : {total}")

        print(f"\n  Regime Distribution:")
        for regime, cnt in regimes.most_common():
            pct = cnt / total * 100
            print(f"  {regime:15s}: {cnt:6d} ({pct:5.1f}%)")

        if adx_vals:
            print(f"\n  ADX Distribution:")
            print(f"    Min : {min(adx_vals):.2f}")
            print(f"    Max : {max(adx_vals):.2f}")
            print(f"    Mean: {sum(adx_vals)/len(adx_vals):.2f}")

        if atr_vals:
            print(f"\n  ATR Distribution:")
            print(f"    Min : {min(atr_vals):.2f}")
            print(f"    Max : {max(atr_vals):.2f}")
            print(f"    Mean: {sum(atr_vals)/len(atr_vals):.2f}")

        # Print the first few COMPRESSION reasons
        print(f"\n  First 5 COMPRESSION reasons (sample):")
        for i, reasons in enumerate(compression_reasons[:5], 1):
            print(f"    {i}. {reasons}")

        # Print sample candles with different regimes (if any non-COMPRESSION exist)
        non_comp = [e for e in regime_log if e["regime"] != "COMPRESSION"]
        if non_comp:
            print(f"\n  Sample non-COMPRESSION candles (first 5):")
            for e in non_comp[:5]:
                print(f"    Index={e['index']}, Price={e['price']:.2f}, Regime={e['regime']}, ADX={e['adx']:.2f}, ATR={e['atr']:.2f}")
        else:
            print(f"\n  No non-COMPRESSION candles found – all candles classified as COMPRESSION.")

        print(f"\n  RECOMMENDATION:")
        print(f"  - If ADX is always below trend threshold, the regime logic defaults to COMPRESSION.")
        print(f"  - Check the ADX trend threshold in strategy/regime_engine.py.")
        print("=" * 70)
