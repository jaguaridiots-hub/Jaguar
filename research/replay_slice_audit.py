# research/replay_slice_audit.py
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

class SliceAuditEngine(BacktestEngine):
    def replay(self, state, candles):
        import json
        log_file = getattr(self, '_log_path', None)
        sample_interval = max(1, (len(candles) - 200) // 20)

        simulator = TradeSimulator()
        attribution = get_attribution()

        # Save full lists
        full_candles_by_tf = {}
        for tf, market in state.market.items():
            full_candles_by_tf[tf] = market.get("candles", [])[:]

        print("\nStarting slice audit replay...")

        for index in range(200, len(candles) - 1):
            candle = candles[index]
            replay_time = candle["time"]

            attribution.count_candle()

            # Slice from saved originals
            for tf, market in state.market.items():
                full_list = full_candles_by_tf[tf]
                historical_tf = [
                    c for c in full_list
                    if c.get("time", 0) <= replay_time
                ]
                market["candles"] = historical_tf

            state.market_current = state.market.get(state.interval)

            # Clear indicator cache
            if hasattr(state, 'indicators'):
                state.indicators = None

            state.price = candle["close"]
            state.high = candle["high"]
            state.low = candle["low"]
            state.volume = candle["volume"]

            # Run pipeline
            self.registry.run(
                state,
                self.bus,
                skip={"BacktestEngine", "YahooMarketEngine"},
            )

            # Re-apply slice after pipeline
            if state.market_current:
                full_current = full_candles_by_tf[state.interval]
                state.market_current["candles"] = [
                    c for c in full_current
                    if c.get("time", 0) <= replay_time
                ]

            # ---- LOG SAMPLE ----
            if index % sample_interval == 0 and log_file:
                mc = state.market_current
                slice_candles = mc.get("candles", []) if mc else []
                rsi_val = None
                ind = state.indicators if hasattr(state, 'indicators') else None
                if ind:
                    rsi_dict = ind.get('rsi')
                    if isinstance(rsi_dict, dict):
                        rsi_val = rsi_dict.get('value')
                log_entry = {
                    "index": index,
                    "slice_length": len(slice_candles),
                    "first_time": slice_candles[0]["time"] if slice_candles else None,
                    "last_time": slice_candles[-1]["time"] if slice_candles else None,
                    "last_close": slice_candles[-1]["close"] if slice_candles else None,
                    "rsi": rsi_val
                }
                with open(log_file, 'a') as f:
                    f.write(json.dumps(log_entry, default=str) + "\n")

            # ---- Trade logic (unchanged) ----
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

        print(f"Slice audit replay complete. Trades: {self.result.total_trades}")


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


def run_slice_audit(symbol="GC=F", mode="SCALP"):
    import uuid, copy
    from core.orchestrator import JaguarOrchestrator
    from core.engine_registry import EngineRegistry
    from core.register_engines import register
    from research.database import init_db, insert_research_run, update_research_run, get_campaign_stats
    from jaguar_version import JAGUAR_VERSION

    log_path = os.path.join(tempfile.gettempdir(), f"slice_audit_{symbol}_{mode}.jsonl")
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
    engine = SliceAuditEngine(registry)
    engine._log_path = log_path
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
        print("No log generated.")
        return

    entries = []
    with open(log_path, 'r') as f:
        for line in f:
            entries.append(json.loads(line.strip()))

    print("\n" + "="*70)
    print("  REPLAY SLICE AUDIT")
    print("="*70)
    print(f"  Samples: {len(entries)}")
    slice_lengths = [e['slice_length'] for e in entries]
    rsi_vals = [e['rsi'] for e in entries if e['rsi'] is not None]
    print(f"  Slice lengths: {slice_lengths}")
    print(f"  Unique slice lengths: {len(set(slice_lengths))}")
    print(f"  RSI values: {rsi_vals}")
    print(f"  Unique RSI values: {len(set(rsi_vals))}")
    print("="*70)
