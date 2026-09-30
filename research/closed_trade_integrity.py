import hashlib
import json
import math


_REQUIRED_SNAPSHOT_FIELDS = {
    "exit_price",
    "pnl",
    "r_multiple",
    "win_loss",
    "holding_time",
    "timestamp",
}


def _same_number(left, right):
    try:
        left = float(left)
        right = float(right)
    except (TypeError, ValueError):
        return False

    if not math.isfinite(left) or not math.isfinite(right):
        return False

    return math.isclose(
        left,
        right,
        rel_tol=0.0,
        abs_tol=1e-8,
    )


def _normalize_win_loss(value):
    if isinstance(value, bool):
        return int(value)

    try:
        numeric = int(value)
    except (TypeError, ValueError):
        return None

    if numeric not in (0, 1):
        return None

    return numeric


def validate_closed_trade_record(record):
    """
    Validate the durable terminal close snapshot against the
    top-level closed-trade columns.

    The snapshot checksum proves snapshot authenticity.
    Equality checks prove the top-level terminal fields cannot
    silently diverge from that authenticated snapshot.
    """
    if record is None:
        raise RuntimeError(
            "FAIL-CLOSED: Closed trade record is missing"
        )

    row = dict(record)

    if str(row.get("status", "")).strip().upper() != "CLOSED":
        raise RuntimeError(
            "FAIL-CLOSED: Closed trade status mismatch"
        )

    raw_snapshot = row.get("snapshot_close")
    stored_checksum = row.get("snapshot_close_checksum")

    if (
        not isinstance(raw_snapshot, str)
        or not raw_snapshot.strip()
        or not isinstance(stored_checksum, str)
        or not stored_checksum.strip()
    ):
        raise RuntimeError(
            "FAIL-CLOSED: Closed trade snapshot/fingerprint missing"
        )

    try:
        snapshot = json.loads(raw_snapshot)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(
            "FAIL-CLOSED: Closed trade snapshot is invalid"
        ) from exc

    if not isinstance(snapshot, dict):
        raise RuntimeError(
            "FAIL-CLOSED: Closed trade snapshot is not an object"
        )

    missing = _REQUIRED_SNAPSHOT_FIELDS - set(snapshot)
    if missing:
        raise RuntimeError(
            "FAIL-CLOSED: Closed trade snapshot fields missing: "
            f"{sorted(missing)}"
        )

    expected_checksum = hashlib.sha256(
        json.dumps(
            snapshot,
            sort_keys=True,
        ).encode()
    ).hexdigest()

    if stored_checksum != expected_checksum:
        raise RuntimeError(
            "FAIL-CLOSED: Closed trade snapshot checksum mismatch"
        )

    top_win_loss = _normalize_win_loss(row.get("win_loss"))
    snapshot_win_loss = _normalize_win_loss(snapshot.get("win_loss"))

    if top_win_loss is None or snapshot_win_loss is None:
        raise RuntimeError(
            "FAIL-CLOSED: Closed trade win_loss is invalid"
        )

    if top_win_loss != snapshot_win_loss:
        raise RuntimeError(
            "FAIL-CLOSED: Closed trade win_loss conflicts with snapshot"
        )

    if not _same_number(row.get("exit_price"), snapshot["exit_price"]):
        raise RuntimeError(
            "FAIL-CLOSED: Closed trade exit_price conflicts with snapshot"
        )

    if not _same_number(row.get("pnl"), snapshot["pnl"]):
        raise RuntimeError(
            "FAIL-CLOSED: Closed trade pnl conflicts with snapshot"
        )

    if not _same_number(row.get("r_multiple"), snapshot["r_multiple"]):
        raise RuntimeError(
            "FAIL-CLOSED: Closed trade r_multiple conflicts with snapshot"
        )

    try:
        top_holding_time = int(row.get("holding_time"))
        snapshot_holding_time = int(snapshot["holding_time"])
    except (TypeError, ValueError) as exc:
        raise RuntimeError(
            "FAIL-CLOSED: Closed trade holding_time is invalid"
        ) from exc

    if top_holding_time != snapshot_holding_time:
        raise RuntimeError(
            "FAIL-CLOSED: Closed trade holding_time conflicts with snapshot"
        )

    if row.get("close_time") != snapshot["timestamp"]:
        raise RuntimeError(
            "FAIL-CLOSED: Closed trade close_time conflicts with snapshot"
        )

    return row
