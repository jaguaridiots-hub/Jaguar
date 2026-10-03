# research/audit_candidate_setups.py
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

class CandidateAuditEngine(BacktestEngine):
    """Replays each candle and logs the first failing prerequisite for trade entry."""

    def replay(self, state, candles):
        import json

        log_file = getattr(self, '_log_path', None)
        simulator = TradeSimulator()
        attribution = get_attribution()

        # Save full lists
        full_candles_by_tf = {}
        for tf, market in state.market.items():
            full_candles_by_tf[tf] = market.get("candles", [])[:]

        print("\nStarting candidate setup audit...")
        rejection_log = []

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

            # Re-apply slice
            if state.market_current:
                full_current = full_candles_by_tf[state.interval]
                state.market_current["candles"] = [c for c in full_current if c.get("time", 0) <= replay_time]

            # --- Inspect rejection path ---
            master = getattr(state, "master_decision", {})
            planner = getattr(state, "trade_plan", {})
            trigger = getattr(state, "execution_trigger", {})
            confirmation = getattr(state, "execution_confirmation", {})
            trade_uuid = getattr(state, "_trade_id", None)

            decision = master.get("decision", "UNKNOWN")
            reason = None
            stage = None

            # Determine the first failing stage
            if decision in ("REJECT", "WAIT"):
                reasons = master.get("reasons", [])
                reason = reasons[0] if reasons else "Unknown rejection"
                stage = "Master Decision"
            elif decision in ("BUY", "SELL") and not planner:
                reason = "No Trade Plan"
                stage = "Trade Planner"
            elif decision in ("BUY", "SELL") and planner:
                # Check execution gates
                trigger_confirmed = trigger.get("confirmed", False) if isinstance(trigger, dict) else False
                confirm_confirmed = confirmation.get("confirmed", False) if isinstance(confirmation, dict) else False
                if not trigger_confirmed:
                    trigger_reasons = trigger.get("reasons", [])
                    reason = trigger_reasons[0] if trigger_reasons else "Trigger not confirmed"
                    stage = "Execution Trigger"
                elif not confirm_confirmed:
                    confirm_reasons = confirmation.get("reasons", [])
                    reason = confirm_reasons[0] if confirm_reasons else "Confirmation not confirmed"
                    stage = "Execution Confirmation"
                elif trade_uuid is None:
                    reason = "Execution Engine Skipped"
                    stage = "Execution Engine"
                else:
                    # Trade actually opened
                    stage = "TRADE OPENED"
                    reason = "Success"
            else:
                reason = "Unknown decision"
                stage = "Unknown"

            entry = {
                "index": index,
                "timestamp": str(replay_time),
                "price": candle["close"],
                "stage": stage,
                "reason": reason,
            }
            rejection_log.append(entry)

        # Write log if needed
        if log_file:
            with open(log_file, 'w') as f:
                json.dump(rejection_log, f, indent=2)

        # Produce the report from rejection_log
        total = len(rejection_log)
        stage_counter = Counter()
        reason_counter = Counter()
        rejected_samples = [e for e in rejection_log if e["stage"] != "TRADE OPENED"]
        display_samples = rejected_samples[:20]

        for e in rejection_log:
            stage_counter[e["stage"]] += 1
            if e["stage"] != "TRADE OPENED":
                reason_counter[e["reason"]] += 1

        print("\n" + "=" * 70)
        print("  CANDIDATE SETUP AUDIT – REJECTION ANALYSIS")
        print("=" * 70)
        print(f"  Total candles evaluated : {total}")
        trades_opened = stage_counter.get("TRADE OPENED", 0)
        print(f"  Trades opened           : {trades_opened}")

        # Percentages per stage
        print("\n  Rejection by Stage:")
        for stage in ["Master Decision", "Trade Planner", "Execution Trigger",
                      "Execution Confirmation", "Execution Engine", "Unknown"]:
            count = stage_counter.get(stage, 0)
            pct = (count / total * 100) if total else 0
            print(f"  {stage:25s}: {count:5d} ({pct:5.1f}%)")

        print("\n  Top Rejection Reasons:")
        for reason, cnt in reason_counter.most_common(15):
            pct = (cnt / total * 100) if total else 0
            print(f"  {reason:40s}: {cnt:5d} ({pct:5.1f}%)")

        # Dominant bottleneck
        if reason_counter:
            top_reason, top_count = reason_counter.most_common(1)[0]
            print(f"\n  PRIMARY BOTTLENECK: {top_reason} ({top_count} occurrences)")
        else:
            print("  No rejections found.")

        # First 20 rejected examples
        print("\n  First 20 Rejected Examples (Timestamp, Price, Reason):")
        for i, ex in enumerate(display_samples, 1):
            print(f"  {i:2d}. {ex['timestamp']:25s}  Price={ex['price']:>8.2f}  Reason: {ex['reason']}")

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


def run_candidate_audit(symbol="GC=F", mode="SCALP"):
    import uuid, copy
    from core.orchestrator import JaguarOrchestrator
    from core.engine_registry import EngineRegistry
    from core.register_engines import register
    from research.database import init_db, insert_research_run, update_research_run, get_campaign_stats
    from jaguar_version import JAGUAR_VERSION

    log_path = os.path.join(tempfile.gettempdir(), f"candidate_audit_{symbol}_{mode}.json")
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
    engine = CandidateAuditEngine(registry)
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
