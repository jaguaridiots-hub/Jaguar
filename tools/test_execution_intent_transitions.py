import tempfile
from pathlib import Path

import research.database as db


with tempfile.TemporaryDirectory() as tmp:
    db.DB_PATH = str(
        Path(tmp) / "execution_transition.sqlite3"
    )
    db.init_db()

    authorization_id = "TRANSITION-CANCEL-001"

    db.insert_execution_intent({
        "authorization_id": authorization_id,
        "trade_uuid": "TRADE-TRANSITION-001",
        "client_order_id": "CLIENT-TRANSITION-001",
        "symbol": "SBIN",
        "timeframe": "15m",
        "mode": "PAPER",
        "decision": "LONG",
        "quantity": 1.0,
        "status": "AUTHORIZED",
        "created_at": "2026-09-09T00:00:00",
        "updated_at": "2026-09-09T00:00:00",
    })

    db.update_execution_intent(
        authorization_id,
        status="CANCELLED",
    )

    stored = dict(
        db.get_execution_intent(
            authorization_id
        )
    )

    assert stored["status"] == "CANCELLED"

    print("AUTHORIZED_TO_CANCELLED: PASS")
    print("EXECUTION_INTENT_TRANSITION_REGRESSION: PASS")
