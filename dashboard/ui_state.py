"""
Jaguar Quant X — canonical read-only UI state adapter.

This module does not make trading decisions.
It only translates the existing canonical Jaguar state into
a stable presentation contract for dashboards and APIs.
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any


def _mapping(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def build_ui_state(state: Any) -> dict:
    """
    Build a read-only presentation snapshot from canonical Jaguar state.

    Authority order:
        canonical enterprise IDM
        canonical enterprise risk
        canonical enterprise execution

    Legacy/compatibility fields are used only when necessary for display.
    """

    institutional = _mapping(
        getattr(state, "institutional_report", None)
    )

    enterprise = _mapping(
        institutional.get("enterprise")
    )

    master = _mapping(
        getattr(state, "master_decision", None)
    )

    components = _mapping(
        master.get("components")
    )

    structural = _mapping(
        components.get("structural_zone")
    )

    execution_confirmation = _mapping(
        components.get("execution_confirmation")
    )

    structure = _mapping(
        getattr(state, "structure", None)
    )
    structure_bos = _mapping(
        structure.get("bos")
    )
    structure_choch = _mapping(
        structure.get("choch")
    )

    trade = _mapping(
        enterprise.get("trade")
    )

    risk = _mapping(
        enterprise.get("risk")
    )

    execution = _mapping(
        enterprise.get("execution")
    )

    # Master IDM is the canonical decision authority.
    decision = _text(
        master.get(
            "decision",
            enterprise.get("decision", "WAIT"),
        ),
        "WAIT",
    )

    # Canonical direction is primarily supplied by structural authority.
    direction = _text(
        structural.get(
            "direction",
            trade.get("direction", "NEUTRAL"),
        ),
        "NEUTRAL",
    )

    # Current market price is obtained from the canonical market container.
    market = _mapping(
        getattr(state, "market", None)
    )

    timeframe = getattr(state, "timeframe", None)
    if not timeframe:
        timeframe = getattr(state, "interval", "")

    market_tf = _mapping(
        market.get(timeframe)
    )

    candles = market_tf.get("candles", [])
    latest = candles[-1] if isinstance(candles, list) and candles else {}

    price = (
        latest.get("close")
        if isinstance(latest, dict)
        else None
    )

    if price is None:
        price = getattr(state, "close", 0.0)

    raw_reasons = master.get("reasons", [])
    if not isinstance(raw_reasons, list):
        raw_reasons = [str(raw_reasons)] if raw_reasons else []

    # IDM reasons and execution-gate reasons have different provenance.
    # Keep them separate rather than merging or rewriting them.
    decision_reasons = [
        str(reason).strip()
        for reason in raw_reasons
        if str(reason).strip()
    ]

    execution_reason = str(
        execution.get("reason", "")
    ).strip()

    generated_epoch = time.time()
    generated_at = datetime.now().astimezone()

    market_timestamp = None

    if isinstance(latest, dict):
        market_timestamp = (
            latest.get("timestamp")
            or latest.get("time")
            or latest.get("datetime")
        )

    raw_mtf = getattr(state, "mtf_indicators", None)
    if not isinstance(raw_mtf, dict):
        raw_mtf = {}

    mtf = {}
    for frame in ("15m", "1h", "4h", "1d"):
        data = raw_mtf.get(frame, {})
        if not isinstance(data, dict):
            data = {}

        ema = data.get("ema", {})
        rsi = data.get("rsi", {})
        volume = data.get("volume", {})
        atr = data.get("atr", {})
        vwap = data.get("vwap", {})

        if not isinstance(ema, dict):
            ema = {}
        if not isinstance(rsi, dict):
            rsi = {}
        if not isinstance(volume, dict):
            volume = {}
        if not isinstance(atr, dict):
            atr = {}
        if not isinstance(vwap, dict):
            vwap = {}

        mtf[frame] = {
            "trend": _text(ema.get("trend"), "UNDEFINED"),
            "rsi": rsi.get("value"),
            "rsi_signal": _text(rsi.get("signal"), "UNDEFINED"),
            "volume_signal": _text(volume.get("signal"), "UNDEFINED"),
            "atr": atr.get("value"),
            "atr_volatility": _text(atr.get("volatility"), "UNDEFINED"),
            "vwap_signal": _text(vwap.get("signal"), "UNDEFINED"),
        }

    return {
        "system": {
            "mode": "PAPER",
            "health": "HEALTHY",
        },

        "freshness": {
            "generated_at": generated_at.isoformat(
                timespec="seconds"
            ),
            "generated_epoch": generated_epoch,
            "market_timestamp": market_timestamp,
            "initial_status": "CURRENT",
        },

        "mtf": mtf,

        "market": {
            "symbol": _text(
                getattr(state, "symbol", ""),
            ),
            "timeframe": _text(timeframe),
            "price": _number(price),
            "status": "READY" if candles else "UNKNOWN",
        },

        "idm": {
            "decision": decision,
            "approved": bool(master.get("approved", False)),
            "direction": direction,
            "score": _number(
                master.get(
                    "score",
                    enterprise.get("score", 0.0),
                )
            ),
            "confidence": _number(
                master.get(
                    "confidence",
                    enterprise.get("confidence", 0.0),
                )
            ),
            "grade": _text(
                components.get(
                    "institutional_grade",
                    enterprise.get("grade", "F"),
                ),
                "F",
            ),
            "priority": _text(
                master.get("priority", "UNKNOWN"),
                "UNKNOWN",
            ),
            "structure": _text(
                structural.get("structure_state", "UNKNOWN"),
                "UNKNOWN",
            ),
            "zone": _text(
                structural.get("zone_type", "NONE"),
                "NONE",
            ),
            "zone_lifecycle": _text(
                structural.get("zone_lifecycle", "UNKNOWN"),
                "UNKNOWN",
            ),
            "location": _text(
                structural.get("location_quality", "UNKNOWN"),
                "UNKNOWN",
            ),
            "trigger": _text(
                structural.get("trigger_status", "NONE"),
                "NONE",
            ),
            "readiness": _text(
                structural.get("readiness", "UNKNOWN"),
                "UNKNOWN",
            ),
            "trigger_confirmed": bool(
                execution_confirmation.get("confirmed", False)
            ),
            "decision_reasons": decision_reasons,
        },

        "structure": {
            "trend": _text(
                structure.get("trend"),
                "UNDEFINED",
            ),
            "bos": _text(
                structure_bos.get("signal"),
                "NONE",
            ),
            "choch": _text(
                structure_choch.get("signal"),
                "NONE",
            ),
            "direction": _text(
                structural.get("direction"),
                "NEUTRAL",
            ),
            "state": _text(
                structural.get("structure_state"),
                "UNDEFINED",
            ),
            "readiness": _text(
                structural.get("readiness"),
                "UNDEFINED",
            ),
            "trigger": _text(
                structural.get("trigger_status"),
                "NONE",
            ),
            "zone_type": _text(
                structural.get("zone_type"),
                "NONE",
            ),
            "zone_direction": _text(
                structural.get("zone_direction"),
                "NONE",
            ),
            "zone_lifecycle": _text(
                structural.get("zone_lifecycle"),
                "NONE",
            ),
        },
        "risk": {
            "approved": bool(risk.get("approved", False)),
            "status": _text(
                risk.get("status", "UNKNOWN"),
                "UNKNOWN",
            ),
            "position_size": _number(
                risk.get("position_size", 0.0)
            ),
            "risk_percent": _number(
                risk.get("risk_percent", 0.0)
            ),
            "risk_amount": _number(
                risk.get("risk_amount", 0.0)
            ),
            "exposure": _number(
                risk.get("exposure", 0.0)
            ),
            "reason": _text(
                risk.get("reason", ""),
            ),
        },

        "execution": {
            "ready": bool(execution.get("ready", False)),
            "approved": bool(execution.get("approved", False)),
            "status": _text(
                execution.get("status", "WAIT"),
                "WAIT",
            ),
            "gate": _text(
                execution.get("gate", "IDM"),
                "IDM",
            ),
            "broker": _text(
                execution.get("broker", "Paper"),
                "Paper",
            ),
            "authorization_id": execution.get(
                "authorization_id"
            ),
            "reason": execution_reason,
        },

        "position": {
            "status": "NONE",
            "side": None,
            "quantity": 0.0,
        },

        "audit": {
            "run_id": getattr(state, "run_id", None),
            "decision_id": None,
            "timestamp": datetime.now().isoformat(
                timespec="seconds"
            ),
        },
    }
