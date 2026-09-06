# validation/runner.py
import copy
from core.orchestrator import JaguarOrchestrator
from core.engine_registry import EngineRegistry
from core.register_engines import register
from core.backtest_engine import BacktestEngine
from research.database import init_db

def run_backtest(symbol, mode):
    """Run a backtest for a single symbol and mode."""
    print(f"\n📊 Backtesting {symbol} – {mode}")
    app = JaguarOrchestrator()
    state = app.analyze(symbol, "15m", mode=mode)

    backtest_state = copy.deepcopy(state)
    backtest_state.symbol = symbol
    backtest_state.interval = "15m"
    backtest_state.mode = mode

    registry = EngineRegistry()
    register(registry)
    backtest_engine = BacktestEngine(registry)
    bus = app.bus
    backtest_engine.run(backtest_state, bus)

    return backtest_state

def run_validation(symbols, modes):
    """Run backtests for multiple symbols and modes."""
    init_db()
    results = {}
    for symbol in symbols:
        for mode in modes:
            try:
                state = run_backtest(symbol, mode)
                results[(symbol, mode)] = state.backtest
            except Exception as e:
                print(f"❌ Backtest failed for {symbol} {mode}: {e}")
                results[(symbol, mode)] = None
    return results
