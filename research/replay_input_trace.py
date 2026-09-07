# research/replay_input_trace.py
import json
import os
import tempfile
from datetime import datetime
from core.backtest_engine import BacktestEngine
from core.trade import Trade
from core.trade_simulator import TradeSimulator
from core.filter_attribution import get_attribution
from research.recorder import record_trade_close, record_decision_snapshot
from research.database import update_decision_outcome, update_decision_stage

class TraceBacktestEngine(BacktestEngine):
    """
    Instrumented backtest engine that logs per‑candle engine inputs and outputs
    at evenly spaced sample points for diagnostic purposes.
    """

    def replay(self, state, candles):
        import json
        from datetime import datetime

        log_file = getattr(self, '_trace_log', None)
        sample_interval = max(1, (len(candles) - 200) // 20)

        simulator = TradeSimulator()
        attribution = get_attribution()

        print("\nStarting historical replay (trace audit active)...")

        for index in range(200, len(candles) - 1):
            candle = candles[index]
            replay_time = candle["time"]

            attribution.count_candle()

            # ---- Update market data for each timeframe ----
            for tf, market in state.market.items():
                tf_candles = market.get("candles", [])
                historical_tf = [
                    c for c in tf_candles
                    if c.get("time", 0) <= replay_time
                ]
                market["candles"] = historical_tf

            state.market_current = state.market.get(state.interval)

            # ---- Clear ONLY transient analysis caches (NOT risk, trade_validator, etc.) ----
            for attr in ['indicators', 'ai_brain', 'brain_explain',
                         'confluence', 'trade_plan',
                         'execution_trigger', 'execution_confirmation']:
                if hasattr(state, attr):
                    setattr(state, attr, None)

            # Update price data
            state.price = candle["close"]
            state.high = candle["high"]
            state.low = candle["low"]
            state.volume = candle["volume"]

            # ---- Capture BEFORE state (market snapshot) ----
            if index % sample_interval == 0 and log_file:
                before_snap = {
                    "index": index,
                    "replay_time": replay_time,
                    "symbol": state.symbol,
                    "timeframe": state.interval,
                    "market_candles_count": len(state.market_current["candles"]) if state.market_current else 0,
                    "latest_candle_time": replay_time,
                    "price": state.price,
                    "high": state.high,
                    "low": state.low,
                    "volume": state.volume,
                }

            # Run the pipeline – skip market download and ourselves
            self.registry.run(
                state,
                self.bus,
                skip={
                    "BacktestEngine",
                    "YahooMarketEngine",
                },
            )

            # Re‑apply slice after pipeline (existing fix)
            if state.market_current:
                full_candles = state.market.get(state.interval, {}).get("candles", [])
                state.market_current["candles"] = [
                    c for c in full_candles
                    if c.get("time", 0) <= replay_time
                ]

            # ---- Capture AFTER state (engine outputs) ----
            if index % sample_interval == 0 and log_file:
                # Engine raw outputs (dicts where available)
                engine_outputs = {}
                for eng_name in ['smc', 'structure', 'mss', 'liquidity', 'fvg',
                                 'order_block', 'premium_discount', 'wyckoff',
                                 'equal_levels', 'volume_profile', 'session',
                                 'gann', 'regime', 'orderflow', 'mtf',
                                 'probability', 'ai_brain', 'brain_explain',
                                 'confluence', 'trade_validator', 'trade_plan',
                                 'execution_trigger', 'execution_confirmation']:
                    obj = getattr(state, eng_name, None)
                    if isinstance(obj, dict):
                        engine_outputs[eng_name] = obj
                    elif obj is not None:
                        engine_outputs[eng_name] = str(obj)

                # Contributions from brain_explain if available
                brain_explain = getattr(state, "brain_explain", {})
                contributions = brain_explain.get("contributions", []) if brain_explain else []

                after_snap = {
                    "index": index,
                    "brain_score": getattr(state, "ai_brain", {}).get("score", None) if getattr(state, "ai_brain", None) else None,
                    "composite_score": getattr(state, "master_decision", {}).get("score", None) if getattr(state, "master_decision", None) else None,
                    "decision": getattr(state, "master_decision", {}).get("decision", None) if getattr(state, "master_decision", None) else None,
                    "engine_outputs": engine_outputs,
                    "contributions": contributions,
                }

                with open(log_file, 'a') as f:
                    f.write(json.dumps({"type": "before", **before_snap}, default=str) + "\n")
                    f.write(json.dumps({"type": "after", **after_snap}, default=str) + "\n")

            # ---- Original trade logic (unchanged) ----
            decision_id = record_decision_snapshot(state, candle_timestamp=replay_time)

            master = getattr(state, "master_decision", {})
            planner = getattr(state, "trade_plan", {})

            if master.get("decision") not in ["BUY", "SELL"] or not planner:
                continue

            direction = master["decision"]

            attribution.count_executed_trade()

            trade_uuid = getattr(state, "_trade_id", None)
            if trade_uuid is None:
                mode_thresholds = {"SCALP": 70, "SWING": 70, "CLASSIC": 50}
                threshold_required = mode_thresholds.get(state.mode.upper(), None)
                reason_text = json.dumps(master.get("reasons", []))
                update_decision_stage(decision_id, "EXECUTION", threshold_required=threshold_required, reasons=reason_text)
                continue

            quantity = state.risk.get("position_size", 1.0)
            entry_time_str = _to_iso(replay_time)

            trade = Trade(
                direction=direction,
                entry=planner["entry"],
                stop_loss=planner["stop"],
                take_profit_1=planner["tp1"],
                take_profit_2=planner.get("tp2", planner["tp1"]),
                entry_time=entry_time_str,
                quantity=quantity,
                uuid=trade_uuid
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
                    except Exception:
                        holding_seconds = 0

                record_trade_close(
                    uuid=trade.uuid,
                    exit_price=trade.exit_price,
                    pnl=trade.pnl,
                    r_multiple=trade.rr,
                    win_loss=(trade.status == "WIN"),
                    holding_time=holding_seconds
                )

                update_decision_outcome(decision_id, trade.status, trade_uuid)

            self.result.total_trades += 1
            if trade.status == "WIN":
                self.result.wins += 1
                attribution.count_winning_trade()
            elif trade.status == "LOSS":
                self.result.losses += 1
                attribution.count_losing_trade()

            self.result.trades.append({
                "direction": trade.direction,
                "entry": trade.entry,
                "exit": trade.exit_price,
                "status": trade.status,
            })

        if self.result.total_trades:
            self.result.win_rate = round(
                self.result.wins * 100 / self.result.total_trades, 2
            )
            self.result.loss_rate = round(
                self.result.losses * 100 / self.result.total_trades, 2
            )

        print(f"Replay complete. Trades: {self.result.total_trades}")


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


def run_input_trace(symbol="GC=F", mode="SCALP"):
    """Run a campaign with input trace logging and print summary."""
    import uuid, copy
    from core.orchestrator import JaguarOrchestrator
    from core.engine_registry import EngineRegistry
    from core.register_engines import register
    from research.database import init_db, insert_research_run, update_research_run, get_campaign_stats
    from jaguar_version import JAGUAR_VERSION

    log_path = os.path.join(tempfile.gettempdir(), f"trace_{symbol}_{mode}.jsonl")

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
    engine = TraceBacktestEngine(registry)
    engine._trace_log = log_path
    bus = app.bus

    engine.run(backtest_state, bus)

    end_time = datetime.now().isoformat()
    duration = (datetime.now() - datetime.fromisoformat(start_time)).total_seconds()
    stats = get_campaign_stats(run_id)
    update_research_run(run_id, end_time, duration, stats["total_decisions"],
                        stats["executed_trades"], stats["wins"], stats["losses"],
                        stats["avg_brain_score"], stats["avg_composite_score"],
                        stats["avg_confidence"])

    # Analyze trace
    if not os.path.exists(log_path):
        print("No trace log generated.")
        return

    samples = []
    with open(log_path, 'r') as f:
        for line in f:
            samples.append(json.loads(line.strip()))

    before = [s for s in samples if s['type'] == 'before']
    after = [s for s in samples if s['type'] == 'after']

    print("\n" + "="*70)
    print("  REPLAY INPUT TRACE AUDIT")
    print("="*70)

    # Analyze per engine
    engines_to_check = ['smc', 'structure', 'liquidity', 'fvg', 'order_block',
                        'premium_discount', 'wyckoff', 'equal_levels',
                        'volume_profile', 'session', 'gann', 'regime',
                        'orderflow', 'mtf', 'probability']

    for eng in engines_to_check:
        output_vals = []
        for a in after:
            out = a.get('engine_outputs', {}).get(eng)
            output_vals.append(out)

        prices = [b['price'] for b in before]
        market_dynamic = len(set(prices)) > 1

        # Contributions dynamic?
        contrib_vals = []
        for a in after:
            contribs = a.get('contributions', [])
            for c in contribs:
                if c.get('engine') == eng or c.get('label') == eng:
                    contrib_vals.append(c.get('contribution'))
        contrib_dynamic = len(set(contrib_vals)) > 1 if contrib_vals else False

        # Output dynamic?
        output_strs = [json.dumps(o, sort_keys=True) if isinstance(o, dict) else str(o) for o in output_vals]
        output_dynamic = len(set(output_strs)) > 1

        print(f"\n  Engine: {eng}")
        print(f"    Market input dynamic?      {'YES' if market_dynamic else 'NO'}")
        print(f"    Raw calculations dynamic?  {'YES' if output_dynamic else 'NO'}")
        print(f"    Final contribution dynamic?{'YES' if contrib_dynamic else 'NO'}")
        if not output_dynamic:
            first = output_vals[0] if output_vals else None
            print(f"    (constant output: {first})")

    print("="*70)
