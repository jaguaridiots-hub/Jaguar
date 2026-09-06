# research/recorder.py
import json
import uuid
import hashlib
from datetime import datetime
from core.asset_registry import get_asset_class
from .database import (
    init_db,
    insert_open_trade,
    delete_open_trade,
    update_close_trade,
    insert_decision_log,
)
from jaguar_version import JAGUAR_VERSION

# ---- Phase 38: Persistence Audit logging ----
AUDIT_LOG_FILE = None

def set_audit_log_path(path):
    global AUDIT_LOG_FILE
    AUDIT_LOG_FILE = path

def _compute_checksum(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()

def record_trade_open(
    state,
    run_id=None,
    entry_time=None,
    trade_uuid=None,
    authorization_id=None,
):
    init_db()

    enterprise_trade = getattr(state, "trade", {}) or {}
    enterprise_execution = getattr(state, "execution", {}) or {}
    legacy_trade_plan = getattr(state, "trade_plan", {}) or {}

    if (
        isinstance(enterprise_trade, dict)
        and enterprise_trade.get("entry") is not None
    ):
        trade_plan = enterprise_trade
        contract_source = "ENTERPRISE"
    elif isinstance(legacy_trade_plan, dict) and legacy_trade_plan:
        trade_plan = legacy_trade_plan
        contract_source = "LEGACY"
    else:
        return None

    asset_class = get_asset_class(state.symbol) or "unknown"

    # Canonical execution authority: IDM.
    idm = getattr(state, "idm", {}) or {}
    if not isinstance(idm, dict):
        idm = {}

    # Compatibility-only mirror.
    md = getattr(state, "master_decision", {}) or {}
    if not isinstance(md, dict):
        md = {}
    brain = getattr(state, "ai_brain", {})
    prob = getattr(state, "probability", {})
    if not isinstance(prob, dict):
        prob = {"score": prob}

    risk = getattr(state, "risk", {})
    if not isinstance(risk, dict):
        risk = {}
    validator = getattr(state, "trade_validator", None) or {}
    decision_weights = getattr(state, "_decision_weights", {})
    brain_explain = getattr(state, "brain_explain", {})
    regime = getattr(state, "regime", {})
    mtf = getattr(state, "mtf", {})
    smc = getattr(state, "smc", {})
    liquidity = getattr(state, "liquidity", {})
    fvg = getattr(state, "fvg", {})
    orderflow = getattr(state, "orderflow", {})
    enterprise_targets = trade_plan.get("targets", [])

    if (
        isinstance(enterprise_targets, list)
        and len(enterprise_targets) > 0
    ):
        take_profit = enterprise_targets[0]
    else:
        take_profit = trade_plan.get("tp1")

    snapshot_open = {
        # Canonical execution authority.
        "execution_authority": "IDM",
        "idm": idm,

        # Compatibility / legacy mirror retained for provenance.
        "master_decision": md,

        "brain": brain,
        "probability": prob,
        "validator": validator,
        "risk": risk,
        "trade_plan": trade_plan,
        "enterprise_trade": enterprise_trade,
        "enterprise_execution": enterprise_execution,
        "contract_source": contract_source,
        "mode": state.mode,
        "regime": regime,
        "session": getattr(state, "session", {}),
        "market": {
            "price": state.price,
            "high": state.high,
            "low": state.low,
            "volume": state.volume,
        },
        "brain_explain": brain_explain,
        "decision_weights": decision_weights,
        "engine_contributions": brain_explain.get("contributions", []),
    }
    snapshot_json = json.dumps(snapshot_open, default=str)
    checksum = _compute_checksum(snapshot_open)

    trade_uuid = trade_uuid or str(uuid.uuid4())

    state_authorization_id = None

    if isinstance(enterprise_execution, dict):
        state_authorization_id = enterprise_execution.get(
            "authorization_id"
        )

    # FAIL-CLOSED: authoritative execution identity is mandatory.
    if (
        not isinstance(authorization_id, str)
        or not authorization_id.strip()
    ):
        raise RuntimeError(
            "FAIL-CLOSED: Missing authoritative authorization_id"
        )

    # FAIL-CLOSED: mutable state must agree with the authoritative
    # execution identity before persistence.
    if state_authorization_id != authorization_id:
        raise RuntimeError(
            "FAIL-CLOSED: Authorization identity mismatch "
            f"(state={state_authorization_id!r}, "
            f"authoritative={authorization_id!r})"
        )

    data = {
        "uuid": trade_uuid,
        "authorization_id": authorization_id,
        "status": "OPEN",
        "open_time": entry_time or datetime.now().isoformat(),
        "symbol": state.symbol,
        "timeframe": state.interval,
        "mode": state.mode,
        "entry_price": trade_plan.get("entry"),
        "stop_loss": trade_plan.get("stop_loss", trade_plan.get("stop")),
        "take_profit": take_profit,
        "snapshot_open": snapshot_json,
        "snapshot_open_checksum": checksum,
        # Canonical executable decision facts come from IDM.
        "decision": idm.get("decision"),
        "confidence": idm.get("confidence"),
        "composite_score": idm.get("score"),
        "brain_score": brain.get("score"),
        "probability_score": prob.get("score"),
        # Compatibility column; canonical authority remains IDM.
        "master_decision": idm.get("decision"),
        "validator_score": validator.get("validation_score", 0),
        "market_regime": regime.get("regime"),
        "mtf_bias": mtf.get("bias"),
        "smc_signal": smc.get("signal"),
        "liquidity_signal": liquidity.get("signal"),
        "fvg_signal": fvg.get("signal"),
        "orderflow_signal": orderflow.get("signal"),
        "run_id": run_id,
        "success": 1,
        "asset_class": asset_class,
    }
    insert_open_trade(data)
    print(f"📊 Research: Trade {trade_uuid} opened.")
    return trade_uuid

def compensate_trade_open(trade_uuid):
    """Remove a DB trade created before position persistence failed."""
    delete_open_trade(trade_uuid)


def record_trade_abandoned(uuid):
    """Mark a finite-replay trade as right-censored/abandoned.

    This is a research terminal state, not a realized exit.
    No exit price, PnL, R-multiple, or close_time is fabricated.
    """
    init_db()

    if not isinstance(uuid, str) or not uuid.strip():
        raise ValueError("Invalid trade UUID")

    update_close_trade(
        uuid,
        {
            "status": "ABANDONED",
        },
    )

    print(
        f"📊 Research: Trade {uuid} abandoned at replay boundary."
    )


def record_trade_close(uuid, exit_price, pnl, r_multiple, win_loss, holding_time, exit_time=None):
    init_db()
    close_data = {
        "status": "CLOSED",
        "close_time": exit_time or datetime.now().isoformat(),
        "exit_price": exit_price,
        "pnl": pnl,
        "r_multiple": r_multiple,
        "win_loss": 1 if win_loss else 0,
        "holding_time": int(holding_time),
        "snapshot_close": json.dumps({
            "exit_price": exit_price,
            "pnl": pnl,
            "r_multiple": r_multiple,
            "win_loss": win_loss,
            "holding_time": int(holding_time),
            "timestamp": datetime.now().isoformat()
        }),
        "snapshot_close_checksum": _compute_checksum({
            "exit_price": exit_price,
            "pnl": pnl,
            "r_multiple": r_multiple,
            "win_loss": win_loss,
            "holding_time": int(holding_time),
            "timestamp": datetime.now().isoformat()
        })
    }
    update_close_trade(uuid, close_data)
    print(f"📊 Research: Trade {uuid} closed (PnL: {pnl:.2f}, R: {r_multiple:.2f})")


def record_decision_snapshot(state, candle_timestamp=None):
    """
    Capture all scoring data from the state after a decision is made.
    """
    decision_id = str(uuid.uuid4())

    # Canonical decision authority is IDM.
    # master_decision remains a compatibility fallback
    # for legacy/replay states that do not provide IDM.
    idm = getattr(state, "idm", None)
    if isinstance(idm, dict) and idm:
        md = idm
    else:
        md = getattr(state, "master_decision", {}) or {}

    brain = getattr(state, "ai_brain", {})
    brain_explain = getattr(state, "brain_explain", {})
    contributions = brain_explain.get("contributions", [])

    regime = getattr(state, "regime", {})
    smc = getattr(state, "smc", {})
    liquidity = getattr(state, "liquidity", {})
    orderflow = getattr(state, "orderflow", {})
    premium_discount = getattr(state, "premium_discount", None)
    session = getattr(state, "session", {})
    volume_profile = getattr(state, "volume_profile", {})
    validator = getattr(state, "trade_validator", {})

    pd_signal = None
    if isinstance(premium_discount, dict):
        pd_signal = premium_discount.get("signal") or premium_discount.get("raw")
    elif isinstance(premium_discount, str):
        pd_signal = premium_discount

    # Convert candle timestamp to ISO string
    ts = None
    if candle_timestamp is not None:
        try:
            if isinstance(candle_timestamp, (int, float)):
                ts = datetime.fromtimestamp(candle_timestamp).isoformat()
            else:
                datetime.fromisoformat(str(candle_timestamp))
                ts = str(candle_timestamp)
        except Exception:
            ts = datetime.now().isoformat()
    else:
        ts = datetime.now().isoformat()

    # Determine initial rejection stage
    decision = md.get("decision", "REJECT")
    trade_plan = getattr(state, "trade_plan", None)
    validator_approved = validator.get("approved", True) if validator else True

    if decision in ("BUY", "SELL") and trade_plan:
        stage = "NONE"
    elif not validator_approved:
        stage = "VALIDATOR"
    else:
        stage = "MASTER_DECISION"

    # Engine snapshot (raw signals) – keys must match contributions_json names
    engine_snapshot = {
        "SMC": smc.get("signal", "NONE"),
        "Structure": getattr(state, "structure", {}).get("signal", "NONE"),
        "Order Flow": orderflow.get("signal", "NONE"),               # was "OrderFlow"
        "Wyckoff": getattr(state, "wyckoff", {}).get("signal", "NONE"),
        "Liquidity": liquidity.get("signal", "NONE"),
        "Volume Profile": volume_profile.get("signal", "NONE"),      # was "VolumeProfile"
        "Session": session.get("signal", "NONE") if isinstance(session, dict) else "NONE",
        "Premium/Discount": pd_signal or "NONE",                     # was "PremiumDiscount"
    }

    # MTF loaded status
    available_timeframes = ["15m", "1h", "4h", "1d"]
    mtf_status = {}
    for tf in available_timeframes:
        mtf_status[tf] = tf in state.timeframes if hasattr(state, "timeframes") else False

    # ---- Phase 38: Write runtime values to audit log BEFORE writing to DB ----
    if AUDIT_LOG_FILE:
        try:
            with open(AUDIT_LOG_FILE, "a") as f:
                audit_entry = {
                    "decision_id": decision_id,
                    "brain_score": brain.get("score"),
                    "composite_score": md.get("score"),
                    "contributions": contributions,
                    "engine_snapshot": engine_snapshot,
                }
                f.write(json.dumps(audit_entry) + "\n")
        except Exception as e:
            print(f"⚠️  Audit log write failed: {e}")

    data = {
        "decision_id": decision_id,
        "timestamp": ts,
        "symbol": state.symbol,
        "timeframe": state.interval,
        "mode": state.mode,
        "brain_score": brain.get("score"),
        "composite_score": md.get("score"),
        "decision": decision,
        "contributions_json": json.dumps(contributions, default=str),
        "regime": regime.get("regime"),
        "smc_signal": smc.get("signal"),
        "liquidity_signal": liquidity.get("signal"),
        "orderflow_signal": orderflow.get("signal"),
        "premium_discount": pd_signal,
        "session_score": session.get("score") if isinstance(session, dict) else None,
        "volume_profile_score": volume_profile.get("score") if isinstance(volume_profile, dict) else None,
        "rejection_stage": stage,
        "rejection_reasons": json.dumps(md.get("reasons", []), default=str) if md else None,
        "validator_approved": 1 if validator_approved else 0,
        "engine_snapshot_json": json.dumps(engine_snapshot, default=str),
        "mtf_loaded": json.dumps(mtf_status),
        "threshold_required_score": None,
        "trade_uuid": getattr(state, "_trade_id", None),
        "outcome": "REJECT",
        "run_id": getattr(state, "run_id", None),
        "jaguar_version": JAGUAR_VERSION,
    }

    if data["trade_uuid"]:
        data["outcome"] = "OPEN"

    insert_decision_log(data)
    return decision_id
