# research/regime_input_audit.py
import json
import os
import tempfile
from datetime import datetime
from collections import Counter
from core.backtest_engine import BacktestEngine
from core.trade import Trade
from core.trade_simulator import TradeSimulator
from core.filter_attribution import get_attribution
from research.recorder import record_trade_close, record_decision_snapshot
from research.database import update_decision_outcome, update_decision_stage

class RegimeInputAuditEngine(BacktestEngine):
    """Replays candles and logs the exact inputs the RegimeEngine receives."""

    def replay(self, state, candles):
        simulator = TradeSimulator()
        attribution = get_attribution()

        full_candles_by_tf = {}
        for tf, market in state.market.items():
            full_candles_by_tf[tf] = market.get("candles", [])[:]

        input_log = []

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

            # Capture indicator keys and values right after the pipeline run
            ind = state.indicators if hasattr(state, "indicators") else {}
            indicator_keys = list(ind.keys()) if isinstance(ind, dict) else []
            adx_val = None
            bb_width_val = None
            bollinger_val = None
            if isinstance(ind, dict):
                adx_data = ind.get("adx")
                if isinstance(adx_data, dict):
                    adx_val = adx_data.get("value")
                elif isinstance(adx_data, (int, float)):
                    adx_val = adx_data
                bb_width_data = ind.get("bb_width")
                if isinstance(bb_width_data, dict):
                    bb_width_val = bb_width_data.get("value")
                elif isinstance(bb_width_data, (int, float)):
                    bb_width_val = bb_width_data
                bollinger_data = ind.get("bollinger")
                if isinstance(bollinger_data, dict):
                    bollinger_val = json.dumps(bollinger_data)  # keep it compact
                elif bollinger_data is not None:
                    bollinger_val = str(bollinger_data)

            # Capture regime output
            regime_obj = getattr(state, "regime", None)
            regime_label = "UNKNOWN"
            if isinstance(regime_obj, dict):
                regime_label = regime_obj.get("regime", "UNKNOWN")
            elif isinstance(regime_obj, str):
                regime_label = regime_obj

            input_log.append({
                "index": index,
                "indicator_keys": indicator_keys,
                "adx": adx_val,
                "bb_width": bb_width_val,
                "bollinger": bollinger_val,
                "regime": regime_label,
            })

            # Original trade logic (unchanged)
            decision_id = record_decision_snapshot(state, candle_timestamp=replay_time)
            master = getattr(state, "master_decision", {})
            planner = getattr(state, "trade_plan", {})
            if master.get("decision") not in ["BUY", "SELL"] or not planner:
                continue
            direction = master["decision"]
            attribution.count_executed_trade()
            trade_uuid = getattr(state, "_trade_id", None)
            if trade_uuid is None:
                continue
            quantity = state.risk.get("position_size", 1.0)
            entry_time_str = _to_iso(replay_time)
            trade = Trade(
                direction=direction, entry=planner["entry"],
                stop_loss=planner["stop"], take_profit_1=planner["tp1"],
                take_profit_2=planner.get("tp2", planner["tp1"]),
                entry_time=entry_time_str, quantity=quantity, uuid=trade_uuid
            )
            future = candles[index + 1:]
            trade = simulator.simulate(trade, future)
            trade.compute_pnl()
            if trade.status in ("WIN", "LOSS"):
                holding_seconds = 0
                if trade.entry_time and trade.exit_time:
                    try:
                        entry_dt = _parse_iso(trade.entry_time)
                        exit_dt = _parse_iso(trade.exit_time)
                        holding_seconds = (exit_dt - entry_dt).total_seconds()
                    except:
                        pass
                record_trade_close(
                    uuid=trade.uuid, exit_price=trade.exit_price,
                    pnl=trade.pnl, r_multiple=trade.rr,
                    win_loss=(trade.status == "WIN"), holding_time=holding_seconds,
                    exit_time=trade.exit_time
                )
                update_decision_outcome(decision_id, trade.status, trade.uuid)
            self.result.total_trades += 1
            if trade.status == "WIN":
                self.result.wins += 1
            elif trade.status == "LOSS":
                self.result.losses += 1

        if self.result.total_trades:
            self.result.win_rate = round(self.result.wins * 100 / self.result.total_trades, 2)
            self.result.loss_rate = round(self.result.losses * 100 / self.result.total_trades, 2)

        # Analysis
        total = len(input_log)
        print("\n" + "=" * 70)
        print("  REGIME INPUT AUDIT")
        print("=" * 70)
        print(f"  Total candles analysed : {total}")

        # Check for presence of bb_width
        has_bb_width = any(e["bb_width"] is not None for e in input_log)
        bb_width_vals = [e["bb_width"] for e in input_log if e["bb_width"] is not None]
        adx_vals = [e["adx"] for e in input_log if e["adx"] is not None]

        print(f"\n  Indicator Keys (from first 3 samples):")
        for i, e in enumerate(input_log[:3], 1):
            print(f"    {i}. keys={e['indicator_keys']}")

        print(f"\n  ADX present in samples : {len(adx_vals)} / {total}")
        if adx_vals:
            print(f"    Min: {min(adx_vals):.2f}  Max: {max(adx_vals):.2f}  Mean: {sum(adx_vals)/len(adx_vals):.2f}")

        print(f"\n  BB Width present in samples : {len(bb_width_vals)} / {total}")
        if bb_width_vals:
            print(f"    Min: {min(bb_width_vals):.2f}  Max: {max(bb_width_vals):.2f}  Mean: {sum(bb_width_vals)/len(bb_width_vals):.2f}")
        else:
            print("    ⚠️  BB Width is NEVER populated. The regime engine receives bb_width = None/0 from indicators.")

        # Show a sample where bollinger data exists but bb_width is missing
        bollinger_present = [e for e in input_log if e["bollinger"] is not None]
        if bollinger_present and not bb_width_vals:
            print("\n  Bollinger bands ARE present in indicators, but bb_width is missing.")
            print("  The IndicatorEngine must compute and store bb_width explicitly.")
            print("  Check indicators/indicator_engine.py: add 'bb_width' to the returned dict.")
            for e in bollinger_present[:3]:
                print(f"    Sample bollinger: {e['bollinger'][:100]}")

        # Regime distribution
        regime_counts = Counter(e["regime"] for e in input_log)
        print(f"\n  Resulting Regime Distribution:")
        for regime, cnt in regime_counts.most_common():
            pct = cnt / total * 100
            print(f"    {regime:15s}: {cnt:6d} ({pct:5.1f}%)")

        print("\n  RECOMMENDATION:")
        if not bb_width_vals:
            print("  - Add 'bb_width' to state.ai / state.indicators in IndicatorEngine.")
            print("  - The RegimeEngine currently defaults to COMPRESSION because bb_width is 0/None.")
        elif all(v == 0 for v in bb_width_vals):
            print("  - BB Width is always 0. Verify the calculation or the Bollinger band data.")
        else:
            print("  - BB Width data exists and varies. Regime outputs should be diverse.")
        print("=" * 70)


def _to_iso(ts):
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts).isoformat()
    try:
        datetime.fromisoformat(str(ts))
        return str(ts)
    except:
        return str(ts)

def _parse_iso(ts):
    try:
        return datetime.fromisoformat(ts)
    except:
        return datetime.fromtimestamp(float(ts))


def run_regime_input_audit(symbol="GC=F", mode="SCALP"):
    import uuid, copy
    from core.orchestrator import JaguarOrchestrator
    from core.engine_registry import EngineRegistry
    from core.register_engines import register
    from research.database import init_db, insert_research_run, update_research_run, get_campaign_stats
    from jaguar_version import JAGUAR_VERSION

    app = JaguarOrchestrator()
    state = app.analyze(symbol, "15m", mode=mode)

    init_db()
    run_id = str(uuid.uuid4())
    start_time = datetime.now().isoformat()
    insert_research_run(run_id, JAGUAR_VERSION, symbol, mode, "15m", start_time=start_time)
    state.run_id = run_id

    backtest_state = copy.deepcopy(state)
    backtest_state.symbol = symbol
    backtest_state.interval = "15m"
    backtest_state.mode = mode
    backtest_state.run_id = run_id

    registry = EngineRegistry()
    register(registry)
    engine = RegimeInputAuditEngine(registry)
    bus = app.bus

    engine.run(backtest_state, bus)

    end_time = datetime.now().isoformat()
    duration = (datetime.now() - datetime.fromisoformat(start_time)).total_seconds()
    stats = get_campaign_stats(run_id)
    update_research_run(run_id, end_time, duration, stats["total_decisions"],
                        stats["executed_trades"], stats["wins"], stats["losses"],
                        stats["avg_brain_score"], stats["avg_composite_score"],
                        stats["avg_confidence"])
