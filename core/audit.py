"""
Blackboard Audit – Phase 2A (canonical ADR-002 EvidenceBlock)
"""
import time
from core.pipeline import analyze
from core.state import JaguarState
from core.blackboard import MarketBlackboard
from core.engine_registry import EngineRegistry
from core.evidence import EvidenceBlock, ADR002_SCHEMA
from core.register_engines import register

# Registry name -> EvidenceBlock.engine mapping
ENGINE_NAME_MAP = {
    "SMC": "SMCEngine",
    "Structure": "StructureEngineRunner",
    "Wyckoff": "WyckoffEngineRunner",
    "Liquidity": "LiquidityEngineRunner",
    "FVG": "FVGEngineRunner",
    "Order Block": "Order Block",
    "Order Flow": "OrderFlowEngineRunner",
    "Volume Profile": "VolumeProfileEngineRunner",
    "Session": "SessionEngineRunner",
    "MTF": "MTF",
    "Regime": "RegimeEngineRunner",
    "Gann": "GannEngineRunner",
    "Equal Levels": "EqualLevelsEngineRunner",
    "Premium/Discount": "PremiumDiscountEngineRunner",
    "MSS": "MSSEngineRunner",
}
# Runtime engines that intentionally do NOT publish EvidenceBlocks.
# They provide market data / preprocessing consumed by downstream engines.
NON_EVIDENCE_ENGINES = {
    "YahooMarketEngine",
    "TimeframeIndicatorEngineRunner",
}



def populate_minimal_state(state: JaguarState):
    """Inject minimal market data so engines can run without crashing."""
    # Dummy candles (100 bars)
    candles = []
    base_price = 100.0
    for i in range(100):
        candles.append({
            "open": base_price + i * 0.1,
            "high": base_price + i * 0.1 + 0.2,
            "low": base_price + i * 0.1 - 0.2,
            "close": base_price + i * 0.1 + 0.05,
            "volume": 1000 + i * 10,
        })
    state.market_current = {
        "candles": candles,
        "price": candles[-1]["close"],
        "high": max(c["high"] for c in candles),
        "low": min(c["low"] for c in candles),
        "open": candles[-1]["open"],
        "close": candles[-1]["close"],
    }
    # Common indicator fields
    state.indicators = {
        "rsi": 50.0,
        "volume": 1200.0,
        "fibonacci": {
            "0.0": 100.0,
            "23.6": 99.0,
            "38.2": 98.0,
            "50.0": 97.0,
            "61.8": 96.0,
            "78.6": 95.0,
            "100.0": 94.0,
        },
        "atr": 0.5,
        "macd": 0.0,
        "adx": 30.0,
        "supertrend": 99.5,
        "bollinger": {"upper": 101.0, "middle": 100.0, "lower": 99.0},
        "bb_width": 2.0,
        "vwap": 100.0,
    }
    # Other common state attributes
    state.mtf = {"score": 0, "bias": "NEUTRAL", "alignment": 0}
    state.structure = {}
    state.mss = {}
    state.smc = {}
    state.fvg = {}
    state.orderblock = {}
    state.orderflow = {}
    state.volumeprofile = {}
    state.session = {}
    state.regime = {}
    state.gann = {}
    state.equal_levels = {}
    state.premium_discount = {}
    state.wyckoff = {}
    state.liquidity = {}
    # Basic config
    state.symbol = "BTCUSDT"
    state.interval = "15m"
    state.mode = "SWING"

def validate_schema(block: EvidenceBlock) -> bool:
    """Check an EvidenceBlock against ADR-002 canonical schema."""
    required_fields = {
        'engine': str,
        'signal': str,
        'confidence_raw': float,
        'confidence_calibrated': float,
        'sub_evidence': list,
        'lifecycle_state': str,
        'timestamp': float,
    }
    for field, expected_type in required_fields.items():
        if not hasattr(block, field):
            return False
        if not isinstance(getattr(block, field), expected_type):
            return False

    # Semantic checks
    if block.lifecycle_state != "DETECTED":
        return False
    if not (0.0 <= block.confidence_raw <= 1.0):
        return False
    if not (0.0 <= block.confidence_calibrated <= 1.0):
        return False
    if not isinstance(block.sub_evidence, list):
        return False
    return True

def run_blackboard_audit():
    print("Running blackboard audit...\n")

    # Fresh state with new blackboard
    state = JaguarState()
    state.blackboard = MarketBlackboard()
    populate_minimal_state(state)

    # Run pipeline with this state (bus can be None for audit)
    analyze(state.symbol, state.interval, state=state, bus=None)

    blocks = state.blackboard.get_all()

    print("\nEvidenceBlock engines:")
    for block in blocks:
        print(" -", block.engine)

    # Build map engine -> list of blocks
    engine_blocks = {}

    for block in blocks:
        canonical = ENGINE_NAME_MAP.get(block.engine, block.engine)
        engine_blocks.setdefault(canonical, []).append(block)

    # Get registered engine names
    registry = EngineRegistry()
    register(registry)
    registered_engines = set(registry.get_engine_names())
    evidence_engines = registered_engines - NON_EVIDENCE_ENGINES

    results = {}
    duplicates = 0
    missing = []
    schema_errors = 0
    empty_evidence = 0
    invalid_signals = 0

    for registry_name in sorted(evidence_engines):

        engine_name = ENGINE_NAME_MAP.get(
            registry_name,
            registry_name
        )

        blist = engine_blocks.get(engine_name, [])

        if not blist:
            missing.append(registry_name)
            results[registry_name] = "MISSING"
        elif len(blist) > 1:
            duplicates += len(blist) - 1
            results[registry_name] = "DUPLICATE"
        else:
            block = blist[0]
            if not validate_schema(block):
                schema_errors += 1
                results[registry_name] = "SCHEMA_ERROR"
            elif not block.sub_evidence:
                empty_evidence += 1
                results[registry_name] = "EMPTY_EVIDENCE"
            elif block.confidence_raw == 0.0 and block.lifecycle_state == 'DETECTED':
                invalid_signals += 1
                results[registry_name] = "INVALID_SIGNAL"
            else:
                results[registry_name] = "PASS"

    # Print report
    print('=' * 40)
    print('BLACKBOARD AUDIT')
    print('=' * 40)
    for name in sorted(evidence_engines):
        status = results.get(name, 'UNKNOWN')
        print(f'{name:20} ..... {status}')
    print('-' * 40)
    print(f'Registered Engines : {len(registered_engines)}')
    print(f'Infrastructure Engines : {len(NON_EVIDENCE_ENGINES)}')
    print(f'Evidence Engines : {len(evidence_engines)}')
    print(f'EvidenceBlocks : {len(blocks)}')
    print(f'Duplicates : {duplicates}')
    print(f'Missing : {len(missing)}')
    print(f'Schema Errors : {schema_errors}')
    print(f'Empty Evidence : {empty_evidence}')
    print(f'Invalid Signals: {invalid_signals}')
    print('=' * 40)

    if (
        duplicates == 0
        and not missing
        and schema_errors == 0
        and empty_evidence == 0
        and invalid_signals == 0
    ):
        print("BLACKBOARD STATUS : PASS")
    else:
        print("BLACKBOARD STATUS : FAIL")
