# research/regime_audit.py
import json
from datetime import datetime
from collections import Counter
from core.backtest_engine import BacktestEngine
from core.trade import Trade
from core.trade_simulator import TradeSimulator
from core.filter_attribution import get_attribution
from research.recorder import record_trade_close, record_decision_snapshot
from research.database import update_decision_outcome, update_decision_stage

class RegimeAuditEngine(BacktestEngine):
    """Replays candles and collects regime outputs per decision."""

    def replay(self, state, candles):
        simulator = TradeSimulator()
        attribution = get_attribution()

        full_candles_by_tf = {}
        for tf, market in state.market.items():
            full_candles_by_tf[tf] = market.get("candles", [])[:]

        regime_log = []

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

            # Capture regime
            regime_obj = getattr(state, "regime", None)
            regime_label = "UNKNOWN"
            if isinstance(regime_obj, dict):
                regime_label = regime_obj.get("regime", "UNKNOWN")
            elif isinstance(regime_obj, str):
                regime_label = regime_obj

            regime_log.append({
                "index": index,
                "timestamp": str(replay_time),
                "price": candle["close"],
                "regime": regime_label,
            })

            # Original trade logic (unchanged, but we won't simulate trades in this audit)
            # We can skip trade recording to speed things up, but for completeness we'll keep it.
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
        total = len(regime_log)
        regime_counts = Counter(r["regime"] for r in regime_log)
        print("\n" + "=" * 70)
        print("  REGIME AUDIT")
        print("=" * 70)
        print(f"  Total candles analysed : {total}")
        print(f"\n  Regime Distribution:")
        for regime, cnt in regime_counts.most_common():
            pct = cnt / total * 100
            print(f"  {regime:15s}: {cnt:6d} ({pct:5.1f}%)")

        # Print raw regime labels and first few examples for non-COMPRESSION
        non_comp = [r for r in regime_log if r["regime"] != "COMPRESSION"]
        if non_comp:
            print(f"\n  Non-COMPRESSION examples (first 10):")
            for r in non_comp[:10]:
                print(f"    Index={r['index']}, Price={r['price']:.2f}, Regime={r['regime']}")
        else:
            print(f"\n  ⚠️  ALL candles classified as COMPRESSION – possible logic defect or very low ADX.")
            print(f"  Inspect strategy/regime_engine.py for the ADX threshold and decision logic.")

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


def run_regime_audit(symbol="GC=F", mode="SCALP"):
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
    engine = RegimeAuditEngine(registry)
    bus = app.bus

    engine.run(backtest_state, bus)

    end_time = datetime.now().isoformat()
    duration = (datetime.now() - datetime.fromisoformat(start_time)).total_seconds()
    stats = get_campaign_stats(run_id)
    update_research_run(run_id, end_time, duration, stats["total_decisions"],
                        stats["executed_trades"], stats["wins"], stats["losses"],
                        stats["avg_brain_score"], stats["avg_composite_score"],
                        stats["avg_confidence"])
