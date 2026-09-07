# research/dead_engine_diagnostic.py
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

DEAD_ENGINES = ["Gann", "MTF", "Order Block", "Regime", "SMC"]

class DeadEngineDiagnosticEngine(BacktestEngine):
    """Replays each candle and logs the output of the five inactive engines."""

    def replay(self, state, candles):
        simulator = TradeSimulator()
        attribution = get_attribution()

        full_candles_by_tf = {}
        for tf, market in state.market.items():
            full_candles_by_tf[tf] = market.get("candles", [])[:]

        logs = []

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

            # Capture engine outputs
            entry = {"index": index, "timestamp": replay_time}
            for eng_name in DEAD_ENGINES:
                attr_name = eng_name.lower().replace(" ", "_")  # e.g., "order_block", "regime", etc.
                val = getattr(state, attr_name, None)
                entry[eng_name] = val
            logs.append(entry)

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

        self._analyze(logs)


    def _analyze(self, logs):
        total = len(logs)
        print("\n" + "=" * 70)
        print("  DEAD ENGINE DIAGNOSTIC")
        print("=" * 70)
        print(f"  Candles analysed : {total}")

        for eng_name in DEAD_ENGINES:
            vals = [entry.get(eng_name) for entry in logs]
            # Count distinct representations
            none_count = sum(1 for v in vals if v is None)
            empty_dict_count = sum(1 for v in vals if isinstance(v, dict) and not v)
            zero_score_count = 0
            nonzero_count = 0
            for v in vals:
                if isinstance(v, dict):
                    score = v.get("score", None)
                    if score == 0:
                        zero_score_count += 1
                    elif score is not None and score != 0:
                        nonzero_count += 1
                elif isinstance(v, (int, float)):
                    if v == 0:
                        zero_score_count += 1
                    else:
                        nonzero_count += 1

            print(f"\n  Engine: {eng_name}")
            print(f"    None / not set : {none_count}")
            print(f"    Empty dict     : {empty_dict_count}")
            print(f"    Zero score     : {zero_score_count}")
            print(f"    Non‑zero       : {nonzero_count}")

            # Classification
            if none_count == total:
                print(f"    Classification: LOGIC DEFECT or DATA MISSING – engine never writes to state")
                print(f"    Likely the engine runner is not calling the engine, or the engine is disabled.")
            elif zero_score_count == total or (empty_dict_count + zero_score_count) == total:
                print(f"    Classification: CONSTANT ZERO – engine runs but always produces zero")
                print(f"    Possible threshold too high, or indicator input missing/zero.")
            elif nonzero_count > 0:
                print(f"    Classification: ACTIVE – engine does produce non‑zero output occasionally")
            else:
                print(f"    Classification: UNKNOWN – review raw output")

            # Show a sample of the output
            unique_samples = list(set(str(v)[:120] for v in vals if v is not None))[:3]
            if unique_samples:
                print(f"    Sample outputs: {unique_samples}")

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


def run_dead_engine_diagnostic(symbol="GC=F", mode="SCALP"):
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
    engine = DeadEngineDiagnosticEngine(registry)
    bus = app.bus

    engine.run(backtest_state, bus)

    end_time = datetime.now().isoformat()
    duration = (datetime.now() - datetime.fromisoformat(start_time)).total_seconds()
    stats = get_campaign_stats(run_id)
    update_research_run(run_id, end_time, duration, stats["total_decisions"],
                        stats["executed_trades"], stats["wins"], stats["losses"],
                        stats["avg_brain_score"], stats["avg_composite_score"],
                        stats["avg_confidence"])
