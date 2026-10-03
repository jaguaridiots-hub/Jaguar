# research/audit_market_data.py
import sys
from datetime import datetime

def run_market_audit(symbol="GC=F", interval="15m"):
    """
    Load market data for the given symbol/interval using the same engine
    as the production pipeline, then report candle count and quality.
    """
    try:
        from core.orchestrator import JaguarOrchestrator
    except ImportError as e:
        print(f"❌ Could not import Jaguar modules: {e}")
        return

    print("=" * 70)
    print("  MARKET DATA AUDIT")
    print("=" * 70)
    print(f"  Symbol   : {symbol}")
    print(f"  Interval : {interval}")

    # We need a minimal state object – JaguarOrchestrator.analyze() runs the full pipeline.
    # To only load market data, we can directly call YahooMarketEngine with a fresh state.
    # However, YahooMarketEngine expects a bus. We'll simulate a simple bus.

    class DummyBus:
        def publish(self, event, payload=None):
            pass

    try:
        from strategy.yahoo_market_engine import YahooMarketEngine
        from core.state import State  # assuming a State class exists; if not, we use dict
    except ImportError:
        # Fallback: create a minimal state manually
        class State:
            pass

    state = State()
    state.symbol = symbol
    state.interval = interval
    state.mode = "SCALP"  # not critical

    engine = YahooMarketEngine()
    bus = DummyBus()

    print("  Attempting market load (will try Yahoo, then fallback) ...")
    try:
        # This will attempt to load from Yahoo; if it fails, the engine
        # internally catches the error and uses fallback data.
        engine.run(state, bus)
    except Exception as e:
        print(f"  ❌ Market engine raised an exception: {e}")
        # continue to inspect state even after error

    # After run, state.market should be populated
    market = getattr(state, "market", None)
    if market is None:
        print("  ❌ No market data loaded (state.market is missing).")
        return

    tf_data = market.get(interval)
    if tf_data is None:
        print(f"  ❌ No data for timeframe '{interval}'.")
        return

    candles = tf_data.get("candles", [])
    candle_count = len(candles)

    print(f"  Data source        : {'Yahoo' if getattr(state, 'market_source', 'unknown') == 'yahoo' else 'Fallback'}")
    print(f"  Candles returned   : {candle_count}")

    if candle_count == 0:
        print("  ❌ No candles – market load failed completely.")
        return

    # Timestamps and integrity
    first = candles[0]
    last = candles[-1]
    first_time = first.get("time")
    last_time = last.get("time")
    print(f"  Earliest candle    : {first_time}")
    print(f"  Latest candle      : {last_time}")

    # Check required fields
    required_fields = ["time", "open", "high", "low", "close", "volume"]
    missing_fields = set()
    for c in candles:
        for f in required_fields:
            if f not in c or c[f] is None:
                missing_fields.add(f)
    if missing_fields:
        print(f"  ⚠️  Missing fields   : {', '.join(missing_fields)}")
    else:
        print("  ✅ All required OHLCV fields present")

    # Check chronological order
    ordered = True
    for i in range(1, len(candles)):
        if candles[i]["time"] < candles[i-1]["time"]:
            ordered = False
            break
    print(f"  Chronological order: {'✅' if ordered else '❌ NOT chronological'}")

    # Duplicates
    times = [c["time"] for c in candles]
    duplicates = len(times) - len(set(times))
    if duplicates > 0:
        print(f"  ⚠️  Duplicate timestamps: {duplicates}")
    else:
        print("  ✅ No duplicate timestamps")

    # Minimum required for research
    print("\n  RESEARCH READINESS")
    if candle_count >= 500:
        print(f"  ✅ Sufficient candles ({candle_count}) for replay.")
    else:
        print(f"  ❌ Only {candle_count} candle(s) – at least 500 required for reliable replay.")
        if candle_count == 1:
            print("  → Fallback data is likely a single static candle. Check the fallback implementation.")
            print("  → Look for the function that generates fallback data in YahooMarketEngine or market_feed.py.")

    print("=" * 70)
