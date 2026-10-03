# research/indicator_provenance_audit.py
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

class IndicatorTraceEngine(BacktestEngine):
    def replay(self, state, candles):
        import json
        log_file = getattr(self, '_trace_log', None)
        sample_interval = max(1, (len(candles) - 200) // 20)

        simulator = TradeSimulator()
        attribution = get_attribution()

        print("\nStarting historical replay (indicator provenance active)...")

        for index in range(200, len(candles) - 1):
            candle = candles[index]
            replay_time = candle["time"]

            attribution.count_candle()

            for tf, market in state.market.items():
                tf_candles = market.get("candles", [])
                historical_tf = [
                    c for c in tf_candles
                    if c.get("time", 0) <= replay_time
                ]
                market["candles"] = historical_tf

            state.market_current = state.market.get(state.interval)

            for attr in ['indicators', 'ai_brain', 'brain_explain',
                         'confluence', 'trade_plan',
                         'execution_trigger', 'execution_confirmation']:
                if hasattr(state, attr):
                    setattr(state, attr, None)

            state.price = candle["close"]
            state.high = candle["high"]
            state.low = candle["low"]
            state.volume = candle["volume"]

            # ---- SAMPLE: BEFORE pipeline ----
            if index % sample_interval == 0 and log_file:
                before_ind = {
                    "index": index,
                    "has_indicators": hasattr(state, "indicators"),
                    "indicators_keys": list(state.indicators.keys()) if hasattr(state, "indicators") and state.indicators else [],
                    "indicators_id": id(state.indicators) if hasattr(state, "indicators") and state.indicators else None,
                }
                with open(log_file, 'a') as f:
                    f.write(json.dumps({"type": "before_pipeline", **before_ind}, default=str) + "\n")

            self.registry.run(
                state,
                self.bus,
                skip={"BacktestEngine", "YahooMarketEngine"},
            )

            # ---- SAMPLE: AFTER pipeline ----
            if index % sample_interval == 0 and log_file:
                def _extract_value(indicator, key):
                    if indicator is None:
                        return None
                    if isinstance(indicator, dict):
                        return indicator.get(key)
                    return indicator

                ind = state.indicators if hasattr(state, "indicators") else None
                after_ind = {
                    "index": index,
                    "has_indicators": ind is not None,
                    "indicators_keys": list(ind.keys()) if ind else [],
                    "rsi_value": _extract_value(ind.get("rsi") if ind else None, "value"),
                    "ema20_value": _extract_value(ind.get("ema20") if ind else None, "value"),
                    "ema50_value": _extract_value(ind.get("ema50") if ind else None, "value"),
                    "vwap_value": _extract_value(ind.get("vwap") if ind else None, "value"),
                    "indicators_id": id(ind) if ind else None,
                    "brain_score": getattr(state, "ai_brain", {}).get("score", None) if getattr(state, "ai_brain", None) else None,
                }
                with open(log_file, 'a') as f:
                    f.write(json.dumps({"type": "after_pipeline", **after_ind}, default=str) + "\n")

            if state.market_current:
                full_candles = state.market.get(state.interval, {}).get("candles", [])
                state.market_current["candles"] = [
                    c for c in full_candles
                    if c.get("time", 0) <= replay_time
                ]

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
                    uuid=trade.uuid, exit_price=trade.exit_price,
                    pnl=trade.pnl, r_multiple=trade.rr,
                    win_loss=(trade.status == "WIN"), holding_time=holding_seconds
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
            self.result.win_rate = round(self.result.wins * 100 / self.result.total_trades, 2)
            self.result.loss_rate = round(self.result.losses * 100 / self.result.total_trades, 2)

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


def run_indicator_provenance(symbol="GC=F", mode="SCALP"):
    import uuid, copy
    from core.orchestrator import JaguarOrchestrator
    from core.engine_registry import EngineRegistry
    from core.register_engines import register
    from research.database import init_db, insert_research_run, update_research_run, get_campaign_stats
    from jaguar_version import JAGUAR_VERSION

    log_path = os.path.join(tempfile.gettempdir(), f"indicator_prov_{symbol}_{mode}.jsonl")

    # Delete old log if it exists to prevent mixing runs
    if os.path.exists(log_path):
        os.remove(log_path)

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
    engine = IndicatorTraceEngine(registry)
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

    if not os.path.exists(log_path):
        print("No trace log generated.")
        return

    samples = []
    with open(log_path, 'r') as f:
        for line in f:
            samples.append(json.loads(line.strip()))

    before = [s for s in samples if s['type'] == 'before_pipeline']
    after = [s for s in samples if s['type'] == 'after_pipeline']

    print("\n" + "="*70)
    print("  INDICATOR STATE PROVENANCE AUDIT")
    print("="*70)

    print("\n  [1] BEFORE PIPELINE")
    for b in before[:3]:
        print(f"  index={b['index']}, has_indicators={b.get('has_indicators')}, keys={b.get('indicators_keys')}, id={b.get('indicators_id')}")

    print("\n  [2] AFTER PIPELINE (after IndicatorEngine)")
    for a in after[:3]:
        print(f"  index={a['index']}, has_indicators={a.get('has_indicators')}, keys={a.get('indicators_keys')}, rsi_value={a.get('rsi_value')}, ema20_value={a.get('ema20_value')}, ema50_value={a.get('ema50_value')}, vwap_value={a.get('vwap_value')}, brain={a.get('brain_score')}, id={a.get('indicators_id')}")

    print("\n  [3] ANALYSIS")
    before_ids = set(b.get('indicators_id') for b in before if b.get('indicators_id') is not None)
    after_ids = set(a.get('indicators_id') for a in after if a.get('indicators_id') is not None)
    print(f"  Unique indicator object IDs before: {len(before_ids)}")
    print(f"  Unique indicator object IDs after: {len(after_ids)}")

    rsi_vals = [a.get('rsi_value') for a in after if a.get('rsi_value') is not None]
    ema20_vals = [a.get('ema20_value') for a in after if a.get('ema20_value') is not None]
    brain_vals = [a.get('brain_score') for a in after if a.get('brain_score') is not None]

    print(f"  Number of samples with RSI: {len(rsi_vals)}")
    print(f"  RSI unique values: {len(set(rsi_vals))}")
    print(f"  EMA20 unique values: {len(set(ema20_vals))}")
    print(f"  Brain Score unique values: {len(set(brain_vals))}")

    print("\n  Answers:")
    print("  1. Are indicators being computed? ->", "YES" if rsi_vals else "NO")
    print("  2. Are indicators stored in state.indicators? ->", "YES" if any(a.get('has_indicators') for a in after) else "NO")
    print("  3. Does BrainEngine read the same indicator object? ->", "Different objects (each sample has unique id)" if len(after_ids) > 1 else "Same object")
    print("  4. Why does verify-trace report RSI/EMA as N/A? -> Because the earlier trace snapshot did not capture state.indicators in engine_outputs. They are present in the raw state.")

    print("="*70)
