# research/suite.py
import uuid
from datetime import datetime
from jaguar_version import JAGUAR_VERSION
from .database import init_db, insert_research_run, update_research_run, get_campaign_stats

def run_research_suite(symbol=None, mode=None, asset_class=None, run_id=None, brain_instance=None):
    from core.orchestrator import JaguarOrchestrator
    from core.backtest_engine import BacktestEngine
    from core.engine_registry import EngineRegistry
    from core.register_engines import register
    import copy

    app = JaguarOrchestrator()
    if symbol is None:
        symbol = "GC=F"
    if mode is None:
        mode = "SCALP"

    state = app.analyze(symbol, "15m", mode=mode)

    if run_id:
        state.run_id = run_id

    # ---- Staged Brain injection ----
    if brain_instance:
        from strategy.master_decision_engine import MasterDecisionEngine
        original_run = MasterDecisionEngine.run

        def patched_run(self, state, bus):
            result = brain_instance.evaluate(state)
            state.master_decision = result
            return state

        MasterDecisionEngine.run = patched_run
        try:
            backtest_state = copy.deepcopy(state)
            backtest_state.symbol = symbol
            backtest_state.interval = "15m"
            backtest_state.mode = mode
            if run_id:
                backtest_state.run_id = run_id

            registry = EngineRegistry()
            register(registry)
            backtest_engine = BacktestEngine(registry)
            bus = app.bus
            backtest_engine.run(backtest_state, bus)
        finally:
            MasterDecisionEngine.run = original_run
    else:
        backtest_state = copy.deepcopy(state)
        backtest_state.symbol = symbol
        backtest_state.interval = "15m"
        backtest_state.mode = mode
        if run_id:
            backtest_state.run_id = run_id

        registry = EngineRegistry()
        register(registry)
        backtest_engine = BacktestEngine(registry)
        bus = app.bus
        backtest_engine.run(backtest_state, bus)

    return backtest_state.backtest


def run_research_campaign(symbol="GC=F", mode="SCALP", asset_class=None, notes=None, brain_instance=None):
    init_db()
    run_id = str(uuid.uuid4())
    start_time = datetime.now().isoformat()
    timeframes = "15m"

    insert_research_run(run_id, JAGUAR_VERSION, symbol, mode, timeframes,
                        notes=notes, start_time=start_time)

    print(f"\n{'='*60}")
    print(f"RESEARCH CAMPAIGN STARTED")
    print(f"Run ID    : {run_id}")
    print(f"Symbol    : {symbol}")
    print(f"Mode      : {mode}")
    print(f"Timeframe : {timeframes}")
    print(f"{'='*60}\n")

    try:
        result = run_research_suite(symbol=symbol, mode=mode,
                                    asset_class=asset_class, run_id=run_id,
                                    brain_instance=brain_instance)
    except Exception as e:
        print(f"⚠️  Research suite failed: {e}")
        result = None

    end_time = datetime.now().isoformat()
    duration = (datetime.now() - datetime.fromisoformat(start_time)).total_seconds()

    stats = get_campaign_stats(run_id)

    update_research_run(
        run_id, end_time, duration,
        stats["total_decisions"], stats["executed_trades"],
        stats["wins"], stats["losses"],
        stats["avg_brain_score"], stats["avg_composite_score"],
        stats["avg_confidence"]
    )

    print(f"\n{'='*60}")
    print("CAMPAIGN COMPLETE")
    print(f"Run ID      : {run_id}")
    print(f"Duration    : {duration:.2f} sec")
    print(f"Symbol      : {symbol}")
    print(f"Mode        : {mode}")
    print(f"Total Decisions : {stats['total_decisions']}")
    print(f"Executed Trades : {stats['executed_trades']}")
    print(f"Wins        : {stats['wins']}")
    print(f"Losses      : {stats['losses']}")
    print(f"Avg Brain Score  : {stats['avg_brain_score']:.2f}")
    print(f"Avg Composite Score : {stats['avg_composite_score']:.2f}")
    print(f"Database    : research.db")
    print(f"{'='*60}\n")

    return run_id


def run_all_modes_campaign(symbol="GC=F", asset_class=None, notes=None):
    modes = ["SCALP", "SWING", "CLASSIC"]
    for mode in modes:
        run_research_campaign(symbol=symbol, mode=mode, asset_class=asset_class, notes=notes)
