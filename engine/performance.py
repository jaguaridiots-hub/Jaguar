from research import database as db
from research.closed_trade_integrity import (
    validate_closed_trade_record,
)


class Performance:

    def summary(self):

        # Durable CLOSED trades are the authoritative source
        # for terminal performance reporting.
        db.init_db()

        conn = db.get_connection()

        try:
            rows = conn.execute(
                """
                SELECT *
                FROM trades
                WHERE status = 'CLOSED'
                ORDER BY close_time
                """
            ).fetchall()
        finally:
            conn.close()

        wins = 0
        losses = 0

        for row in rows:

            record = validate_closed_trade_record(
                dict(row)
            )

            outcome = int(record["win_loss"])

            if outcome == 1:
                wins += 1
            elif outcome == 0:
                losses += 1
            else:
                raise RuntimeError(
                    "FAIL-CLOSED: Closed trade win_loss is invalid"
                )

        trades = len(rows)

        win_rate = (
            round(
                (wins / trades) * 100.0,
                2,
            )
            if trades
            else 0
        )

        return {
            "Trades": trades,
            "Wins": wins,
            "Losses": losses,
            "WinRate": win_rate,
        }
