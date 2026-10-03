import traceback
"""
Jaguar Quant X Enterprise
Temporal Structural Validator v1.0

Purpose:
Replay historical candles through the canonical production
institutional pipeline and prove temporal structural behavior.

This validator is diagnostic only.

It does not:
- authorize trades
- modify production engines
- calculate PnL
- replace the execution gateway
"""

import argparse
import csv
import io
from contextlib import redirect_stdout
from pathlib import Path

from core.kernel import JaguarKernel

from data.market_data import get_klines

from indicators.indicator_engine import (
    update_market_state,
)

from engine.institutional_master import (
    analyze as institutional_master,
)


# ============================================================
# SAFE HELPERS
# ============================================================

def _dictionary(value):

    if isinstance(value, dict):
        return value

    return {}


def _number(value, default=0.0):

    try:
        return float(value)

    except (TypeError, ValueError):
        return float(default)


def _value(value, default="NONE"):

    if value is None:
        return default

    return value


# ============================================================
# TEMPORAL VALIDATOR
# ============================================================

def load_candle_fixture(path):
    """
    Load an immutable CSV candle fixture.

    The returned candle contract mirrors
    data.market_data.get_klines().
    """

    fixture_path = Path(path)

    if not fixture_path.exists():

        raise FileNotFoundError(
            "Candle fixture does not exist: "
            f"{fixture_path}"
        )

    numeric_fields = {
        "time": int,
        "close_time": int,
        "open": float,
        "high": float,
        "low": float,
        "close": float,
        "volume": float,
    }

    with fixture_path.open(
        newline="",
    ) as handle:

        reader = csv.DictReader(
            handle
        )

        if reader.fieldnames is None:

            raise RuntimeError(
                "Fixture has no CSV header"
            )

        required_fields = set(
            numeric_fields
        )

        actual_fields = set(
            reader.fieldnames
        )

        missing = sorted(
            required_fields
            - actual_fields
        )

        if missing:

            raise RuntimeError(
                "Fixture missing candle fields: "
                f"{missing}"
            )

        candles = []

        for row_number, row in enumerate(
            reader,
            start=2,
        ):

            candle = {}

            for field, converter in (
                numeric_fields.items()
            ):

                raw_value = row.get(
                    field
                )

                if raw_value is None:

                    raise RuntimeError(
                        "Fixture field missing at "
                        f"row {row_number}: "
                        f"{field}"
                    )

                value = raw_value.strip()

                if not value:

                    raise RuntimeError(
                        "Fixture field empty at "
                        f"row {row_number}: "
                        f"{field}"
                    )

                try:

                    candle[field] = converter(
                        value
                    )

                except ValueError as exc:

                    raise RuntimeError(
                        "Invalid fixture value at "
                        f"row {row_number}, "
                        f"field {field}: "
                        f"{value!r}"
                    ) from exc

            candles.append(
                candle
            )

    if not candles:

        raise RuntimeError(
            "Candle fixture is empty"
        )

    previous_time = None

    for position, candle in enumerate(
        candles
    ):

        candle_time = candle[
            "time"
        ]

        if (
            previous_time is not None
            and candle_time <= previous_time
        ):

            raise RuntimeError(
                "Fixture candle time is not "
                "strictly increasing at "
                f"position {position}: "
                f"{candle_time} <= "
                f"{previous_time}"
            )

        previous_time = candle_time

    return candles


def run(
    symbol="BTCUSDT",
    timeframe="15m",
    warmup=220,
    output_path=None,
    fixture=None,
):

    if fixture is not None:

        candles = load_candle_fixture(
            fixture
        )

        data_source = (
            f"FIXTURE:{fixture}"
        )

    else:

        candles = get_klines(
            symbol=symbol,
            interval=timeframe,
        )

        data_source = (
            "LIVE:data.market_data."
            "get_klines"
        )

    if not isinstance(candles, list):

        raise RuntimeError(
            "Market data provider did not return a candle list"
        )

    if len(candles) <= warmup:

        raise RuntimeError(
            "Insufficient candles for temporal validation: "
            f"{len(candles)} <= warmup {warmup}"
        )

    # ========================================================
    # PRODUCTION-COMPATIBLE STATE
    #
    # IMPORTANT:
    # The same state object is reused for every replay cycle.
    #
    # This preserves canonical structural_memory.
    # ========================================================

    kernel = JaguarKernel()

    kernel.initialize(
        symbol,
        timeframe,
    )

    state = kernel.get_state()

    state.symbol = symbol

    state.timeframe = timeframe

    rows = []

    previous_snapshot = None

    print()
    print("=" * 100)
    print("JAGUAR QUANT X - TEMPORAL STRUCTURAL VALIDATOR")
    print("=" * 100)
    print("Symbol       :", symbol)
    print("Timeframe    :", timeframe)
    print("Candles      :", len(candles))
    print("Data Source  :", data_source)
    print("Warmup       :", warmup)
    print("Replay Cycles:", len(candles) - warmup)
    print("=" * 100)
    print()

    for current_index in range(
        warmup,
        len(candles),
    ):

        # Prefix includes current candle.
        #
        # This mirrors production analysis where the latest
        # closed candle is available to the engine.
        history = candles[
            : current_index + 1
        ]

        latest = history[-1]

        state.symbol = symbol

        state.timeframe = timeframe

        state.price = _number(
            latest.get(
                "close",
                0.0,
            )
        )

        state.volume = _number(
            latest.get(
                "volume",
                0.0,
            )
        )

        # Production indicator/state preparation.
        state = update_market_state(
            state,
            history,
        )

        # StructuralZoneEngine currently emits console
        # diagnostics. Suppress pipeline output so this
        # validator prints only temporal transitions.
        pipeline_output = io.StringIO()

        try:

            with redirect_stdout(
                pipeline_output
            ):

                institutional_master(
                    state
                )

        except Exception as exc:

            print(
                f"[ERROR] index={current_index} "
                f"{type(exc).__name__}: {exc}"
            )

            traceback.print_exc()

            continue

        structural_zone = _dictionary(
            getattr(
                state,
                "structural_zone",
                {},
            )
        )

        execution_trigger = _dictionary(
            structural_zone.get(
                "execution_trigger",
                {},
            )
        )

        snapshot = {
            "index":
                current_index,

            "price":
                state.price,

            "direction":
                structural_zone.get(
                    "direction",
                    "NEUTRAL",
                ),

            "structure_state":
                structural_zone.get(
                    "structure_state",
                    "UNDEFINED",
                ),

            "zone_status":
                structural_zone.get(
                    "zone_status",
                    "NONE",
                ),

            "zone_type":
                structural_zone.get(
                    "zone_type",
                    "NONE",
                ),

            "zone_direction":
                structural_zone.get(
                    "zone_direction",
                    "NEUTRAL",
                ),

            "zone_lifecycle":
                structural_zone.get(
                    "zone_lifecycle",
                    "UNKNOWN",
                ),

            "zone_low":
                structural_zone.get(
                    "zone_low",
                    0.0,
                ),

            "zone_high":
                structural_zone.get(
                    "zone_high",
                    0.0,
                ),

            "interacting":
                structural_zone.get(
                    "interacting",
                    False,
                ),

            "location_quality":
                structural_zone.get(
                    "location_quality",
                    "UNKNOWN",
                ),

            "trigger_status":
                execution_trigger.get(
                    "status",
                    "NONE",
                ),

            "trigger_source":
                execution_trigger.get(
                    "source",
                    "NONE",
                ),

            "trigger_direction":
                execution_trigger.get(
                    "direction",
                    "NEUTRAL",
                ),

            "trigger_lifecycle":
                execution_trigger.get(
                    "lifecycle",
                    "UNKNOWN",
                ),

            "trigger_age":
                execution_trigger.get(
                    "trigger_age"
                ),

            "trigger_freshness":
                execution_trigger.get(
                    "freshness",
                    "UNKNOWN",
                ),

            "trigger_fresh":
                execution_trigger.get(
                    "fresh",
                    False,
                ),

            "location_valid":
                execution_trigger.get(
                    "location_valid",
                    False,
                ),

            "selected_zone_match":
                execution_trigger.get(
                    "selected_zone_match",
                    False,
                ),

            "readiness":
                structural_zone.get(
                    "readiness",
                    "WAITING",
                ),
        }

        rows.append(
            snapshot
        )

        transition_key = (
            snapshot[
                "direction"
            ],
            snapshot[
                "structure_state"
            ],
            snapshot[
                "zone_type"
            ],
            snapshot[
                "zone_lifecycle"
            ],
            snapshot[
                "interacting"
            ],
            snapshot[
                "trigger_status"
            ],
            snapshot[
                "trigger_source"
            ],
            snapshot[
                "trigger_direction"
            ],
            snapshot[
                "trigger_age"
            ],
            snapshot[
                "trigger_freshness"
            ],
            snapshot[
                "trigger_fresh"
            ],
            snapshot[
                "location_valid"
            ],
            snapshot[
                "selected_zone_match"
            ],
            snapshot[
                "readiness"
            ],
        )

        if transition_key != previous_snapshot:

            print(
                f"[{current_index:>5}] "
                f"P={state.price:.4f} | "
                f"DIR={snapshot['direction']} | "
                f"STRUCT={snapshot['structure_state']} | "
                f"ZONE={snapshot['zone_type']}/"
                f"{snapshot['zone_lifecycle']} | "
                f"INT={snapshot['interacting']} | "
                f"TRIGGER={snapshot['trigger_status']}/"
                f"{snapshot['trigger_source']}/"
                f"{snapshot['trigger_direction']} | "
                f"AGE={_value(snapshot['trigger_age'])} | "
                f"FRESH={snapshot['trigger_freshness']} | "
                f"ELIG={snapshot['trigger_fresh']} | "
                f"LOC={snapshot['location_valid']} | "
                f"MATCH={snapshot['selected_zone_match']} | "
                f"READY={snapshot['readiness']}"
            )

            previous_snapshot = transition_key

    # ========================================================
    # SUMMARY
    # ========================================================

    confirmed = sum(
        1
        for row in rows
        if row[
            "trigger_status"
        ] == "CONFIRMED"
    )

    fresh = sum(
        1
        for row in rows
        if row[
            "trigger_freshness"
        ] == "FRESH"
    )

    aging = sum(
        1
        for row in rows
        if row[
            "trigger_freshness"
        ] == "AGING"
    )

    stale = sum(
        1
        for row in rows
        if row[
            "trigger_freshness"
        ] == "STALE"
    )

    location_valid = sum(
        1
        for row in rows
        if row[
            "location_valid"
        ]
    )

    ready = sum(
        1
        for row in rows
        if row[
            "readiness"
        ] in (
            "CONFIRMED",
            "TRIGGER_CONFIRMED",
        )
    )

    stale_readiness = sum(
        1
        for row in rows
        if row[
            "readiness"
        ] == "STALE_TRIGGER"
    )

    aging_readiness = sum(
        1
        for row in rows
        if row[
            "readiness"
        ] == "AGING_TRIGGER"
    )

    print()
    print("=" * 100)
    print("TEMPORAL VALIDATION SUMMARY")
    print("=" * 100)
    print("Successful cycles       :", len(rows))
    print("Confirmed triggers      :", confirmed)
    print("Fresh trigger cycles    :", fresh)
    print("Aging trigger cycles    :", aging)
    print("Stale trigger cycles    :", stale)
    print("Location-valid cycles   :", location_valid)
    print("Execution-ready cycles  :", ready)
    print("Aging readiness cycles  :", aging_readiness)
    print("Stale readiness cycles  :", stale_readiness)
    print("=" * 100)

    # ========================================================
    # CSV EVIDENCE
    # ========================================================

    if output_path is None:

        output_path = (
            "backtest/"
            "temporal_structural_validation.csv"
        )

    output = Path(
        output_path
    )

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if rows:

        with output.open(
            "w",
            newline="",
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=list(
                    rows[0].keys()
                ),
            )

            writer.writeheader()

            writer.writerows(
                rows
            )

    print()
    print(
        "CSV evidence:",
        output,
    )

    return rows


# ============================================================
# CLI
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=(
            "Jaguar temporal structural validator"
        )
    )

    parser.add_argument(
        "--symbol",
        default="BTCUSDT",
    )

    parser.add_argument(
        "--timeframe",
        default="15m",
    )

    parser.add_argument(
        "--warmup",
        type=int,
        default=220,
    )

    parser.add_argument(
        "--fixture",
        default=None,
        help=(
            "Immutable CSV candle fixture "
            "used instead of live market data"
        ),
    )

    parser.add_argument(
        "--output",
        default=(
            "backtest/"
            "temporal_structural_validation.csv"
        ),
    )

    args = parser.parse_args()

    run(
        symbol=args.symbol,
        timeframe=args.timeframe,
        warmup=args.warmup,
        output_path=args.output,
        fixture=args.fixture,
    )


if __name__ == "__main__":

    main()
