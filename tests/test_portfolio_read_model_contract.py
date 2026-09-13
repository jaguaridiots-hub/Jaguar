from unittest.mock import patch

import pytest

from core import portfolio_read_model as prm


def test_portfolio_reader_has_no_write_sql():
    source = open(
        "core/portfolio_read_model.py",
        encoding="utf-8",
    ).read()

    assert "INSERT INTO" not in source
    assert "UPDATE " not in source
    assert "DELETE FROM" not in source
    assert ".commit()" not in source


def test_empty_open_trade_set_is_available():
    with patch.object(prm, "_open_trades", return_value=[]):
        result = prm.build_portfolio_snapshot()

    assert result["status"] == "AVAILABLE"
    assert result["positions"] == []
    assert result["equity"] is None
    assert result["available_cash"] is None
    assert result["realized_pnl"] is None
    assert result["unrealized_pnl"] is None


def test_net_quantity_uses_signed_filled_quantity():
    trade = {
        "uuid": "TRADE-1",
        "symbol": "BTCUSDT",
        "timeframe": "15m",
        "mode": "SWING",
        "entry_price": 100.0,
        "stop_loss": 95.0,
        "take_profit": 110.0,
        "status": "OPEN",
        "close_time": None,
    }

    orders = [
        {
            "transaction_type": "BUY",
            "filled_qty": 100.0,
            "status": "FILLED",
        },
        {
            "transaction_type": "SELL",
            "filled_qty": 40.0,
            "status": "FILLED",
        },
    ]

    with patch.object(
        prm,
        "_execution_orders",
        return_value=orders,
    ):
        result = prm._project_trade(trade)

    assert result.quantity == pytest.approx(60.0)
    assert result.side == "LONG"
    assert result.entry_price == 100.0
    assert result.quantity_source == "EXECUTION_ORDERS"


def test_non_filled_orders_do_not_count():
    trade = {
        "uuid": "TRADE-2",
        "symbol": "BTCUSDT",
        "timeframe": "15m",
        "mode": "SWING",
        "entry_price": 100.0,
        "status": "OPEN",
        "close_time": None,
    }

    orders = [
        {
            "transaction_type": "BUY",
            "filled_qty": 100.0,
            "status": "SUBMITTED",
        },
    ]

    with patch.object(
        prm,
        "_execution_orders",
        return_value=orders,
    ):
        with pytest.raises(prm.PortfolioReadModelError):
            prm._project_trade(trade)
