# research/threshold_impact_analysis.py
import json
import os
import tempfile
from datetime import datetime
from collections import defaultdict
from core.backtest_engine import BacktestEngine
from core.trade import Trade
from core.trade_simulator import TradeSimulator
from core.filter_attribution import get_attribution
from research.recorder import record_trade_close, record_decision_snapshot
from research.database import update_decision_outcome, update_decision_stage
from research.research_trade_planner import generate_research_plan


class ThresholdImpactEngine(BacktestEngine):
    """
    Replays all candles.  For every Master BUY/SELL decision
    (including those later blocked by gates) we capture the plan.
    For Master REJECT decisions we generate a research plan.
    Then we apply various composite‑score thresholds and also test
    removing the SMC‑confirmation gate.
    """

    def replay(self, state, candles):
        import json

        simulator = TradeSimulator()
        attribution = get_attribution()

        # Save full history
        full_candles_by_tf = {}
        for tf, market in state.market.items():
            full_candles_by_tf[tf] = market.get("candles", [])[:]

        opportunities = []

        for index in range(200, len(candles) - 1):
            candle = candles[index]
            replay_time = candle["time"]
            attribution.count_candle()

            # Slice market data
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

            self.registry.run(state, self.bus,
                              skip={"BacktestEngine", "YahooMarketEngine"})

            # Re‑apply slice after pipeline
            if state.market_current:
                full_current = full_candles_by_tf[state.interval]
                state.market_current["candles"] = [
                    c for c in full_current if c.get("time", 0) <= replay_time
                ]

            master = getattr(state, "master_decision", {})
            planner = getattr(state, "trade_plan", {})
            decision = master.get("decision", "UNKNOWN")
            composite = master.get("score", 0)
            reasons = master.get("reasons", [])

            # Obtain a plan – real if available, otherwise research
            if decision in ("BUY", "SELL") and planner:
                plan = {
                    "entry": planner["entry"],
                    "stop": planner["stop"],
                    "tp1": planner["tp1"],
                    "tp2": planner.get("tp2", planner["tp1"]),
                    "direction": decision,
                }
            else:
                # For Master REJECT (or BUY/SELL without a plan) we create a research plan
                plan = generate_research_plan(state)
                plan["direction"] = decision if decision in ("BUY", "SELL") else "BUY"  # default for REJECT

            opportunities.append({
                "index": index,
                "composite_score": composite,
                "decision": decision,
                "plan": plan,
                "reasons": reasons,
            })

            # ---- Original trade execution (unchanged) ----
            decision_id = record_decision_snapshot(state, candle_timestamp=replay_time)
            trade_uuid = getattr(state, "_trade_id", None)
            if trade_uuid is None:
                continue
            quantity = state.risk.get("position_size", 1.0)
            entry_time_str = _to_iso(replay_time)
            trade = Trade(
                direction=plan["direction"], entry=plan["entry"],
                stop_loss=plan["stop"], take_profit_1=plan["tp1"],
                take_profit_2=plan["tp2"],
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
            elif trade.status == "LOSS":
                self.result.losses += 1

        if self.result.total_trades:
            self.result.win_rate = round(self.result.wins * 100 / self.result.total_trades, 2)
            self.result.loss_rate = round(self.result.losses * 100 / self.result.total_trades, 2)

        # ---- Threshold simulation ----
        thresholds = [40, 45, 50, 55, 60, 65, 70, 75, 80]
        results_with_smc = {}
        results_without_smc = {}

        for thresh in thresholds:
            # With SMC gate
            accepted = []
            for opp in opportunities:
                if opp["composite_score"] < thresh:
                    continue
                if "Score moderate but lacking SMC confirmation" in opp["reasons"]:
                    continue
                accepted.append(opp)
            results_with_smc[thresh] = _simulate(accepted, simulator, candles)

            # Without SMC gate
            accepted_no_smc = []
            for opp in opportunities:
                if opp["composite_score"] < thresh:
                    continue
                accepted_no_smc.append(opp)
            results_without_smc[thresh] = _simulate(accepted_no_smc, simulator, candles)

        self._print_report(opportunities, thresholds, results_with_smc, results_without_smc)

    def _print_report(self, opportunities, thresholds, results_with_smc, results_without_smc):
        print("\n" + "=" * 70)
        print("  THRESHOLD IMPACT ANALYSIS – FULL REPLAY SIMULATION")
        print("=" * 70)
        print(f"  Total candles processed : {len(opportunities)}")

        # ---- With SMC gate ----
        print("\n  [1] WITH SMC GATE (current behaviour)")
        print(f"  {'Thresh':>6s} {'Trades':>7s} {'WinRate':>8s} {'PF':>7s} {'Expect':>8s} {'MaxDD':>8s}")
        print(f"  {'-'*6} {'-'*7} {'-'*8} {'-'*7} {'-'*8} {'-'*8}")
        for thresh in thresholds:
            r = results_with_smc[thresh]
            print(f"  {thresh:>6d} {r['trades']:>7d} {r['win_rate']:>7.1f}% {r['profit_factor']:>7.2f} {r['expectancy']:>+8.2f} {r['max_dd']:>8.0f}")

        # ---- Without SMC gate ----
        print("\n  [2] WITHOUT SMC GATE (removing 'Score moderate…' rejections)")
        print(f"  {'Thresh':>6s} {'Trades':>7s} {'WinRate':>8s} {'PF':>7s} {'Expect':>8s} {'MaxDD':>8s}")
        print(f"  {'-'*6} {'-'*7} {'-'*8} {'-'*7} {'-'*8} {'-'*8}")
        for thresh in thresholds:
            r = results_without_smc[thresh]
            print(f"  {thresh:>6d} {r['trades']:>7d} {r['win_rate']:>7.1f}% {r['profit_factor']:>7.2f} {r['expectancy']:>+8.2f} {r['max_dd']:>8.0f}")

        # ---- Recommendation ----
        best_thresh = None
        best_pf = 0
        for thresh in thresholds:
            r = results_without_smc[thresh]
            if r['trades'] >= 50 and r['profit_factor'] > best_pf:
                best_pf = r['profit_factor']
                best_thresh = thresh
        if best_thresh is not None:
            print(f"\n  RECOMMENDED THRESHOLD: {best_thresh} (without SMC gate) → PF {best_pf:.2f}")
        else:
            print("\n  No threshold produced ≥50 trades with PF > 0.")

        print("=" * 70)


def _simulate(opportunities, simulator, candles):
    """Simulate the given opportunities and return metrics."""
    if not opportunities:
        return {"trades": 0, "win_rate": 0, "profit_factor": 0, "expectancy": 0, "max_dd": 0}

    total = len(opportunities)
    wins = 0
    gross_profit = 0.0
    gross_loss = 0.0
    cumulative = 0.0
    peak = -float('inf')
    max_dd = 0.0
    for opp in opportunities:
        plan = opp["plan"]
        idx = opp["index"]
        future_candles = candles[idx + 1:]
        trade = Trade(
            direction=plan["direction"],
            entry=plan["entry"],
            stop_loss=plan["stop"],
            take_profit_1=plan["tp1"],
            take_profit_2=plan["tp2"],
            entry_time=str(candles[idx]["time"]),
            quantity=1.0,
            uuid=None
        )
        simulator.simulate(trade, future_candles)
        trade.compute_pnl()
        if trade.status == "WIN":
            wins += 1
        if trade.status in ("WIN", "LOSS"):
            pnl = trade.pnl if trade.pnl else 0
            if pnl > 0:
                gross_profit += pnl
            else:
                gross_loss += abs(pnl)
            cumulative += pnl
            if cumulative > peak:
                peak = cumulative
            else:
                dd = peak - cumulative
                if dd > max_dd:
                    max_dd = dd

    wr = wins / total * 100 if total else 0
    pf = gross_profit / gross_loss if gross_loss else float('inf')
    avg_win = gross_profit / wins if wins else 0
    avg_loss = gross_loss / (total - wins) if (total - wins) else 0
    expectancy = (wins/total * avg_win) - ((total-wins)/total * avg_loss)
    return {
        "trades": total,
        "win_rate": wr,
        "profit_factor": pf,
        "expectancy": expectancy,
        "max_dd": max_dd
    }


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


def run_threshold_impact_analysis(symbol="GC=F", mode="SCALP"):
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
    engine = ThresholdImpactEngine(registry)
    bus = app.bus

    engine.run(backtest_state, bus)

    end_time = datetime.now().isoformat()
    duration = (datetime.now() - datetime.fromisoformat(start_time)).total_seconds()
    stats = get_campaign_stats(run_id)
    update_research_run(run_id, end_time, duration, stats["total_decisions"],
                        stats["executed_trades"], stats["wins"], stats["losses"],
                        stats["avg_brain_score"], stats["avg_composite_score"],
                        stats["avg_confidence"])
