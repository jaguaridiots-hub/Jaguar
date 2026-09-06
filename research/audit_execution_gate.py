# research/audit_execution_gate.py
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

class ExecutionGateAuditEngine(BacktestEngine):
    """Logs every decision gate to find why trades are never opened."""

    def replay(self, state, candles):
        import json

        log_file = getattr(self, '_log_path', None)
        simulator = TradeSimulator()
        attribution = get_attribution()

        full_candles_by_tf = {}
        for tf, market in state.market.items():
            full_candles_by_tf[tf] = market.get("candles", [])[:]

        gate_log = []
        print("\nStarting execution gate audit...")

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

            # --- Inspect execution gates ---
            master = getattr(state, "master_decision", {})
            planner = getattr(state, "trade_plan", {})
            decision = master.get("decision", "UNKNOWN")
            risk = getattr(state, "risk", {})
            trigger = getattr(state, "execution_trigger", {})
            confirmation = getattr(state, "execution_confirmation", {})

            gate_entry = {
                "index": index,
                "master_decision": decision,
                "trade_plan_exists": bool(planner),
                "trade_plan": str(planner)[:200] if planner else None,
                "execution_trigger": str(trigger)[:200] if trigger else None,
                "execution_confirmation": str(confirmation)[:200] if confirmation else None,
                "risk_status": risk.get("status") if isinstance(risk, dict) else None,
                "trade_uuid": getattr(state, "_trade_id", None),
            }
            gate_log.append(gate_entry)

            if decision not in ["BUY", "SELL"] or not planner:
                continue

            attribution.count_executed_trade()
            trade_uuid = getattr(state, "_trade_id", None)

            if trade_uuid is None:
                continue

            # --- Trade opened (should not happen if UUID is always None) ---
            quantity = risk.get("position_size", 1.0) if isinstance(risk, dict) else 1.0
            entry_time_str = _to_iso(replay_time)
            trade = Trade(
                direction=decision, entry=planner["entry"],
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

            self.result.total_trades += 1
            if trade.status == "WIN":
                self.result.wins += 1
            elif trade.status == "LOSS":
                self.result.losses += 1

        if log_file:
            with open(log_file, 'w') as f:
                json.dump(gate_log, f, indent=2)

        print(f"Execution gate audit complete. Trades: {self.result.total_trades}")


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


def run_execution_gate_audit(symbol="GC=F", mode="SCALP"):
    import uuid, copy
    from core.orchestrator import JaguarOrchestrator
    from core.engine_registry import EngineRegistry
    from core.register_engines import register
    from research.database import init_db, insert_research_run, update_research_run, get_campaign_stats
    from jaguar_version import JAGUAR_VERSION

    log_path = os.path.join(tempfile.gettempdir(), f"execution_gate_{symbol}_{mode}.json")
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
    engine = ExecutionGateAuditEngine(registry)
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

    # Analyze
    if not os.path.exists(log_path):
        print("No gate log generated.")
        return

    with open(log_path, 'r') as f:
        gates = json.load(f)

    total = len(gates)
    master_buy_sell = [g for g in gates if g["master_decision"] in ("BUY", "SELL")]
    with_trade_plan = [g for g in master_buy_sell if g["trade_plan_exists"]]
    with_uuid = [g for g in master_buy_sell if g["trade_uuid"] is not None]
    with_risk_safe = [g for g in master_buy_sell if g.get("risk_status") == "SAFE"]

    print("\n" + "=" * 70)
    print("  EXECUTION GATE AUDIT")
    print("=" * 70)
    print(f"  Total decisions logged           : {total}")
    print(f"  Master BUY/SELL                  : {len(master_buy_sell)}")
    print(f"    - Trade plan populated         : {len(with_trade_plan)}")
    print(f"    - Risk status present          : {with_risk_safe}")
    print(f"    - Execution trigger present    : {len([g for g in master_buy_sell if g.get('execution_trigger')])}")
    print(f"    - Execution confirmation present : {len([g for g in master_buy_sell if g.get('execution_confirmation')])}")
    print(f"    - Trade UUID assigned          : {len(with_uuid)}")

    print(f"\n  GATE FAILURE POINT")
    if len(master_buy_sell) == 0:
        print("  ❌ No BUY/SELL decisions – Master Decision is blocking all trades.")
    elif len(with_trade_plan) == 0:
        print("  ❌ Trade plan is never populated after Master BUY/SELL.")
        print("     → Inspect TradePlannerEngineRunner / trade_planner_engine.py")
    elif len(with_uuid) == 0 and len(with_trade_plan) > 0:
        print("  ❌ Trade plan exists but ExecutionEngine never assigns a trade UUID.")
        print("     → The condition inside ExecutionEngine.execute() that calls record_trade_open() is not met.")
        print("     → Likely checks: state.trade_plan, state.master_decision['decision'], state.risk status, execution_trigger/confirmation flags.")
        print("     → Inspect strategy/execution_engine.py : run() or execute() method.")
    elif len(with_uuid) > 0:
        print(f"  ✅ {len(with_uuid)} trades were assigned UUIDs.")
    else:
        print("  Unknown gate failure – review the log file.")

    print("=" * 70)
