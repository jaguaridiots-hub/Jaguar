from types import SimpleNamespace

from engine.trade_manager import TradeManager


def state(price, atr=2.0):
    return SimpleNamespace(
        price=float(price),
        atr=float(atr),
    )


def run_long():
    manager = TradeManager()
    manager.activate()

    plan = {
        "Direction": "BUY",
        "Entry": 100.0,
        "StopLoss": 95.0,
        "TP1": 105.0,
        "TP2": 110.0,
        "TP3": 115.0,
    }

    # Initial HOLD.
    result = manager.manage(
        state(102.0),
        plan,
        current_stop=95.0,
    )

    assert result["Action"] == "HOLD"
    assert result["StopLoss"] == 95.0
    assert manager.tp1_hit is False
    assert manager.tp2_hit is False

    print("R56_POS24_LONG_INITIAL: PASS")

    # TP1 -> break-even.
    result = manager.manage(
        state(105.0),
        plan,
        current_stop=95.0,
    )

    assert result["Action"] == "BOOK 30%"
    assert result["StopLoss"] == 100.0
    assert manager.tp1_hit is True
    assert manager.break_even is True
    assert manager.tp2_hit is False
    assert manager.trailing is False

    print("R56_POS24_LONG_TP1_BREAK_EVEN: PASS")

    # TP2 -> trailing.
    result = manager.manage(
        state(110.0),
        plan,
        current_stop=100.0,
    )

    assert result["Action"] == "BOOK 30%"
    assert manager.tp1_hit is True
    assert manager.tp2_hit is True
    assert manager.break_even is True
    assert manager.trailing is True
    assert result["StopLoss"] == 108.0

    # Critical fact:
    # current stop is now above TP1.
    assert result["StopLoss"] > plan["TP1"]

    print("R56_POS24_LONG_TP2_TRAILING_ABOVE_TP1: PASS")

    # Trailing stop only moves forward.
    result = manager.manage(
        state(112.0),
        plan,
        current_stop=108.0,
    )

    assert result["Action"] == "HOLD"
    assert result["StopLoss"] == 110.0

    print("R56_POS24_LONG_TRAILING_ADVANCE: PASS")

    # A lower candidate must not move the stop backward.
    result = manager.manage(
        state(111.0),
        plan,
        current_stop=110.0,
    )

    assert result["StopLoss"] == 110.0

    print("R56_POS24_LONG_TRAILING_NON_REGRESSION: PASS")

    # TP3 is terminal.
    result = manager.manage(
        state(115.0),
        plan,
        current_stop=110.0,
    )

    assert result["Action"] == "EXIT"
    assert manager.trade_closed is True
    assert manager.position_open is False

    print("R56_POS24_LONG_TERMINAL: PASS")


def run_short():
    manager = TradeManager()
    manager.activate()

    plan = {
        "Direction": "SELL",
        "Entry": 100.0,
        "StopLoss": 105.0,
        "TP1": 95.0,
        "TP2": 90.0,
        "TP3": 85.0,
    }

    result = manager.manage(
        state(98.0),
        plan,
        current_stop=105.0,
    )

    assert result["Action"] == "HOLD"
    assert result["StopLoss"] == 105.0
    assert manager.tp1_hit is False
    assert manager.tp2_hit is False

    print("R56_POS24_SHORT_INITIAL: PASS")

    result = manager.manage(
        state(95.0),
        plan,
        current_stop=105.0,
    )

    assert result["Action"] == "BOOK 30%"
    assert result["StopLoss"] == 100.0
    assert manager.tp1_hit is True
    assert manager.break_even is True

    print("R56_POS24_SHORT_TP1_BREAK_EVEN: PASS")

    result = manager.manage(
        state(90.0),
        plan,
        current_stop=100.0,
    )

    assert result["Action"] == "BOOK 30%"
    assert manager.tp1_hit is True
    assert manager.tp2_hit is True
    assert manager.break_even is True
    assert manager.trailing is True
    assert result["StopLoss"] == 92.0

    # Critical fact:
    # current stop is now below TP1.
    assert result["StopLoss"] < plan["TP1"]

    print("R56_POS24_SHORT_TP2_TRAILING_BELOW_TP1: PASS")

    result = manager.manage(
        state(88.0),
        plan,
        current_stop=92.0,
    )

    assert result["Action"] == "HOLD"
    assert result["StopLoss"] == 90.0

    print("R56_POS24_SHORT_TRAILING_ADVANCE: PASS")

    # Lower stop remains tighter for SHORT; upward candidate
    # must not loosen the stop.
    result = manager.manage(
        state(89.0),
        plan,
        current_stop=90.0,
    )

    assert result["StopLoss"] == 90.0

    print("R56_POS24_SHORT_TRAILING_NON_REGRESSION: PASS")

    result = manager.manage(
        state(85.0),
        plan,
        current_stop=90.0,
    )

    assert result["Action"] == "EXIT"
    assert manager.trade_closed is True
    assert manager.position_open is False

    print("R56_POS24_SHORT_TERMINAL: PASS")


def run_current_stop_authority():
    manager = TradeManager()
    manager.activate()

    plan = {
        "Direction": "BUY",
        "Entry": 100.0,
        "StopLoss": 95.0,
        "TP1": 105.0,
        "TP2": 110.0,
        "TP3": 115.0,
    }

    # current_stop must be authoritative over plan StopLoss.
    result = manager.manage(
        state(103.0),
        plan,
        current_stop=99.0,
    )

    assert result["StopLoss"] == 99.0

    print("R56_POS24_CURRENT_STOP_AUTHORITY: PASS")


def main():
    run_long()
    run_short()
    run_current_stop_authority()

    print(
        "R56-POS-24_TRADE_MANAGER_BEHAVIOR: PASS"
    )


if __name__ == "__main__":
    main()
