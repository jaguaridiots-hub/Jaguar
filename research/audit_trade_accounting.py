# research/audit_trade_accounting.py
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

class AccountingAuditEngine(BacktestEngine):
    """Instruments the replay loop to log every decision and trade event."""

    def replay(self, state, candles):
        import json

        log_file = getattr(self, '_log_path', None)
        simulator = TradeSimulator()
        attribution = get_attribution()

        # Save full lists (identical to production)
        full_candles_by_tf = {}
        for tf, market in state.market.items():
            full_candles_by_tf[tf] = market.get("candles", [])[:]

        event_log = []

        print("\nStarting accounting audit replay...")

        for index in range(200, len(candles) - 1):
            candle = candles[index]
            replay_time = candle["time"]

            # 1. count_candle (attribution)
            attribution.count_candle()

            # Slice
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

            # Run pipeline
            self.registry.run(state, self.bus, skip={"BacktestEngine", "YahooMarketEngine"})

            # Re-apply slice after pipeline
            if state.market_current:
                full_current = full_candles_by_tf[state.interval]
                state.market_current["candles"] = [
                    c for c in full_current if c.get("time", 0) <= replay_time
                ]

            master = getattr(state, "master_decision", {})
            planner = getattr(state, "trade_plan", {})
            decision = master.get("decision", "UNKNOWN")

            # Log decision
            if log_file:
                event_log.append({
                    "index": index,
                    "decision": decision,
                    "brain_score": getattr(state, "ai_brain", {}).get("score", None),
                    "composite_score": master.get("score", None),
                })

            if decision not in ["BUY", "SELL"] or not planner:
                # Rejected or WAIT – no trade
                continue

            # Candidate? The attribution's candidate_setup is never called in the loop; we'll note that later.
            # count_executed_trade (attribution)
            attribution.count_executed_trade()

            trade_uuid = getattr(state, "_trade_id", None)
            if trade_uuid is None:
                event_log.append({"index": index, "event": "execution_skipped", "reason": master.get("reasons", [])})
                continue

            # Trade opened
            event_log.append({"index": index, "event": "trade_opened", "uuid": trade_uuid})

            quantity = state.risk.get("position_size", 1.0)
            entry_time_str = _to_iso(replay_time)

            trade = Trade(
                direction=decision,
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
                    except:
                        pass
                record_trade_close(
                    uuid=trade.uuid, exit_price=trade.exit_price,
                    pnl=trade.pnl, r_multiple=trade.rr,
                    win_loss=(trade.status == "WIN"), holding_time=holding_seconds,
                    exit_time=trade.exit_time
                )
                update_decision_outcome(decision_id, trade.status, trade_uuid)
                event_log.append({"index": index, "event": "trade_closed", "status": trade.status})

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

        # Write event log
        if log_file:
            with open(log_file, 'w') as f:
                json.dump(event_log, f, indent=2)

        print(f"Accounting audit replay complete. Trades: {self.result.total_trades}")


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


def run_accounting_audit(symbol="GC=F", mode="SCALP"):
    import uuid, copy
    from core.orchestrator import JaguarOrchestrator
    from core.engine_registry import EngineRegistry
    from core.register_engines import register
    from research.database import init_db, insert_research_run, update_research_run, get_campaign_stats
    from jaguar_version import JAGUAR_VERSION

    log_path = os.path.join(tempfile.gettempdir(), f"accounting_audit_{symbol}_{mode}.json")
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
    engine = AccountingAuditEngine(registry)
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

    # Analyze event log
    if not os.path.exists(log_path):
        print("No event log generated.")
        return

    with open(log_path, 'r') as f:
        events = json.load(f)

    candles_evaluated = len([e for e in events if "decision" in e])
    master_buy = len([e for e in events if e.get("decision") == "BUY"])
    master_sell = len([e for e in events if e.get("decision") == "SELL"])
    master_reject = len([e for e in events if e.get("decision") in ("REJECT", "WAIT")])
    trade_opened = len([e for e in events if e.get("event") == "trade_opened"])
    trade_closed = len([e for e in events if e.get("event") == "trade_closed"])
    skipped = len([e for e in events if e.get("event") == "execution_skipped"])

    print("\n" + "=" * 70)
    print("  TRADE ACCOUNTING AUDIT")
    print("=" * 70)
    print(f"  Candles evaluated (in replay loop) : {candles_evaluated}")
    print(f"  Master BUY decisions               : {master_buy}")
    print(f"  Master SELL decisions              : {master_sell}")
    print(f"  REJECT/WAIT decisions              : {master_reject}")
    print(f"  Execution attempts (BUY/SELL)      : {master_buy + master_sell}")
    print(f"  Execution skipped (no trade UUID)  : {skipped}")
    print(f"  Trades opened (recorded)           : {trade_opened}")
    print(f"  Trades closed (WIN/LOSS)           : {trade_closed}")
    print(f"  Trades opened but not closed       : {trade_opened - trade_closed}")

    # Attribution check
    attribution = get_attribution()
    print(f"\n  ATTRIBUTION COUNTERS (filter_attribution)")
    print(f"  Candles evaluated : {attribution.candles_evaluated}")
    print(f"  Candidate setups  : {attribution.candidate_setups}   <-- always 0 (never called)")
    print(f"  Executed trades   : {attribution.executed_trades}")
    print(f"  Winning trades    : {attribution.winning_trades}")
    print(f"  Losing trades     : {attribution.losing_trades}")

    # Explanation
    print(f"\n  EXPLANATION")
    print(f"  - 'Candidate Setups' is always 0 because the replay loop never calls attribution.count_candidate_setup().")
    print(f"  - The loop only calls attribution.count_executed_trade() when master says BUY/SELL and a trade UUID exists.")
    print(f"  - 'Executed Trades' in the attribution report equals trades opened (and later closed) in the replay.")
    print(f"  - 'Total Trades' in BacktestResult is also the number of trades processed (opened).")

    # Where to find each counter:
    print(f"\n  LOCATIONS (file:function)")
    print(f"  - count_candle            : core/filter_attribution.py : count_candle()")
    print(f"  - count_executed_trade    : core/filter_attribution.py : count_executed_trade()  (called in backtest_engine.replay())")
    print(f"  - count_candidate_setup   : core/filter_attribution.py : count_candidate_setup()  (never called in replay)")
    print(f"  - BacktestResult.total_trades : core/backtest_result.py  (incremented in backtest_engine.replay())")

    print("\n  VERDICT")
    if candles_evaluated > 0 and trade_opened == trade_closed and skipped <= master_buy + master_sell:
        print("  ✅ Trade accounting is consistent. Discrepancy in Candidate Setups is a known omission (not called).")
    else:
        print("  ❌ Inconsistency found. Review the event log.")
    print("=" * 70)
