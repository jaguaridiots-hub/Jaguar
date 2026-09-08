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

from research.database import get_connection


FILE = os.environ.get("JAGUAR_STATE_PATH", "trade_state.json")

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


def _is_trade_open_in_db(trade_uuid):
    if not isinstance(trade_uuid, str) or not trade_uuid.strip():
        return False

    conn = None

    try:
        conn = get_connection()

        row = conn.execute(
            """
            SELECT close_time
            FROM trades
            WHERE uuid = ?
            LIMIT 1
            """,
            (trade_uuid,),
        ).fetchone()

        return row is not None and row["close_time"] is None

    except Exception:
        # FAIL-CLOSED: never restore local state when
        # database verification is unavailable.
        return False

    finally:
        if conn is not None:
            conn.close()


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

        if take_profit <= entry:
            return False

    elif position == "SHORT":

        if take_profit >= entry:
            return False

    else:

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

    position_size = _to_float(
        getattr(
            position,
            "position_size",
            0.0,
        )
    )

    initial_risk = _to_float(
        getattr(
            position,
            "initial_risk",
            0.0,
        )
    )

    trade_uuid = getattr(
        position,
        "trade_uuid",
        None,
    )

    # FAIL-CLOSED: active positions require a trade identity.
    if position_type in ("LONG", "SHORT"):
        if not isinstance(trade_uuid, str) or not trade_uuid.strip():
            return False



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

        "position_size": position_size,
        "initial_risk": initial_risk,
        "trade_uuid": trade_uuid,

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

    position_size = _to_float(
        data.get(
            "position_size"
        )
    )

    initial_risk = _to_float(
        data.get(
            "initial_risk"
        )
    )

    trade_uuid = data.get(
        "trade_uuid"
    )

    # FAIL-CLOSED: active restored positions require
    # a valid trade identity.
    if position_type in ("LONG", "SHORT"):
        if not isinstance(trade_uuid, str) or not trade_uuid.strip():
            clear()
            return False

        # FAIL-CLOSED: local state may only restore a trade
        # that still exists and remains open in the database.
        if not _is_trade_open_in_db(trade_uuid):
            clear()
            return False

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
    position.position_size = position_size
    position.initial_risk = initial_risk
    if position_type in ("LONG", "SHORT"):
        position.set_trade_uuid(trade_uuid)


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
