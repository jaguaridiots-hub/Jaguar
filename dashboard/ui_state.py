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


def _fibonacci_ui(value: Any) -> dict:
    """
    Read-only projection of the canonical Fibonacci engine result.

    The UI adapter must preserve canonical levels and metadata.
    It must not calculate, reinterpret, or rebuild Fibonacci levels.
    """
    data = _mapping(value)
    metadata = _mapping(data.get("metadata"))

    raw_retracements = _mapping(metadata.get("retracements"))
    raw_extensions = _mapping(metadata.get("extensions"))

    retracements = {
        str(k): v
        for k, v in raw_retracements.items()
    }

    extensions = {
        str(k): v
        for k, v in raw_extensions.items()
    }

    return {
        "name": _text(data.get("name"), "Fibonacci"),
        "signal": _text(data.get("signal"), "NEUTRAL"),
        "status": _text(metadata.get("status"), "UNKNOWN"),
        "zone": _text(metadata.get("zone"), "UNKNOWN"),
        "score": _number(data.get("score", 0.0)),
        "confidence": _number(data.get("confidence", 0.0)),
        "reasons": [
            str(reason).strip()
            for reason in data.get("reasons", [])
            if str(reason).strip()
        ] if isinstance(data.get("reasons"), list) else [],
        "metadata": {
            "lookback": metadata.get("lookback"),
            "candle_count": metadata.get("candle_count"),
            "price": metadata.get("price"),
            "swing_high": metadata.get("swing_high"),
            "swing_low": metadata.get("swing_low"),
            "range": metadata.get("range"),
            "retracements": retracements,
            "extensions": extensions,

            # Legacy compatibility fields remain available for
            # consumers that have not migrated to grouped levels.
            "extension127": metadata.get("extension127"),
            "extension161": metadata.get("extension161"),
            "extension261": metadata.get("extension261"),
            "fib236": metadata.get("fib236"),
            "fib382": metadata.get("fib382"),
            "fib500": metadata.get("fib500"),
            "fib618": metadata.get("fib618"),
            "fib786": metadata.get("fib786"),
        },
    }


def build_ui_state(state: Any, report: dict | None = None) -> dict:
    """
    Build a read-only presentation snapshot from canonical Jaguar state.

    Authority order:
        canonical enterprise IDM
        canonical enterprise risk
        canonical enterprise execution

    Legacy/compatibility fields are used only when necessary for display.
    """

    institutional = _mapping(
        report
        or getattr(state, "institutional_report", None)
    )

    enterprise = _mapping(
        institutional.get("enterprise")
    )

    master = _mapping(
        getattr(state, "idm", None)
        or getattr(state, "master_decision", None)
    )

    components = _mapping(
        master.get("components")
    )

    # Canonical structural authority.
    # The live canonical analysis path publishes structural state on
    # state.structural_zone. Preserve the older IDM structural contract
    # as a compatibility fallback for assistant/dashboard contract fixtures.
    canonical_structural = _mapping(
        getattr(state, "structural_zone", None)
    )

    legacy_structural = _mapping(
        master.get("structural")
        or components.get("structural_zone")
    )

    structural = canonical_structural or legacy_structural

    # Canonical execution-confirmation authority is published
    # directly on state as an EngineResult in the V3 analysis path.
    # Preserve compatibility with older component-based state.
    execution_confirmation_raw = getattr(
        state,
        "execution_confirmation",
        None,
    )

    if execution_confirmation_raw is None:
        execution_confirmation_raw = (
            components.get("execution_confirmation")
        )

    if hasattr(
        execution_confirmation_raw,
        "to_dict",
    ):
        execution_confirmation_raw = (
            execution_confirmation_raw.to_dict()
        )

    execution_confirmation = _mapping(
        execution_confirmation_raw
    )

    structure = _mapping(
        getattr(state, "structure", None)
    )

    # BOS/CHOCH authority comes from the canonical engine results.
    # trigger_status in structural_zone is an execution/structure-trigger
    # field and must not be used as a substitute for BOS/CHOCH engine output.
    engines = _mapping(
        report.get("engines") if isinstance(report, dict) else None
    )

    bos_engine = _mapping(engines.get("BOS"))
    choch_engine = _mapping(engines.get("CHOCH"))

    bos_signal = _text(
        bos_engine.get("signal"),
        "NEUTRAL",
    )
    choch_signal = _text(
        choch_engine.get("signal"),
        "NEUTRAL",
    )

    bos_reasons = _mapping(engines.get("BOS")).get(
        "reasons",
        [],
    )
    choch_reasons = _mapping(engines.get("CHOCH")).get(
        "reasons",
        [],
    )

    if not isinstance(bos_reasons, list):
        bos_reasons = []

    if not isinstance(choch_reasons, list):
        choch_reasons = []

    structure_bos = {
        "signal": bos_signal,
        "reasons": bos_reasons,
    }

    structure_choch = {
        "signal": choch_signal,
        "reasons": choch_reasons,
    }

    trade = _mapping(
        enterprise.get("trade")
    )

    risk = _mapping(
        enterprise.get("risk")
        or getattr(state, "risk", None)
    )

    execution = _mapping(
        enterprise.get("execution")
        or getattr(state, "execution", None)
    )

    # PAPER/LIVE is an execution concern, not the SCALP/SWING/CLASSIC
    # analysis-profile mode stored on state.mode.
    from config.config_manager import config

    execution_mode = config.get_execution_mode()

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

    market_tf = (
        _mapping(market.get(timeframe))
        if timeframe in market
        else market
    )

    candles = market_tf.get("candles", [])
    latest = candles[-1] if isinstance(candles, list) and candles else {}

    price = (
        latest.get("close")
        if isinstance(latest, dict)
        else None
    )

    if price is None:
        price = market_tf.get("price")

    if price is None:
        price = getattr(state, "close", 0.0)

    # Canonical IDM normally lives on state.idm.  Some analysis
    # paths expose the enterprise IDM result only in the report.
    # Preserve the canonical reasons and fall back to the report
    # rather than displaying a misleading "no reason" message.
    raw_reasons = master.get("reasons", [])

    if not raw_reasons:
        raw_reasons = enterprise.get("reasons", [])

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

    try:
        from core.canonical_portfolio_read_model import (
            build_canonical_portfolio_snapshot,
        )

        portfolio = build_canonical_portfolio_snapshot()
    except Exception:
        portfolio = {
            "authority": "JAGUAR_EXECUTION_DATABASE",
            "status": "UNAVAILABLE",
            "positions": [],
            "realized_pnl": None,
            "unrealized_pnl": None,
            "equity": None,
            "available_cash": None,
            "freshness": "UNKNOWN",
            "quantity_source": "EXECUTION_ORDERS",
            "broker": {
                "authority": "UPSTOX_SHORT_TERM_POSITIONS",
                "status": "UNAVAILABLE",
                "positions": [],
                "freshness": "UNKNOWN",
                "quantity_source": "UPSTOX_POSITION_API",
            },
            "account": {
                "authority": "UPSTOX_FUND_AND_MARGIN_V3",
                "status": "UNAVAILABLE",
                "available_to_trade": None,
                "cash_available_to_trade": None,
                "pledge_available_to_trade": None,
                "cash_margin_used": None,
                "pledge_margin_used": None,
                "unsettled_profit_today": None,
                "unsettled_profit_previous_days": None,
                "freshness": "UNKNOWN",
            },
            "reconciliation": {
                "status": "BROKER_UNAVAILABLE",
                "matches": [],
                "mismatches": [],
                "unmatched_broker_positions": [],
                "freshness": "UNKNOWN",
            },
        }

    market_timestamp = None

    if isinstance(latest, dict):
        market_timestamp = (
            latest.get("timestamp")
            or latest.get("time")
            or latest.get("datetime")
        )

    market_metadata = _mapping(
        getattr(state, "market_metadata", None)
    )

    market_freshness = _text(
        market_metadata.get("freshness"),
        "CURRENT",
    )

    raw_data_quality = market_metadata.get(
        "data_quality",
        {},
    )

    if not isinstance(raw_data_quality, dict):
        raw_data_quality = {}

    data_quality = {
        "status": _text(
            raw_data_quality.get("status"),
            "UNKNOWN",
        ),
        "integrity_ok": bool(
            raw_data_quality.get(
                "integrity_ok",
                False,
            )
        ),
        "schema_valid": bool(
            raw_data_quality.get(
                "schema_valid",
                False,
            )
        ),
        "ohlcv_valid": bool(
            raw_data_quality.get(
                "ohlcv_valid",
                False,
            )
        ),
        "timestamps_valid": bool(
            raw_data_quality.get(
                "timestamps_valid",
                False,
            )
        ),
        "monotonic": bool(
            raw_data_quality.get(
                "monotonic",
                False,
            )
        ),
        "duplicates_clear": bool(
            raw_data_quality.get(
                "duplicates_clear",
                False,
            )
        ),
        "interval_consistent": bool(
            raw_data_quality.get(
                "interval_consistent",
                False,
            )
        ),
        "gap_detected": bool(
            raw_data_quality.get(
                "gap_detected",
                False,
            )
        ),
        "gap_count": _number(
            raw_data_quality.get(
                "gap_count",
                0,
            )
        ),
        "gap_policy": _text(
            raw_data_quality.get("gap_policy"),
            "UNKNOWN",
        ),
        "candle_count": raw_data_quality.get(
            "candle_count"
        ),
        "expected_interval_ms": raw_data_quality.get(
            "expected_interval_ms"
        ),
        "observed_interval_ms": raw_data_quality.get(
            "observed_interval_ms"
        ),
        "reason": _text(
            raw_data_quality.get("reason"),
            "",
        ),
    }

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


    # ========================================================
    # Jaguar V3 Decision Intelligence
    # Decision -> Reason -> Blocker -> Next Condition
    # Presentation-only derivation.
    # Canonical authority remains upstream IDM / Risk / Execution.
    # ========================================================

    blocker = "NONE"
    blocker_status = "CLEAR"

    if not bool(
        master.get(
            "approved",
            enterprise.get("approved", False),
        )
    ):
        blocker_status = "BLOCKED"

        missing = master.get(
            "missing",
            enterprise.get("missing", []),
        ) or []

        if isinstance(missing, str):
            missing = [missing]

        if missing:
            blocker = str(missing[0])
        elif execution_reason:
            blocker = execution_reason
        elif decision_reasons:
            blocker = decision_reasons[0]
        else:
            blocker = (
                "IDM has not authorized an executable trade."
            )

    next_conditions = []

    missing = master.get(
        "missing",
        enterprise.get("missing", []),
    ) or []

    if isinstance(missing, str):
        missing = [missing]

    for condition in missing:
        text = str(condition).strip()
        if text and text not in next_conditions:
            next_conditions.append(text)

    readiness_value = str(
        structural.get(
            "readiness",
            master.get(
                "readiness",
                enterprise.get("readiness", ""),
            ),
        )
        or ""
    ).strip().upper()

    trigger_value = str(
        structural.get(
            "trigger_status",
            master.get(
                "trigger",
                enterprise.get("trigger", ""),
            ),
        )
        or ""
    ).strip().upper()

    if readiness_value in {
        "INVALID_ZONE",
        "ZONE_INTERACTION",
    }:
        if "VALID_EXECUTION_ZONE" not in next_conditions:
            next_conditions.append(
                "VALID_EXECUTION_ZONE"
            )

    if trigger_value in {
        "WAITING",
        "UNCONFIRMED",
    }:
        if "ENTRY_TRIGGER_CONFIRMATION" not in next_conditions:
            next_conditions.append(
                "ENTRY_TRIGGER_CONFIRMATION"
            )

    execution_confirmation_metadata = _mapping(
        execution_confirmation.get(
            "metadata"
        )
    )

    execution_confirmation_confirmed = bool(
        execution_confirmation.get(
            "confirmed",
            execution_confirmation_metadata.get(
                "confirmed",
                False,
            ),
        )
    )

    execution_confirmation_signal = str(
        execution_confirmation.get(
            "signal",
            execution_confirmation.get(
                "status",
                "WAIT",
            ),
        )
        or "WAIT"
    ).strip().upper()

    if (
        not bool(
            master.get(
                "approved",
                enterprise.get("approved", False),
            )
        )
        and readiness_value
        and readiness_value != "CONFIRMED"
        and readiness_value not in {
            "INVALID_ZONE",
            "ZONE_INTERACTION",
        }
    ):
        if (
            "STRUCTURAL_READINESS_CONFIRMATION"
            not in next_conditions
        ):
            next_conditions.append(
                "STRUCTURAL_READINESS_CONFIRMATION"
            )

    if (
        not bool(
            master.get(
                "approved",
                enterprise.get("approved", False),
            )
        )
        and (
            trigger_value in {
                "",
                "NONE",
                "WAITING",
                "UNCONFIRMED",
            }
            or not bool(
                structural.get(
                    "execution_trigger_confirmed",
                    False,
                )
            )
        )
    ):
        if (
            "ENTRY_TRIGGER_CONFIRMATION"
            not in next_conditions
        ):
            next_conditions.append(
                "ENTRY_TRIGGER_CONFIRMATION"
            )

    if (
        not bool(
            master.get(
                "approved",
                enterprise.get("approved", False),
            )
        )
        and not execution_confirmation_confirmed
    ):
        if (
            "EXECUTION_CONFIRMATION"
            not in next_conditions
        ):
            next_conditions.append(
                "EXECUTION_CONFIRMATION"
            )

    if (
        not next_conditions
        and not bool(
            master.get(
                "approved",
                enterprise.get("approved", False),
            )
        )
    ):
        next_conditions.append("IDM_AUTHORIZATION")

    authorization = (
        "AUTHORIZED"
        if bool(
            master.get(
                "approved",
                enterprise.get("approved", False),
            )
        )
        else "BLOCKED"
    )

    decision_gate = {
        "decision": decision,
        "reason": (
            decision_reasons[0]
            if decision_reasons
            else (
                execution_reason
                or "No executable decision has been authorized."
            )
        ),
        "blocker": blocker,
        "blocker_status": blocker_status,
        "next_conditions": next_conditions,
        "authorization": authorization,
    }


    execution_confirmation_reasons = (
        execution_confirmation.get("reasons", [])
        if isinstance(
            execution_confirmation.get("reasons", []),
            list,
        )
        else []
    )

    canonical_conflicts = (
        master.get(
            "conflicts",
            enterprise.get("conflicts", []),
        )
        or []
    )

    if isinstance(canonical_conflicts, str):
        canonical_conflicts = [canonical_conflicts]


    # ========================================================
    # Jaguar V3 Thesis / Invalidation
    #
    # Presentation-only canonical evidence surface.
    # No new prediction, threshold, or price rule.
    # ========================================================

    thesis_direction = _text(
        direction,
        "NEUTRAL",
    ).upper()

    thesis_conflict_flags = {
        "direction_conflict": bool(
            master.get(
                "direction_conflict",
                False,
            )
        ),
        "structural_conflict": bool(
            master.get(
                "structural_conflict",
                False,
            )
        ),
        "zone_conflict": bool(
            master.get(
                "zone_conflict",
                False,
            )
        ),
    }

    thesis_weakening = []

    raw_conflicts = (
        master.get(
            "conflicts",
            enterprise.get("conflicts", []),
        )
        or []
    )

    if isinstance(raw_conflicts, str):
        raw_conflicts = [raw_conflicts]

    for item in raw_conflicts:
        text = str(item).strip()
        if text and text not in thesis_weakening:
            thesis_weakening.append(text)

    institutional_state = _mapping(
        getattr(
            state,
            "institutional",
            None,
        )
    )

    for item in (
        institutional_state.get("warnings", [])
        if isinstance(
            institutional_state.get("warnings", []),
            list,
        )
        else []
    ):
        text = str(item).strip()
        if text and text not in thesis_weakening:
            thesis_weakening.append(text)

    brain_state = _mapping(
        getattr(
            state,
            "brain",
            None,
        )
    )

    for item in (
        brain_state.get("conflicts", [])
        if isinstance(
            brain_state.get("conflicts", []),
            list,
        )
        else []
    ):
        text = str(item).strip()
        if text and text not in thesis_weakening:
            thesis_weakening.append(text)

    thesis_support = []

    structural_direction = _text(
        structural.get("direction"),
        "NEUTRAL",
    ).upper()

    if (
        thesis_direction in {
            "BULLISH",
            "BEARISH",
        }
        and structural_direction == thesis_direction
    ):
        thesis_support.append(
            f"Canonical structural direction: "
            f"{thesis_direction}"
        )

    structure_state = _text(
        structural.get("structure_state"),
        "UNKNOWN",
    )

    if structure_state not in {
        "",
        "UNKNOWN",
        "UNDEFINED",
    }:
        thesis_support.append(
            f"Structure state: {structure_state}"
        )

    bos_signal = _text(
        bos_engine.get("signal"),
        "NEUTRAL",
    ).upper()

    if (
        thesis_direction in {
            "BULLISH",
            "BEARISH",
        }
        and bos_signal == thesis_direction
    ):
        thesis_support.append(
            f"BOS confirms {thesis_direction}"
        )

    choch_signal = _text(
        choch_engine.get("signal"),
        "NEUTRAL",
    ).upper()

    if (
        thesis_direction in {
            "BULLISH",
            "BEARISH",
        }
        and choch_signal == thesis_direction
    ):
        thesis_support.append(
            f"CHoCH confirms {thesis_direction}"
        )

    mtf_state = _mapping(
        getattr(
            state,
            "mtf",
            None,
        )
    )

    mtf_bias = _text(
        mtf_state.get("bias"),
        "NEUTRAL",
    ).upper()

    if (
        thesis_direction in {
            "BULLISH",
            "BEARISH",
        }
        and mtf_bias == thesis_direction
    ):
        thesis_support.append(
            f"MTF bias: {mtf_bias}"
        )

    enterprise_trend = _text(
        enterprise.get("trend"),
        "",
    ).upper()

    if (
        thesis_direction in {
            "BULLISH",
            "BEARISH",
        }
        and enterprise_trend == thesis_direction
    ):
        thesis_support.append(
            f"Enterprise trend: {enterprise_trend}"
        )

    enterprise_regime = _text(
        enterprise.get("regime"),
        "",
    ).upper()

    if (
        thesis_direction in {
            "BULLISH",
            "BEARISH",
        }
        and enterprise_regime == thesis_direction
    ):
        thesis_support.append(
            f"Enterprise regime: {enterprise_regime}"
        )

    thesis_support = list(
        dict.fromkeys(thesis_support)
    )

    if thesis_direction not in {
        "BULLISH",
        "BEARISH",
    }:
        thesis_status = "UNDEFINED"
    elif any(thesis_conflict_flags.values()):
        thesis_status = "WEAKENED"
    else:
        thesis_status = "ACTIVE"

    thesis_invalidation_gates = [
        "DIRECTION_CONFLICT",
        "STRUCTURAL_CONFLICT",
        "ZONE_CONFLICT",
        "CONFLICT_CLEARANCE",
    ]

    active_invalidation = []

    if thesis_conflict_flags["direction_conflict"]:
        active_invalidation.append(
            "DIRECTION_CONFLICT"
        )

    if thesis_conflict_flags["structural_conflict"]:
        active_invalidation.append(
            "STRUCTURAL_CONFLICT"
        )

    if thesis_conflict_flags["zone_conflict"]:
        active_invalidation.append(
            "ZONE_CONFLICT"
        )

    if (
        "CONFLICT_CLEARANCE" in (
            master.get("missing", [])
            or []
        )
    ):
        active_invalidation.append(
            "CONFLICT_CLEARANCE"
        )

    thesis_invalidation = {
        "direction": thesis_direction,
        "status": thesis_status,
        "setup": _text(
            master.get("setup")
            or enterprise.get("setup"),
            "UNKNOWN",
        ),
        "supporting_evidence": thesis_support,
        "weakening_evidence": thesis_weakening,
        "canonical_invalidation_gates":
            thesis_invalidation_gates,
        "active_invalidation":
            list(dict.fromkeys(active_invalidation)),
        "direction_relationship": _text(
            master.get(
                "direction_relationship"
                ,
                enterprise.get(
                    "direction_relationship"
                ),
            ),
            "UNKNOWN",
        ),
    }

    what_would_change = {
        "current_decision": decision,
        "current_authorization": authorization,
        "required_conditions": list(next_conditions),
        "structural_readiness": readiness_value or "UNKNOWN",
        "trigger_status": trigger_value or "UNKNOWN",
        "trigger_confirmed": bool(
            structural.get(
                "execution_trigger_confirmed",
                False,
            )
        ),
        "execution_confirmation": (
            execution_confirmation_signal
        ),
        "execution_confirmation_confirmed": (
            execution_confirmation_confirmed
        ),
        "execution_zone_interaction": bool(
            execution_confirmation_metadata.get(
                "zone_interaction",
                False,
            )
        ),
        "execution_trigger_confirmed": bool(
            execution_confirmation_metadata.get(
                "trigger_confirmed",
                False,
            )
        ),
        "execution_trigger_fresh": bool(
            execution_confirmation_metadata.get(
                "trigger_fresh",
                False,
            )
        ),
        "execution_confirmation_reasons": [
            str(reason).strip()
            for reason in execution_confirmation_reasons
            if str(reason).strip()
        ],
        "conflicts": [
            str(conflict).strip()
            for conflict in canonical_conflicts
            if str(conflict).strip()
        ],
        "decision_reasons": list(
            decision_reasons
        ),
    }


    # ========================================================
    # Jaguar V3 Trade Setup Presentation
    #
    # Canonical-source presentation only.
    # This does not authorize or reject trades.
    # ========================================================

    setup_value = _text(
        master.get("setup")
        or enterprise.get("setup"),
        "UNKNOWN",
    ).upper()

    zone_available = bool(
        master.get(
            "zone_available",
            enterprise.get("zone_available", False),
        )
    )

    if setup_value in {
        "CONTINUATION",
        "REVERSAL",
    } and zone_available:
        setup_status = "SETUP PRESENT"
    elif setup_value in {
        "STRUCTURAL_WATCH",
        "STRUCTURAL_WAIT",
    }:
        setup_status = "DEVELOPING SETUP"
    else:
        setup_status = "NO SETUP"

    trade_setup = {
        "status": setup_status,
        "direction": _text(
            master.get(
                "direction",
                enterprise.get("direction"),
            ),
            "NEUTRAL",
        ),
        "setup_type": setup_value,
        "zone": _text(
            structural.get("zone_type"),
            "NONE",
        ),
        "zone_status": _text(
            structural.get("zone_status"),
            "UNKNOWN",
        ),
        "zone_lifecycle": _text(
            structural.get("zone_lifecycle"),
            "UNKNOWN",
        ),
        "location": _text(
            structural.get("location_quality"),
            "UNKNOWN",
        ),
        "readiness": _text(
            structural.get("readiness"),
            "UNKNOWN",
        ),
        "trigger": _text(
            structural.get("trigger_status"),
            "NONE",
        ),
        "trigger_confirmed": bool(
            execution_confirmation.get(
                "confirmed",
                False,
            )
        ),
        "execution_confirmation": _text(
            execution_confirmation.get(
                "signal",
                execution_confirmation.get(
                    "status",
                    "WAIT",
                ),
            ),
            "WAIT",
        ),
        "risk_status": _text(
            risk.get("status"),
            "UNKNOWN",
        ),
        "execution_status": _text(
            execution.get("status"),
            "WAIT",
        ),
        "execution_ready": bool(
            execution.get("ready", False)
        ),
        "execution_approved": bool(
            execution.get("approved", False)
        ),
    }

    # ========================================================
    # Jaguar V3 Confidence Breakdown
    #
    # Presentation-only. No new composite confidence score is
    # manufactured here. Values retain canonical provenance.
    # ========================================================

    report_engines = (
        report.get("engines", {})
        if isinstance(report, dict)
        else {}
    )

    if not isinstance(report_engines, dict):
        report_engines = {}

    confidence_engines = {}

    for engine_name, engine_result in report_engines.items():
        if not isinstance(engine_result, dict):
            continue

        raw_confidence = engine_result.get(
            "confidence",
            0.0,
        )

        try:
            raw_confidence = float(
                raw_confidence or 0.0
            )
        except (TypeError, ValueError):
            raw_confidence = 0.0

        confidence_engines[str(engine_name)] = {
            "confidence": _number(
                raw_confidence
            ),
            "confidence_percent": _number(
                raw_confidence * 100.0
            ),
            "signal": _text(
                engine_result.get("signal"),
                "NEUTRAL",
            ),
            "score": _number(
                engine_result.get(
                    "score",
                    0.0,
                )
            ),
            "weight": _number(
                engine_result.get(
                    "weight",
                    0.0,
                )
            ),
            "reasons": (
                engine_result.get("reasons", [])
                if isinstance(
                    engine_result.get("reasons", []),
                    list,
                )
                else []
            ),
        }

    mtf_state = getattr(
        state,
        "mtf",
        None,
    )

    if not isinstance(mtf_state, dict):
        mtf_state = {}

    institutional_confidence = getattr(
        state,
        "institutional_confidence",
        None,
    )

    if institutional_confidence is None:
        institutional_confidence = master.get(
            "confidence",
            0.0,
        )

    confidence_breakdown = {
        "idm_confidence": _number(
            master.get(
                "confidence",
                institutional_confidence,
            )
        ),
        "institutional_confidence": _number(
            institutional_confidence
        ),
        "institutional_score": _number(
            master.get(
                "score",
                0.0,
            )
        ),
        "probability": _number(
            getattr(
                state,
                "probability",
                None,
            )
        ),
        "grade": _text(
            getattr(
                state,
                "confidence",
                None,
            ),
            "UNKNOWN",
        ),
        "context_grade": _text(
            getattr(
                state,
                "context_confidence",
                None,
            ),
            "UNKNOWN",
        ),
        "mtf": {
            "confidence": _number(
                mtf_state.get(
                    "confidence",
                    0.0,
                )
            ),
            "bias": _text(
                mtf_state.get(
                    "bias",
                    "NEUTRAL",
                ),
                "NEUTRAL",
            ),
            "alignment": _number(
                mtf_state.get(
                    "alignment",
                    0,
                )
            ),
            "score": _number(
                mtf_state.get(
                    "score",
                    0.0,
                )
            ),
        },
        "engines": confidence_engines,
        "method": (
            "Canonical evidence only; "
            "no derived composite confidence."
        ),
    }

    # ========================================================
    # MTF DATA SUFFICIENCY
    # UNAVAILABLE != NEUTRAL
    # ========================================================

    required_mtf = ["15m", "1h", "4h", "1d"]
    available_mtf = []
    unavailable_mtf = []

    for frame in required_mtf:
        frame_data = mtf.get(frame, {})
        trend_value = str(
            frame_data.get("trend") or "UNDEFINED"
        ).strip().upper()

        if trend_value in {
            "UNAVAILABLE",
            "UNDEFINED",
            "UNKNOWN",
            "NONE",
            "",
        }:
            unavailable_mtf.append(frame)
        else:
            available_mtf.append(frame)

    mtf_required_count = len(required_mtf)
    mtf_available_count = len(available_mtf)

    if mtf_available_count == mtf_required_count:
        mtf_sufficiency_status = "COMPLETE"
    elif mtf_available_count == 0:
        mtf_sufficiency_status = "UNAVAILABLE"
    else:
        mtf_sufficiency_status = "PARTIAL"

    mtf_sufficiency = {
        "required": required_mtf,
        "available": available_mtf,
        "unavailable": unavailable_mtf,
        "required_count": mtf_required_count,
        "available_count": mtf_available_count,
        "unavailable_count": len(unavailable_mtf),
        "coverage_ratio": (
            mtf_available_count / mtf_required_count
            if mtf_required_count
            else 0.0
        ),
        "status": mtf_sufficiency_status,
        "impact": (
            "FULL_CONTEXT"
            if mtf_sufficiency_status == "COMPLETE"
            else (
                "PARTIAL_CONTEXT"
                if mtf_sufficiency_status == "PARTIAL"
                else "NO_MTF_CONTEXT"
            )
        ),
    }

    return {
        "system": {
            "mode": _text(
                execution_mode,
                "PAPER",
            ).upper(),
            "health": "HEALTHY",
        },

        "freshness": {
            "generated_at": generated_at.isoformat(
                timespec="seconds"
            ),
            "generated_epoch": generated_epoch,
            "market_timestamp": market_timestamp,
            "initial_status": market_freshness,
        },

        "data_quality": data_quality,

        "mtf": mtf,
        "mtf_sufficiency": mtf_sufficiency,
        "decision_gate": decision_gate,
        "what_would_change": what_would_change,
        "thesis_invalidation": thesis_invalidation,
        "trade_setup": trade_setup,
        "confidence_breakdown": confidence_breakdown,

        "fibonacci": _fibonacci_ui(
            getattr(state, "fibonacci", None)
        ),

        "portfolio": portfolio,

        "market": {
            "symbol": _text(
                getattr(state, "symbol", ""),
            ),
            "timeframe": _text(timeframe),
            "price": _number(price),
            "status": "ANALYSIS READY" if candles else "UNKNOWN",
        },

        "idm": {
            "decision": decision,
            "approved": bool(
                master.get("approved", enterprise.get("approved", False))
            ),
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
                master.get(
                    "priority",
                    enterprise.get("priority", "UNKNOWN"),
                ),
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
            "setup": _text(
                master.get("setup")
                or enterprise.get("setup"),
                "UNKNOWN",
            ),
            "missing": (
                master.get("missing")
                or enterprise.get("missing")
                or []
            ),
            "confirmed": (
                master.get("confirmed")
                or enterprise.get("confirmed")
                or []
            ),
            "direction_relationship": _text(
                master.get("direction_relationship")
                or enterprise.get("direction_relationship"),
                "UNKNOWN",
            ),
            "decision_reasons": decision_reasons,
        },

        "structure": {
            "trend": _text(
                structure.get("trend", getattr(state, "trend", None)),
                "UNDEFINED",
            ),
            "bos": _text(
                structure_bos.get("signal"),
                "NEUTRAL",
            ),
            "bos_reason": _text(
                structure_bos.get("reasons", [""])[0]
                if structure_bos.get("reasons")
                else "",
            ),
            "bos_score": _number(
                bos_engine.get("score", 0)
            ),
            "bos_confidence": _number(
                bos_engine.get("confidence", 0)
            ),
            "choch": _text(
                structure_choch.get("signal"),
                "NEUTRAL",
            ),
            "choch_reason": _text(
                structure_choch.get("reasons", [""])[0]
                if structure_choch.get("reasons")
                else "",
            ),
            "choch_score": _number(
                choch_engine.get("score", 0)
            ),
            "choch_confidence": _number(
                choch_engine.get("confidence", 0)
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
            "mode": _text(
                execution_mode,
                "PAPER",
            ).upper(),
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
