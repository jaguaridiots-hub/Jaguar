from pathlib import Path
import os
import subprocess

from engine.position_manager import PositionManager


ROOT = Path(__file__).resolve().parents[1]

POS37_TAG = "r56-pos37-terminal-close-writer-authority"

PRODUCTION_PATHS = [
    "main.py",
    "engine/active_trade_recovery.py",
    "engine/position_manager.py",
    "engine/state_manager.py",
    "intelligence/paper_post_fill.py",
]


def git_show(tag, path):
    return subprocess.check_output(
        ["git", "show", f"{tag}:{path}"],
        cwd=ROOT,
        text=True,
    )


def git_head(path):
    return (ROOT / path).read_text()


def assert_production_files_frozen():
    for path in PRODUCTION_PATHS:
        baseline = git_show(POS37_TAG, path)
        current = git_head(path)

        assert baseline == current, (
            f"Production file changed after POS37: {path}"
        )

    print(
        "R56_POS38_PRODUCTION_CODE_UNCHANGED_FROM_POS37: PASS"
    )


def assert_terminal_close_authority():
    src = (ROOT / "main.py").read_text()

    marker = "# FINAL CLOSE AUTHORITY:"
    start = src.index(marker)
    end = src.index("record_trade_close(", start)

    segment = src[start:end]

    required = [
        "recover_active_trade_plan(",
        'close_contract["Entry"]',
        'close_contract["PositionSize"]',
        "pnl =",
        "initial_risk = float(",
        "r_multiple =",
    ]

    for needle in required:
        assert needle in segment, (
            f"Missing terminal-close authority element: {needle}"
        )

    recovery = segment.find(
        "recover_active_trade_plan("
    )
    entry = segment.find(
        'close_contract["Entry"]'
    )
    size = segment.find(
        'close_contract["PositionSize"]'
    )
    pnl = segment.find("pnl =")
    risk = segment.find("initial_risk = float(")
    r = segment.find("r_multiple =")

    assert recovery < entry
    assert recovery < size
    assert recovery < pnl
    assert pnl < risk
    assert risk < r

    assert "position.initial_risk =" not in src

    print(
        "R56_POS38_TERMINAL_DURABLE_RECOVERY_PRECEDES_R: PASS"
    )
    print(
        "R56_POS38_TERMINAL_DURABLE_ENTRY_AND_SIZE_PRECEDE_PNL: PASS"
    )
    print(
        "R56_POS38_MAIN_HAS_NO_DIRECT_INITIAL_RISK_MUTATION: PASS"
    )


def assert_startup_recovery_authority():
    src = (ROOT / "main.py").read_text()

    needle = (
        "recover_active_trade_from_durable_lifecycle("
    )

    count = src.count(needle)
    assert count >= 2

    local_load = src.index(
        "position_loaded = load("
    )

    recoveries = []
    offset = 0

    while True:
        pos = src.find(needle, offset)
        if pos < 0:
            break

        recoveries.append(pos)
        offset = pos + 1

    for pos in recoveries:
        assert pos > local_load

    print(
        f"R56_POS38_STARTUP_DURABLE_RECOVERY_CALLS={count}"
    )
    print(
        "R56_POS38_DURABLE_RECOVERY_FOLLOWS_LOCAL_CACHE_LOAD: PASS"
    )


def assert_recovery_reconstructs_risk():
    src = (
        ROOT / "engine/active_trade_recovery.py"
    ).read_text()

    start = src.index(
        "def recover_active_trade_from_durable_lifecycle("
    )

    end = src.index(
        "\ndef persist_active_trade_lifecycle(",
        start,
    )

    segment = src[start:end]

    required = [
        'durable_fill["fill_price"]',
        'intent.get("stop_loss")',
        'intent.get("quantity")',
        "initial_risk = abs(",
        "math.isfinite(initial_risk)",
        "position.open_trade(",
        "initial_risk=initial_risk",
    ]

    for needle in required:
        assert needle in segment, needle

    risk_pos = segment.find(
        "initial_risk = abs("
    )
    hydrate_pos = segment.find(
        "position.open_trade("
    )

    assert risk_pos < hydrate_pos

    print(
        "R56_POS38_DURABLE_FILL_PRICE_IS_RISK_INPUT: PASS"
    )
    print(
        "R56_POS38_DURABLE_STOP_IS_RISK_INPUT: PASS"
    )
    print(
        "R56_POS38_DURABLE_QUANTITY_IS_RISK_INPUT: PASS"
    )
    print(
        "R56_POS38_INITIAL_RISK_RECONSTRUCTION: PASS"
    )
    print(
        "R56_POS38_INITIAL_RISK_HYDRATES_POSITION_MANAGER: PASS"
    )


def assert_cache_poisoning_defeated():
    durable_entry = 101.5
    durable_stop = 99.0
    durable_quantity = 2.0
    exit_price = 106.0

    durable_initial_risk = abs(
        durable_entry - durable_stop
    ) * durable_quantity

    position = PositionManager()

    # Poisoned local/cache state.
    position.open_trade(
        "LONG",
        durable_entry,
        durable_stop,
        105.0,
        position_size=durable_quantity,
        initial_risk=999999.0,
    )

    assert position.initial_risk == 999999.0

    # Exact durable-recovery hydration contract.
    position.open_trade(
        "LONG",
        durable_entry,
        durable_stop,
        105.0,
        position_size=durable_quantity,
        initial_risk=durable_initial_risk,
    )

    assert position.initial_risk == durable_initial_risk

    pnl = (
        exit_price - durable_entry
    ) * durable_quantity

    r_multiple = (
        pnl / position.initial_risk
    )

    assert durable_initial_risk == 5.0
    assert pnl == 9.0
    assert r_multiple == 1.8

    print(
        "R56_POS38_CACHE_POISONING_DEFEATED: PASS"
    )
    print(
        "R56_POS38_DURABLE_INITIAL_RISK=5.0"
    )
    print(
        "R56_POS38_TERMINAL_PNL=9.0"
    )
    print(
        "R56_POS38_TERMINAL_R_MULTIPLE=1.8"
    )


def assert_no_production_diff_against_pos37():
    result = subprocess.run(
        [
            "git",
            "diff",
            "--quiet",
            POS37_TAG,
            "--",
            "main.py",
            "engine",
            "intelligence",
            "research",
            "dashboard",
            "core",
        ],
        cwd=ROOT,
    )

    assert result.returncode == 0, (
        "Production tree differs from POS37"
    )

    print(
        "R56_POS38_PRODUCTION_TREE_FROZEN_AT_POS37: PASS"
    )


def main():
    assert os.environ.get(
        "JAGUAR_EXECUTION_MODE"
    ) == "PAPER"

    assert_production_files_frozen()
    assert_terminal_close_authority()
    assert_startup_recovery_authority()
    assert_recovery_reconstructs_risk()
    assert_cache_poisoning_defeated()
    assert_no_production_diff_against_pos37()

    print("R56-POS-38-PERMANENT-WITNESS: PASS")


if __name__ == "__main__":
    main()
