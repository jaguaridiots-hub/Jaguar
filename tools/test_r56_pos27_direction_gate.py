from types import SimpleNamespace

import intelligence.paper_post_fill as pp
from engine.position_manager import PositionManager


def run_invalid_direction_case(direction):
    position = PositionManager()

    state = SimpleNamespace(
        execution={},
        _trade_id=None,
        run_id="R56-POS27",
        _candle_time=None,
    )

    mutation = {"open": 0}

    original_open_trade = position.open_trade

    def guarded_open_trade(*args, **kwargs):
        mutation["open"] += 1
        return original_open_trade(*args, **kwargs)

    position.open_trade = guarded_open_trade

    try:
        pp.execute_paper_post_fill(
            execution=None,
            execution_result=None,
            authorization_id="AUTH-R56-POS27",
            trade_uuid="TRADE-R56-POS27",
            authorized_stop=90.0,
            authorized_targets=[110.0, 120.0, 130.0],
            direction=direction,
            state=state,
            position=position,
            manager=None,
            journal=None,
            plan=None,
            rollback_execution_if_pre_submission=None,
            preserve_trade_for_recovery=None,
            SYMBOL="BTCUSDT",
            TIMEFRAME="15m",
        )
    except RuntimeError as exc:
        assert str(exc) == (
            "FAIL-CLOSED: Invalid PAPER execution direction"
        )
    else:
        raise AssertionError(
            f"Invalid direction accepted: {direction!r}"
        )

    assert position.position == "NONE", (
        f"Position mutated for invalid direction {direction!r}"
    )
    assert mutation["open"] == 0, (
        f"open_trade() was reached for invalid direction {direction!r}"
    )
    assert state._trade_id is None

    return True


def main():
    invalid_directions = (
        "BUY_TRAP",
        "SELL_TRAP",
        "BUY anything",
        "SELL anything",
        "",
        "UNKNOWN",
        "LONG",
        "SHORT",
    )

    for direction in invalid_directions:
        run_invalid_direction_case(direction)
        label = direction.replace(" ", "_").upper()
        print(
            f"R56_POS27_INVALID_DIRECTION_{label}: PASS"
        )

    source = open(
        "intelligence/paper_post_fill.py",
        "r",
        encoding="utf-8",
    ).read()

    assert "if normalized_direction == 'BUY':" in source
    assert "elif normalized_direction == 'SELL':" in source
    assert "if 'BUY' in direction:" not in source
    assert "elif 'SELL' in direction:" not in source

    print("R56_POS27_EXACT_DIRECTION_BRANCHES: PASS")
    print("R56-POS-27_DIRECTION_GATE_TEST: PASS")


if __name__ == "__main__":
    main()
