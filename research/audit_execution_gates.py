# research/audit_execution_gates.py
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

class GateAuditEngine(BacktestEngine):
    """Instruments the execution gates to record rule-level pass/fail information."""

    def replay(self, state, candles):
        import json
        from strategy.execution_trigger_engine import ExecutionTriggerEngine
        from strategy.execution_confirmation_engine import ExecutionConfirmationEngine

        log_file = getattr(self, '_log_path', None)
        simulator = TradeSimulator()
        attribution = get_attribution()

        full_candles_by_tf = {}
        for tf, market in state.market.items():
            full_candles_by_tf[tf] = market.get("candles", [])[:]

        # Patch the trigger engine (plain function)
        original_trigger = ExecutionTriggerEngine.analyze

        def patched_trigger(state):
            result = original_trigger(state)
            if log_file and hasattr(state, 'execution_trigger'):
                trigger_state = state.execution_trigger
                if isinstance(trigger_state, dict):
                    with open(log_file, 'a') as f:
                        f.write(json.dumps({
                            "stage": "trigger",
                            "confirmed": trigger_state.get("confirmed", False),
                            "signal": trigger_state.get("signal", ""),
                            "reasons": trigger_state.get("reasons", []),
                            "score": trigger_state.get("score", 0)
                        }) + "\n")
            return result

        ExecutionTriggerEngine.analyze = patched_trigger

        # Patch the confirmation engine (instance method)
        original_confirm = ExecutionConfirmationEngine.run

        def patched_confirm(self, state, bus):
            result = original_confirm(self, state, bus)
            if log_file and hasattr(state, 'execution_confirmation'):
                confirm_state = state.execution_confirmation
                if isinstance(confirm_state, dict):
                    with open(log_file, 'a') as f:
                        f.write(json.dumps({
                            "stage": "confirmation",
                            "confirmed": confirm_state.get("confirmed", False),
                            "signal": confirm_state.get("signal", ""),
                            "reasons": confirm_state.get("reasons", []),
                            "score": confirm_state.get("score", 0)
                        }) + "\n")
            return result

        ExecutionConfirmationEngine.run = patched_confirm

        try:
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

                # --- Trade logic ---
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
                    update_decision_outcome(decision_id, trade.status, trade_uuid)

                self.result.total_trades += 1
                if trade.status == "WIN":
                    self.result.wins += 1
                    attribution.count_winning_trade()
                elif trade.status == "LOSS":
                    self.result.losses += 1
                    attribution.count_losing_trade()

            if self.result.total_trades:
                self.result.win_rate = round(self.result.wins * 100 / self.result.total_trades, 2)
                self.result.loss_rate = round(self.result.losses * 100 / self.result.total_trades, 2)

        finally:
            ExecutionTriggerEngine.analyze = original_trigger
            ExecutionConfirmationEngine.run = original_confirm

        print(f"Gate audit replay complete. Trades: {self.result.total_trades}")


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


def run_execution_gates_audit(symbol="GC=F", mode="SCALP"):
    import uuid, copy
    from core.orchestrator import JaguarOrchestrator
    from core.engine_registry import EngineRegistry
    from core.register_engines import register
    from research.database import init_db, insert_research_run, update_research_run, get_campaign_stats
    from jaguar_version import JAGUAR_VERSION

    log_path = os.path.join(tempfile.gettempdir(), f"gate_audit_{symbol}_{mode}.jsonl")
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
    engine = GateAuditEngine(registry)
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
        print("No gate log generated.")
        return

    entries = []
    with open(log_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))

    trigger_entries = [e for e in entries if e.get("stage") == "trigger"]
    confirm_entries = [e for e in entries if e.get("stage") == "confirmation"]

    trigger_reasons = Counter()
    trigger_fails = 0
    for e in trigger_entries:
        if not e.get("confirmed"):
            trigger_fails += 1
            for r in e.get("reasons", []):
                trigger_reasons[r] += 1

    confirm_reasons = Counter()
    confirm_fails = 0
    for e in confirm_entries:
        if not e.get("confirmed"):
            confirm_fails += 1
            for r in e.get("reasons", []):
                confirm_reasons[r] += 1

    print("\n" + "=" * 70)
    print("  EXECUTION GATES AUDIT")
    print("=" * 70)

    print(f"\n  [1] EXECUTION TRIGGER ENGINE")
    print(f"  Decisions logged : {len(trigger_entries)}")
    print(f"  Confirmed=False  : {trigger_fails}")
    print(f"  Confirmed=True   : {len(trigger_entries) - trigger_fails}")
    if trigger_reasons:
        print(f"\n  Failed Rules (frequency):")
        print(f"  {'Rule':50s} {'Count':>6s}")
        print(f"  {'-'*50} {'-'*6}")
        for rule, count in trigger_reasons.most_common():
            print(f"  {rule:50s} {count:>6d}")
    else:
        print("  No rule-level reasons recorded.")

    print(f"\n  [2] EXECUTION CONFIRMATION ENGINE")
    print(f"  Decisions logged : {len(confirm_entries)}")
    print(f"  Confirmed=False  : {confirm_fails}")
    print(f"  Confirmed=True   : {len(confirm_entries) - confirm_fails}")
    if confirm_reasons:
        print(f"\n  Failed Rules (frequency):")
        print(f"  {'Rule':50s} {'Count':>6s}")
        print(f"  {'-'*50} {'-'*6}")
        for rule, count in confirm_reasons.most_common():
            print(f"  {rule:50s} {count:>6d}")
    else:
        print("  No rule-level reasons recorded.")

    # Combined rule failure ranking
    combined = trigger_reasons + confirm_reasons
    if combined:
        print(f"\n  [3] COMBINED RULE FAILURE RANKING")
        print(f"  {'Rule':50s} {'Failed':>6s}")
        print(f"  {'-'*50} {'-'*6}")
        for rule, count in combined.most_common():
            print(f"  {rule:50s} {count:>6d}")
        top_rule = combined.most_common(1)[0]
        print(f"\n  🔴 SINGLE MOST RESTRICTIVE RULE: '{top_rule[0]}' (failed {top_rule[1]} times)")
    else:
        print("  No rule failures recorded – gate reasons may be stored elsewhere.")

    print("\n  VERDICT")
    if trigger_fails == len(trigger_entries) and confirm_fails == len(confirm_entries):
        print("  ❌ Both gates block every BUY decision. At least one gate must be relaxed to allow trades.")
    else:
        print("  ✅ Some decisions pass the gates.")
    print("=" * 70)
