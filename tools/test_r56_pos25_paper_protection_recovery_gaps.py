"""R56-POS-25 adversarial PAPER protection recovery witness."""

from pathlib import Path
import tempfile

import research.database as db

from engine.active_trade_recovery import (
    ActiveTradeRecoveryError,
    recover_active_trade_from_durable_lifecycle,
)
from engine.position_manager import PositionManager
from engine.trade_manager import TradeManager

from tools.test_r56_pos24_restart_recovery_witness import (
    create_durable_trade,
)


def recover():
    position = PositionManager()
    manager = TradeManager()

    return recover_active_trade_from_durable_lifecycle(
        position=position,
        manager=manager,
        symbol="BTCUSDT",
    )


def main():
    with tempfile.TemporaryDirectory(
        dir=".jaguar_audit",
        prefix="r56-pos25-protection-",
    ) as td:
        temp_db = Path(td) / "protection-gaps.db"

        original_db = db.DB_PATH
        db.DB_PATH = str(temp_db)

        try:
            db.init_db()

            auth = "AUTH-R56-POS25-PROTECTION"
            trade_uuid = "TRADE-R56-POS25-PROTECTION"

            create_durable_trade(
                auth=auth,
                trade_uuid=trade_uuid,
                direction="LONG",
                fill_price=101.0,
            )

            # ----------------------------------------------------------
            # GAP 1 regression: VERIFIED protection with incorrect
            # verified_qty must fail closed against the durable fill.
            # ----------------------------------------------------------
            conn = db.get_connection()
            try:
                cursor = conn.execute(
                    """
                    UPDATE execution_protection
                    SET verified_qty = 1.0
                    WHERE authorization_id = ?
                      AND protection_type = 'STOP_LOSS'
                    """,
                    (auth,),
                )
                assert cursor.rowcount == 1
                conn.commit()
            finally:
                conn.close()

            try:
                recover()
            except ActiveTradeRecoveryError as exc:
                assert "verified quantity" in str(exc).lower()
                print(
                    "R56_POS25_VERIFIED_QTY_FAIL_CLOSED: PASS"
                )
            else:
                raise AssertionError(
                    "Corrupt VERIFIED protection quantity was accepted"
                )

            # ----------------------------------------------------------
            # GAP 2 regression: an unexpected TP4 must fail closed.
            # Use a fresh isolated DB so the first deliberate corruption
            # cannot interfere with the second recovery witness.
            # ----------------------------------------------------------
            second_db = Path(td) / "extra-tp.db"
            db.DB_PATH = str(second_db)
            db.init_db()

            auth = "AUTH-R56-POS25-EXTRA-TP"
            trade_uuid = "TRADE-R56-POS25-EXTRA-TP"

            create_durable_trade(
                auth=auth,
                trade_uuid=trade_uuid,
                direction="LONG",
                fill_price=101.0,
            )

            db.insert_execution_protection(
                {
                    "protection_id": f"{auth}:PROTECTION:TP4",
                    "authorization_id": auth,
                    "protection_type": "TAKE_PROFIT",
                    "target_index": 3,
                    "broker_order_id": None,
                    "requested_qty": 2.0,
                    "verified_qty": 2.0,
                    "requested_price": 120.0,
                    "verified_price": 120.0,
                    "status": "VERIFIED",
                    "created_at": "2026-09-29T00:00:00",
                    "updated_at": "2026-09-29T00:00:00",
                }
            )

            try:
                recover()
            except ActiveTradeRecoveryError as exc:
                assert (
                    "cardinality" in str(exc).lower()
                    or "not exact" in str(exc).lower()
                )
                print(
                    "R56_POS25_EXTRA_TP_FAIL_CLOSED: PASS"
                )
            else:
                raise AssertionError(
                    "Unexpected TP4 protection was accepted"
                )

            print(
                "R56-POS-25_PROTECTION_RECOVERY_CONTRACT: PASS"
            )

        finally:
            db.DB_PATH = original_db


if __name__ == "__main__":
    main()
