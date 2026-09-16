# research/audit_execution_gate.py

import copy
import json
import os
import tempfile
import uuid
from collections import Counter
from datetime import datetime

from core.backtest_engine import BacktestEngine
from core.orchestrator import JaguarOrchestrator
from jaguar_version import JAGUAR_VERSION
from research.database import (
    get_campaign_stats,
    init_db,
    insert_research_run,
    update_research_run,
)


def _run(symbol, mode, filename_prefix):
    log_path = os.path.join(
        tempfile.gettempdir(),
        f"{filename_prefix}_{symbol}_{mode}.json",
    )

    if os.path.exists(log_path):
        os.remove(log_path)

    app = JaguarOrchestrator()
    state = app.analyze(symbol, "15m", mode=mode)

    init_db()

    run_id = str(uuid.uuid4())
    start_time = datetime.now().isoformat()

    insert_research_run(
        run_id,
        JAGUAR_VERSION,
        symbol,
        mode,
        "15m",
        start_time=start_time,
    )

    state.run_id = run_id

    replay_state = copy.deepcopy(state)
    replay_state.symbol = symbol
    replay_state.interval = "15m"
    replay_state.mode = mode
    replay_state.run_id = run_id

    engine = BacktestEngine()
    engine.run(replay_state, app.bus)

    result = engine.result
    trades = list(getattr(result, "trades", []) or [])

    with open(log_path, "w") as f:
        json.dump(trades, f, indent=2)

    end_time = datetime.now().isoformat()
    duration = (
        datetime.fromisoformat(end_time)
        - datetime.fromisoformat(start_time)
    ).total_seconds()

    stats = get_campaign_stats(run_id)

    update_research_run(
        run_id,
        end_time,
        duration,
        stats["total_decisions"],
        stats["executed_trades"],
        stats["wins"],
        stats["losses"],
        stats["avg_brain_score"],
        stats["avg_composite_score"],
        stats["avg_confidence"],
    )

    return {
        "run_id": run_id,
        "log_path": log_path,
        "state": replay_state,
        "engine": engine,
        "result": result,
        "trades": trades,
    }


def _summary(audit, title):
    result = audit["result"]
    trades = audit["trades"]

    valid = [
        item
        for item in trades
        if isinstance(item, dict)
        and isinstance(item.get("authorization_id"), str)
        and item.get("authorization_id").strip()
    ]

    long_count = sum(
        1 for item in valid
        if str(item.get("direction", "")).upper() == "BUY"
    )

    short_count = sum(
        1 for item in valid
        if str(item.get("direction", "")).upper() == "SELL"
    )

    decisions = Counter(
        str(item.get("idm_decision", "UNKNOWN")).upper()
        for item in valid
    )

    statuses = Counter(
        str(item.get("status", "UNKNOWN")).upper()
        for item in valid
    )

    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)
    print(f"  Result records                     : {len(trades)}")
    print(f"  Authorized records                 : {len(valid)}")
    print(
        "  ENTER_LONG                         : "
        f"{decisions.get('ENTER_LONG', 0)}"
    )
    print(
        "  ENTER_SHORT                        : "
        f"{decisions.get('ENTER_SHORT', 0)}"
    )
    print(f"  BUY                                 : {long_count}")
    print(f"  SELL                                : {short_count}")
    print(f"  Wins                                : {result.wins}")
    print(f"  Losses                              : {result.losses}")
    print(f"  Total trades                       : {result.total_trades}")

    if result.total_trades:
        print(f"  Win rate                            : {result.win_rate}%")
        print(f"  Loss rate                           : {result.loss_rate}%")

    if statuses:
        print("\n  STATUS")
        for key, value in statuses.most_common():
            print(f"  {key:20s}: {value}")

    if valid:
        print("\n  AUTHORIZATION RECORDS")
        for number, item in enumerate(valid[:10], 1):
            print(
                f"  {number:02d}. "
                f"decision={item.get('idm_decision')} "
                f"direction={item.get('direction')} "
                f"status={item.get('status')} "
                f"entry={item.get('entry')} "
                f"authorization={item.get('authorization_id')}"
            )
    else:
        print("\n  VERDICT")
        print("  No authorized historical execution was produced.")

    print("=" * 70)


def run_execution_gate_audit(symbol="GC=F", mode="SCALP"):
    audit = _run(
        symbol=symbol,
        mode=mode,
        filename_prefix="execution_gate",
    )

    _summary(
        audit,
        "EXECUTION GATE AUDIT",
    )

    return audit


def run_execution_gates_audit(symbol="GC=F", mode="SCALP"):
    audit = _run(
        symbol=symbol,
        mode=mode,
        filename_prefix="gate_audit",
    )

    _summary(
        audit,
        "ENTERPRISE EXECUTION GATE AUDIT",
    )

    return audit
