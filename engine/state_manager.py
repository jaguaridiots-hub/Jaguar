"""
Jaguar Quant X
Trade State Manager V2

Responsible for persistent position state.

The state manager never creates a trade.
It only stores, validates, restores, and clears
an existing position lifecycle.
"""

import json
import os
import time


FILE = "trade_state.json"

STATE_VERSION = 2


# ===================================================
# INTERNAL HELPERS
# ===================================================

def _to_float(value, default=0.0):

    try:

        if value is None:
            return default

        return float(value)

    except (TypeError, ValueError):

        return default


def _normalize_position(value):

    value = str(
        value or "NONE"
    ).upper().strip()

    if value not in [
        "LONG",
        "SHORT",
        "NONE",
    ]:

        return "NONE"

    return value


def _is_valid_trade(
    position,
    entry,
    stop_loss,
    take_profit,
):

    if position == "NONE":

        return False

    if entry <= 0:

        return False

    if stop_loss <= 0:

        return False

    if take_profit <= 0:

        return False


    if position == "LONG":

        if stop_loss >= entry:

            return False

        if take_profit <= entry:

            return False


    elif position == "SHORT":

        if stop_loss <= entry:

            return False

        if take_profit >= entry:

            return False


    return True


# ===================================================
# SAVE POSITION
# ===================================================

def save(
    position,
    symbol=None,
):

    position_type = _normalize_position(
        getattr(
            position,
            "position",
            "NONE",
        )
    )


    entry = _to_float(
        getattr(
            position,
            "entry",
            0.0,
        )
    )


    stop_loss = _to_float(
        getattr(
            position,
            "stop_loss",
            0.0,
        )
    )


    take_profit = _to_float(
        getattr(
            position,
            "take_profit",
            0.0,
        )
    )


    pnl = _to_float(
        getattr(
            position,
            "pnl",
            0.0,
        )
    )


    if not _is_valid_trade(
        position_type,
        entry,
        stop_loss,
        take_profit,
    ):

        return False


    data = {

        "version": STATE_VERSION,

        "symbol": str(
            symbol or ""
        ).upper(),

        "position": position_type,

        "entry": entry,

        "stop_loss": stop_loss,

        "take_profit": take_profit,

        "pnl": pnl,

        "updated_at": int(
            time.time()
        ),

    }


    temp_file = FILE + ".tmp"


    try:

        with open(
            temp_file,
            "w",
        ) as file:

            json.dump(
                data,
                file,
                indent=4,
            )


        os.replace(
            temp_file,
            FILE,
        )


        return True


    except (
        OSError,
        TypeError,
        ValueError,
    ):

        if os.path.exists(
            temp_file
        ):

            try:

                os.remove(
                    temp_file
                )

            except OSError:

                pass


        return False


# ===================================================
# LOAD POSITION
# ===================================================

def load(
    position,
    symbol=None,
):

    if not os.path.exists(
        FILE
    ):

        return False


    try:

        with open(
            FILE,
            "r",
        ) as file:

            data = json.load(
                file
            )


    except (
        OSError,
        json.JSONDecodeError,
    ):

        clear()

        return False


    if not isinstance(
        data,
        dict,
    ):

        clear()

        return False


    version = data.get(
        "version"
    )


    if version != STATE_VERSION:

        clear()

        return False


    saved_symbol = str(
        data.get(
            "symbol",
            "",
        )
    ).upper()


    expected_symbol = str(
        symbol or ""
    ).upper()


    if (
        expected_symbol
        and saved_symbol != expected_symbol
    ):

        clear()

        return False


    position_type = _normalize_position(
        data.get(
            "position"
        )
    )


    entry = _to_float(
        data.get(
            "entry"
        )
    )


    stop_loss = _to_float(
        data.get(
            "stop_loss"
        )
    )


    take_profit = _to_float(
        data.get(
            "take_profit"
        )
    )


    pnl = _to_float(
        data.get(
            "pnl"
        )
    )


    if not _is_valid_trade(
        position_type,
        entry,
        stop_loss,
        take_profit,
    ):

        clear()

        return False


    position.position = position_type

    position.entry = entry

    position.stop_loss = stop_loss

    position.take_profit = take_profit

    position.pnl = pnl


    return True


# ===================================================
# CLEAR POSITION STATE
# ===================================================

def clear():

    removed = False


    for file_path in [
        FILE,
        FILE + ".tmp",
    ]:

        if os.path.exists(
            file_path
        ):

            try:

                os.remove(
                    file_path
                )

                removed = True


            except OSError:

                pass


    return removed
