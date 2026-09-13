"""Read-only portfolio projection from durable execution state."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import isfinite
from typing import Any

from research import database as db


class PortfolioReadModelError(RuntimeError):
    """Raised when the durable portfolio projection cannot be trusted."""


@dataclass(frozen=True)
class PortfolioPosition:
    symbol: str
    timeframe: str
    mode: str
    trade_uuid: str
    side: str
    quantity: float
    entry_price: float | None
    stop_loss: float | None
    take_profit: float | None
    quantity_source: str
    status: str


@dataclass(frozen=True)
class PortfolioSnapshot:
    authority: str
    status: str
    positions: tuple[PortfolioPosition, ...]
    realized_pnl: float | None
    unrealized_pnl: float | None
    equity: float | None
    available_cash: float | None
    freshness: str
    quantity_source: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "authority": self.authority,
            "status": self.status,
            "positions": [
                asdict(position)
                for position in self.positions
            ],
            "realized_pnl": self.realized_pnl,
            "unrealized_pnl": self.unrealized_pnl,
            "equity": self.equity,
            "available_cash": self.available_cash,
            "freshness": self.freshness,
            "quantity_source": self.quantity_source,
        }


def _value(row: Any, key: str, default: Any = None) -> Any:
    try:
        value = row[key]
    except (KeyError, IndexError, TypeError):
        return default
    return default if value is None else value


def _quantity(value: Any) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise PortfolioReadModelError(
            "Invalid filled_qty in execution database"
        ) from exc

    if not isfinite(result) or result < 0:
        raise PortfolioReadModelError(
            "Invalid filled_qty in execution database"
        )

    return result


def _open_trades():
    conn = db.get_connection()
    try:
        return conn.execute(
            """
            SELECT
                uuid,
                symbol,
                timeframe,
                mode,
                entry_price,
                stop_loss,
                take_profit,
                status,
                close_time
            FROM trades
            WHERE status = 'OPEN'
              AND close_time IS NULL
            ORDER BY open_time ASC, uuid ASC
            """
        ).fetchall()
    finally:
        conn.close()


def _execution_orders(trade_uuid: str):
    conn = db.get_connection()
    try:
        return conn.execute(
            """
            SELECT
                transaction_type,
                filled_qty,
                status
            FROM execution_orders
            WHERE trade_uuid = ?
            ORDER BY child_index ASC
            """,
            (trade_uuid,),
        ).fetchall()
    finally:
        conn.close()


def _project_trade(trade: Any) -> PortfolioPosition:
    trade_uuid = str(_value(trade, "uuid", "")).strip()
    symbol = str(_value(trade, "symbol", "")).strip()
    timeframe = str(_value(trade, "timeframe", "")).strip()
    mode = str(_value(trade, "mode", "")).strip().upper()

    if not trade_uuid or not symbol or not timeframe or not mode:
        raise PortfolioReadModelError(
            "Open trade is missing required identity fields"
        )

    net_quantity = 0.0
    any_filled = False

    for order in _execution_orders(trade_uuid):
        if str(_value(order, "status", "")).strip().upper() != "FILLED":
            continue

        transaction_type = str(
            _value(order, "transaction_type", "")
        ).strip().upper()

        if transaction_type not in {"BUY", "SELL"}:
            raise PortfolioReadModelError(
                f"Invalid transaction_type for trade {trade_uuid}"
            )

        filled_qty = _quantity(_value(order, "filled_qty", 0.0))

        if filled_qty == 0:
            continue

        any_filled = True

        if transaction_type == "BUY":
            net_quantity += filled_qty
        else:
            net_quantity -= filled_qty

    if not any_filled or abs(net_quantity) <= 1e-12:
        raise PortfolioReadModelError(
            f"Open trade {trade_uuid} has no positive net executed quantity"
        )

    side = "LONG" if net_quantity > 0 else "SHORT"

    entry_price = _value(trade, "entry_price")
    stop_loss = _value(trade, "stop_loss")
    take_profit = _value(trade, "take_profit")

    return PortfolioPosition(
        symbol=symbol,
        timeframe=timeframe,
        mode=mode,
        trade_uuid=trade_uuid,
        side=side,
        quantity=abs(net_quantity),
        entry_price=(
            float(entry_price)
            if entry_price is not None
            else None
        ),
        stop_loss=(
            float(stop_loss)
            if stop_loss is not None
            else None
        ),
        take_profit=(
            float(take_profit)
            if take_profit is not None
            else None
        ),
        quantity_source="EXECUTION_ORDERS",
        status="OPEN",
    )


def build_portfolio_snapshot() -> dict[str, Any]:
    """Return a strictly read-only projection of active portfolio positions."""

    try:
        positions = tuple(
            _project_trade(trade)
            for trade in _open_trades()
        )

        return PortfolioSnapshot(
            authority="JAGUAR_EXECUTION_DATABASE",
            status="AVAILABLE",
            positions=positions,
            realized_pnl=None,
            unrealized_pnl=None,
            equity=None,
            available_cash=None,
            freshness="CURRENT",
            quantity_source="EXECUTION_ORDERS",
        ).to_dict()

    except PortfolioReadModelError:
        raise
    except Exception as exc:
        raise PortfolioReadModelError(
            "Portfolio read model unavailable"
        ) from exc
