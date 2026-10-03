"""
============================================================
Jaguar Quant X Enterprise
============================================================

Module:
    Structural Comparison Diagnostic

Version:
    1.0

Owner:
    Core Architecture / Diagnostics

Status:
    Diagnostic

Regression:
    Production behavior must not be modified.

Purpose:
    Compare the historical Liquidity structural pipeline
    against the canonical structure_snapshot() pipeline.

    The diagnostic identifies semantic differences in:

        - candle window selection
        - swing high detection
        - swing low detection
        - pivot indices
        - pivot prices
        - pivot available_index values

    This module is diagnostic only.

    It does not:

        - modify production engines
        - authorize trades
        - calculate PnL
        - update regression baselines
        - mutate Jaguar structural logic

============================================================
"""

import argparse
import csv
from pathlib import Path
from types import SimpleNamespace

from engine.structure_utils import (
    detect_swings,
    structure_snapshot,
)


# ==========================================================
# DEFAULT CONTRACT
# ==========================================================

DEFAULT_FIXTURE = Path(
    "backtest/fixtures/btcusdt_15m_300.csv"
)

DEFAULT_LOOKBACK = 80
DEFAULT_LEFT = 2
DEFAULT_RIGHT = 2

PRICE_EPSILON = 1e-9


# ==========================================================
# SAFE HELPERS
# ==========================================================

def _number(value, default=0.0):
    """
    Safely convert a value to float.
    """

    try:
        return float(value)

    except (TypeError, ValueError):
        return float(default)


def _integer(value, default=0):
    """
    Safely convert a value to int.
    """

    try:
        return int(value)

    except (TypeError, ValueError):
        return int(default)


def _dictionary(value):
    """
    Return a dictionary or an empty dictionary.
    """

    if isinstance(value, dict):
        return value

    return {}


# ==========================================================
# FIXTURE LOADER
# ==========================================================

def load_fixture(path):
    """
    Load an immutable Jaguar candle CSV fixture.
    """

    fixture_path = Path(path)

    if not fixture_path.exists():
        raise FileNotFoundError(
            "Fixture does not exist: "
            f"{fixture_path}"
        )

    required_fields = {
        "time",
        "close_time",
        "open",
        "high",
        "low",
        "close",
        "volume",
    }

    candles = []

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

        actual_fields = set(
            reader.fieldnames
        )

        missing_fields = sorted(
            required_fields
            - actual_fields
        )

        if missing_fields:
            raise RuntimeError(
                "Fixture missing required fields: "
                f"{missing_fields}"
            )

        for row_number, row in enumerate(
            reader,
            start=2,
        ):

            try:

                candle = {
                    "time": _integer(
                        row["time"]
                    ),
                    "close_time": _integer(
                        row["close_time"]
                    ),
                    "open": _number(
                        row["open"]
                    ),
                    "high": _number(
                        row["high"]
                    ),
                    "low": _number(
                        row["low"]
                    ),
                    "close": _number(
                        row["close"]
                    ),
                    "volume": _number(
                        row["volume"]
                    ),
                }

            except KeyError as exc:

                raise RuntimeError(
                    "Fixture field missing at "
                    f"row {row_number}: "
                    f"{exc}"
                ) from exc

            candles.append(
                candle
            )

    if not candles:
        raise RuntimeError(
            "Fixture is empty"
        )

    return candles


# ==========================================================
# DIAGNOSTIC STATE
# ==========================================================

def build_state(candles):
    """
    Build the minimal state contract required by
    engine.structure_utils.get_candles().
    """

    return SimpleNamespace(
        candles=candles,
        market_data=candles,
        klines=candles,
    )


# ==========================================================
# PIVOT NORMALIZATION
# ==========================================================

def _pivot_identity(pivot):
    """
    Build a stable diagnostic identity for one pivot.

    Index is intentionally part of the identity because
    Liquidity temporal eligibility depends on local indices.
    """

    pivot = _dictionary(
        pivot
    )

    return (
        pivot.get("index"),
        pivot.get("price"),
        pivot.get("available_index"),
    )


def _pivot_map(pivots):
    """
    Map pivot index to pivot data.
    """

    result = {}

    for pivot in pivots:

        pivot = _dictionary(
            pivot
        )

        index = pivot.get(
            "index"
        )

        if index is None:
            continue

        result[index] = pivot

    return result


# ==========================================================
# PIVOT COMPARISON
# ==========================================================

def compare_pivots(
    label,
    liquidity_pivots,
    snapshot_pivots,
):
    """
    Compare two pivot collections.
    """

    liquidity_map = _pivot_map(
        liquidity_pivots
    )

    snapshot_map = _pivot_map(
        snapshot_pivots
    )

    liquidity_indices = set(
        liquidity_map
    )

    snapshot_indices = set(
        snapshot_map
    )

    only_liquidity = sorted(
        liquidity_indices
        - snapshot_indices
    )

    only_snapshot = sorted(
        snapshot_indices
        - liquidity_indices
    )

    shared_indices = sorted(
        liquidity_indices
        & snapshot_indices
    )

    price_differences = []

    available_index_differences = []

    for index in shared_indices:

        liquidity_pivot = liquidity_map[
            index
        ]

        snapshot_pivot = snapshot_map[
            index
        ]

        liquidity_price = _number(
            liquidity_pivot.get("price")
        )

        snapshot_price = _number(
            snapshot_pivot.get("price")
        )

        if abs(
            liquidity_price
            - snapshot_price
        ) > PRICE_EPSILON:

            price_differences.append(
                {
                    "index": index,
                    "liquidity": liquidity_price,
                    "snapshot": snapshot_price,
                }
            )

        liquidity_available = (
            liquidity_pivot.get(
                "available_index"
            )
        )

        snapshot_available = (
            snapshot_pivot.get(
                "available_index"
            )
        )

        if (
            liquidity_available
            != snapshot_available
        ):

            available_index_differences.append(
                {
                    "index": index,
                    "liquidity":
                        liquidity_available,
                    "snapshot":
                        snapshot_available,
                }
            )

    exact_match = (
        len(liquidity_pivots)
        == len(snapshot_pivots)
        and not only_liquidity
        and not only_snapshot
        and not price_differences
        and not available_index_differences
        and [
            _pivot_identity(pivot)
            for pivot in liquidity_pivots
        ]
        == [
            _pivot_identity(pivot)
            for pivot in snapshot_pivots
        ]
    )

    return {
        "label": label,
        "liquidity_count":
            len(liquidity_pivots),
        "snapshot_count":
            len(snapshot_pivots),
        "only_liquidity":
            only_liquidity,
        "only_snapshot":
            only_snapshot,
        "price_differences":
            price_differences,
        "available_index_differences":
            available_index_differences,
        "exact_match":
            exact_match,
    }


# ==========================================================
# REPORTING
# ==========================================================

def _print_difference_list(
    label,
    values,
    limit=20,
):
    """
    Print a bounded diagnostic list.
    """

    print(
        f"{label:<32}: "
        f"{len(values)}"
    )

    if not values:
        return

    for value in values[:limit]:

        print(
            "    ",
            value,
        )

    remaining = (
        len(values)
        - limit
    )

    if remaining > 0:

        print(
            "    ... "
            f"{remaining} more"
        )


def print_comparison(result):
    """
    Print one pivot comparison report.
    """

    print()
    print(
        "=" * 100
    )

    print(
        result["label"]
    )

    print(
        "=" * 100
    )

    print(
        "Liquidity pivot count          :",
        result["liquidity_count"],
    )

    print(
        "Snapshot pivot count           :",
        result["snapshot_count"],
    )

    _print_difference_list(
        "Only Liquidity indices",
        result["only_liquidity"],
    )

    _print_difference_list(
        "Only Snapshot indices",
        result["only_snapshot"],
    )

    _print_difference_list(
        "Price differences",
        result["price_differences"],
    )

    _print_difference_list(
        "Available-index differences",
        result[
            "available_index_differences"
        ],
    )

    print(
        "Exact pivot identity           :",
        (
            "MATCH"
            if result["exact_match"]
            else "MISMATCH"
        ),
    )


# ==========================================================
# DIAGNOSTIC
# ==========================================================

def run_diagnostic(
    fixture,
    lookback,
    left,
    right,
):
    """
    Execute structural comparison.
    """

    candles = load_fixture(
        fixture
    )

    state = build_state(
        candles
    )

    # ======================================================
    # HISTORICAL LIQUIDITY PIPELINE
    # ======================================================
    #
    # Liquidity first created a local candle window.
    # detect_swings() therefore emitted LOCAL pivot indices.
    # ======================================================

    liquidity_window = candles[
        -min(
            lookback,
            len(candles),
        ):
    ]

    liquidity_swings = detect_swings(
        liquidity_window,
        left=left,
        right=right,
    )

    # ======================================================
    # STRUCTURAL CORE PIPELINE
    # ======================================================
    #
    # structure_snapshot() passes the full candle collection
    # to detect_swings() and applies lookback inside the
    # structural detector.
    #
    # This may preserve GLOBAL candle indices.
    # ======================================================

    snapshot = structure_snapshot(
        state,
        left=left,
        right=right,
        lookback=lookback,
    )

    snapshot_swings = snapshot[
        "swings"
    ]

    window_offset = (
        len(candles)
        - len(liquidity_window)
    )

    normalized_snapshot_swings = {
        "highs": [
            {
                **pivot,
                "index": (
                    pivot["index"]
                    - window_offset
                ),
                "available_index": (
                    pivot["available_index"]
                    - window_offset
                    if pivot.get(
                        "available_index"
                    ) is not None
                    else None
                ),
            }
            for pivot in snapshot_swings["highs"]
        ],
        "lows": [
            {
                **pivot,
                "index": (
                    pivot["index"]
                    - window_offset
                ),
                "available_index": (
                    pivot["available_index"]
                    - window_offset
                    if pivot.get(
                        "available_index"
                    ) is not None
                    else None
                ),
            }
            for pivot in snapshot_swings["lows"]
        ],
    }

    print(
        "=" * 100
    )

    print(
        "JAGUAR QUANT X - STRUCTURAL PIPELINE COMPARISON"
    )

    print(
        "=" * 100
    )

    print(
        "Fixture                     :",
        Path(fixture).resolve(),
    )

    print(
        "Total candles                :",
        len(candles),
    )

    print(
        "Lookback                     :",
        lookback,
    )

    print(
        "Swing left                   :",
        left,
    )

    print(
        "Swing right                  :",
        right,
    )

    print(
        "Liquidity window candles     :",
        len(liquidity_window),
    )

    print(
        "Snapshot candle count        :",
        len(
            snapshot["candles"]
        ),
    )

    print(
        "Window coordinate offset     :",
        window_offset,
    )

    print(
        "=" * 100
    )

    high_result = compare_pivots(
        "SWING HIGH COMPARISON",
        liquidity_swings["highs"],
        snapshot_swings["highs"],
    )

    low_result = compare_pivots(
        "SWING LOW COMPARISON",
        liquidity_swings["lows"],
        snapshot_swings["lows"],
    )

    print_comparison(
        high_result
    )

    print_comparison(
        low_result
    )

    normalized_high_result = compare_pivots(
        "NORMALIZED SWING HIGH COMPARISON",
        liquidity_swings["highs"],
        normalized_snapshot_swings["highs"],
    )

    normalized_low_result = compare_pivots(
        "NORMALIZED SWING LOW COMPARISON",
        liquidity_swings["lows"],
        normalized_snapshot_swings["lows"],
    )

    print_comparison(
        normalized_high_result
    )

    print_comparison(
        normalized_low_result
    )

    overall_match = (
        high_result["exact_match"]
        and low_result["exact_match"]
    )

    normalized_match = (
        normalized_high_result["exact_match"]
        and normalized_low_result["exact_match"]
    )

    print()
    print(
        "=" * 100
    )

    print(
        "DIAGNOSTIC CLASSIFICATION"
    )

    print(
        "=" * 100
    )

    print(
        "Swing highs match            :",
        high_result["exact_match"],
    )

    print(
        "Swing lows match             :",
        low_result["exact_match"],
    )

    print(
        "Overall structural identity  :",
        (
            "MATCH"
            if overall_match
            else "MISMATCH"
        ),
    )

    print(
        "Normalized structural identity:",
        (
            "MATCH"
            if normalized_match
            else "MISMATCH"
        ),
    )

    if overall_match:

        classification = (
            "STRUCTURAL_PIPELINES_IDENTICAL"
        )

    elif normalized_match:

        classification = (
            "COORDINATE_SPACE_ONLY_DIFFERENCE"
        )

    else:

        classification = (
            "STRUCTURAL_PIPELINES_DIFFER"
        )

    print(
        "Classification               :",
        classification,
    )

    print(
        "=" * 100
    )

    return (
        0
        if (
            overall_match
            or normalized_match
        )
        else 1
    )


# ==========================================================
# CLI
# ==========================================================

def parse_arguments():
    """
    Parse command-line arguments.
    """

    parser = argparse.ArgumentParser(
        description=(
            "Compare the historical Liquidity swing "
            "pipeline against Jaguar Structural Core."
        )
    )

    parser.add_argument(
        "--fixture",
        default=str(
            DEFAULT_FIXTURE
        ),
        help=(
            "Path to immutable candle fixture."
        ),
    )

    parser.add_argument(
        "--lookback",
        type=int,
        default=DEFAULT_LOOKBACK,
        help=(
            "Structural lookback."
        ),
    )

    parser.add_argument(
        "--left",
        type=int,
        default=DEFAULT_LEFT,
        help=(
            "Swing-left confirmation width."
        ),
    )

    parser.add_argument(
        "--right",
        type=int,
        default=DEFAULT_RIGHT,
        help=(
            "Swing-right confirmation width."
        ),
    )

    return parser.parse_args()


# ==========================================================
# ENTRY POINT
# ==========================================================

def main():
    """
    Diagnostic entry point.
    """

    arguments = parse_arguments()

    return run_diagnostic(
        fixture=arguments.fixture,
        lookback=arguments.lookback,
        left=arguments.left,
        right=arguments.right,
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
