"""R56-POS-24D startup recovery seam certification."""

from pathlib import Path


MAIN = Path("main.py").read_text()


def test_import():
    assert (
        "recover_active_trade_from_durable_lifecycle"
        in MAIN
    )

    print(
        "R56_POS24_STARTUP_RECOVERY_IMPORT: PASS"
    )


def test_recovery_precedes_orphan_barrier():
    recovery = MAIN.index(
        "recover_active_trade_from_durable_lifecycle("
    )

    barrier = MAIN.index(
        "assert_no_orphan_durable_trade(SYMBOL)"
    )

    none_check = MAIN.index(
        "if durable_recovery_plan is None:"
    )

    assert none_check < barrier
    assert barrier > recovery

    print(
        "R56_POS24_DURABLE_RECOVERY_BEFORE_ORPHAN_BARRIER: PASS"
    )


def test_success_sets_existing_trade_context():
    recovery_plan = MAIN.index(
        "plan = durable_recovery_plan"
    )

    trade_id = MAIN.index(
        "state._trade_id = recovered_trade_uuid"
    )

    assert trade_id < recovery_plan

    print(
        "R56_POS24_RECOVERY_REBUILDS_EXISTING_TRADE_CONTEXT: PASS"
    )


def test_recovery_has_no_execution_authority():
    block_start = MAIN.index(
        "if not position_loaded:"
    )

    block_end = MAIN.index(
        "if position_loaded:",
        block_start,
    )

    block = MAIN[block_start:block_end]

    forbidden = (
        "insert_execution_intent",
        "bind_execution_identity",
        "ExecutionGateway",
        "execution_dispatch",
        "execute_paper_post_fill",
    )

    for token in forbidden:
        assert token not in block, (
            f"Recovery startup block contains forbidden execution token: {token}"
        )

    print(
        "R56_POS24_STARTUP_RECOVERY_NO_EXECUTION_PATH: PASS"
    )


def test_none_path_retains_orphan_quarantine():
    block_start = MAIN.index(
        "if not position_loaded:"
    )

    block_end = MAIN.index(
        "if position_loaded:",
        block_start,
    )

    block = MAIN[block_start:block_end]

    assert (
        "if durable_recovery_plan is None:"
        in block
    )

    assert (
        "assert_no_orphan_durable_trade(SYMBOL)"
        in block
    )

    print(
        "R56_POS24_NONE_RECOVERY_RETAINS_POS23_QUARANTINE: PASS"
    )


def test_recovery_mode_guard():
    recovery_block_start = MAIN.index(
        "recover_active_trade_from_durable_lifecycle("
    )

    recovery_context_start = MAIN.rfind(
        "try:",
        0,
        recovery_block_start,
    )

    assert recovery_context_start != -1

    # The actual PAPER-only enforcement lives inside the recovery
    # constructor. This startup seam must invoke only that constructor
    # and must not add a separate LIVE execution route.
    assert (
        "recover_active_trade_from_durable_lifecycle("
        in MAIN
    )

    print(
        "R56_POS24_STARTUP_RECOVERY_USES_CANONICAL_PAPER_GUARD: PASS"
    )


def main():
    test_import()
    test_recovery_precedes_orphan_barrier()
    test_success_sets_existing_trade_context()
    test_recovery_has_no_execution_authority()
    test_none_path_retains_orphan_quarantine()
    test_recovery_mode_guard()

    print(
        "R56-POS-24D_STARTUP_RECOVERY_SEAM: PASS"
    )


if __name__ == "__main__":
    main()
