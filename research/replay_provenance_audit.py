# research/replay_provenance_audit.py
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

class ProvenanceBacktestEngine(BacktestEngine):
    def replay(self, state, candles):
        import json
        from datetime import datetime
        log_file = getattr(self, '_provenance_log', None)
        sample_interval = max(1, (len(candles) - 200) // 20)

        simulator = TradeSimulator()
        attribution = get_attribution()

        print("\nStarting historical replay (provenance audit active)...")

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

            state.price = candle["close"]
            state.high = candle["high"]
            state.low = candle["low"]
            state.volume = candle["volume"]

            if index % sample_interval == 0 and log_file:
                sample_before = {
                    "index": index,
                    "replay_time": replay_time,
                    "price": state.price,
                    "high": state.high,
                    "low": state.low,
                    "volume": state.volume,
                    "market_current_len": len(state.market_current["candles"]) if state.market_current else 0,
                }

            self.registry.run(
                state,
                self.bus,
                skip={
                    "BacktestEngine",
                    "YahooMarketEngine",
                },
            )

            if index % sample_interval == 0 and log_file:
                master = getattr(state, "master_decision", {})
                brain = getattr(state, "ai_brain", {})
                sample_after = {
                    "index": index,
                    "brain_score": brain.get("score"),
                    "composite_score": master.get("score"),
                    "decision": master.get("decision"),
                }
                with open(log_file, 'a') as f:
                    f.write(json.dumps({"type": "before", **sample_before}) + "\n")
                    f.write(json.dumps({"type": "after", **sample_after}) + "\n")

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


def run_provenance_audit(symbol="GC=F", mode="SCALP"):
    import uuid
    import copy
    from datetime import datetime
    from core.orchestrator import JaguarOrchestrator
    from core.engine_registry import EngineRegistry
    from core.register_engines import register
    from research.database import init_db, insert_research_run, update_research_run, get_campaign_stats
    from jaguar_version import JAGUAR_VERSION

    log_path = os.path.join(tempfile.gettempdir(), f"provenance_{symbol}_{mode}.jsonl")

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
    engine = ProvenanceBacktestEngine(registry)
    engine._provenance_log = log_path
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
        print("No provenance log generated.")
        return

    samples = []
    with open(log_path, 'r') as f:
        for line in f:
            samples.append(json.loads(line.strip()))

    before_samples = [s for s in samples if s['type'] == 'before']
    after_samples = [s for s in samples if s['type'] == 'after']

    print("\n" + "="*70)
    print("  REPLAY DATA PROVENANCE AUDIT")
    print("="*70)
    print(f"  Run ID: {run_id}")
    print(f"  Samples collected: {len(before_samples)} before, {len(after_samples)} after")

    prices = [s['price'] for s in before_samples]
    if len(set(prices)) == 1:
        print("  ❌ OHLCV: constant – market data NOT refreshing per candle.")
    else:
        print(f"  ✅ OHLCV: varies (unique={len(set(prices))}) – fresh per candle.")

    lengths = [s['market_current_len'] for s in before_samples]
    if len(set(lengths)) == 1:
        print("  ❌ market_current candle count: constant – slice not applied.")
    else:
        print(f"  ✅ market_current candle count: varies (min={min(lengths)}, max={max(lengths)}) – slice applied.")

    brain_scores = [s['brain_score'] for s in after_samples if s.get('brain_score') is not None]
    if len(set(brain_scores)) == 1:
        print("  ❌ Brain Score: constant – engines producing static output.")
    else:
        print(f"  ✅ Brain Score: varies (unique={len(set(brain_scores))}) – dynamic output.")

    print("="*70)
