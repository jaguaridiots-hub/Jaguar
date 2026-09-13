from core.canonical_portfolio_read_model import (
    build_canonical_portfolio_snapshot,
)


def jaguar_snapshot():
    return {
        "authority": "JAGUAR_EXECUTION_DATABASE",
        "status": "AVAILABLE",
        "positions": [{
            "symbol": "GOLDM",
            "timeframe": "15m",
            "mode": "SWING",
            "trade_uuid": "TRADE-1",
            "instrument_token": "MCX_FO|GOLDM_TEST",
            "side": "LONG",
            "quantity": 2.0,
            "entry_price": 5867.0,
            "stop_loss": 5800.0,
            "take_profit": 6000.0,
            "quantity_source": "EXECUTION_ORDERS",
            "status": "OPEN",
        }],
        "realized_pnl": None,
        "unrealized_pnl": None,
        "equity": None,
        "available_cash": None,
        "freshness": "CURRENT",
        "quantity_source": "EXECUTION_ORDERS",
    }


def broker_snapshot():
    return {
        "authority": "UPSTOX_SHORT_TERM_POSITIONS",
        "status": "AVAILABLE",
        "positions": [{
            "instrument_token": "MCX_FO|GOLDM_TEST",
            "broker_symbol": "GOLDM",
            "quantity": 2.0,
            "average_price": 5867.0,
            "pnl": 10.0,
            "unrealised_pnl": 10.0,
            "realised_pnl": 0.0,
            "last_price": 5872.0,
            "value": 11744.0,
            "exchange": "MCX",
            "product": "D",
        }],
        "freshness": "CURRENT",
        "quantity_source": "UPSTOX_POSITION_API",
    }


def account_snapshot():
    return {
        "authority": "UPSTOX_FUND_AND_MARGIN_V3",
        "status": "AVAILABLE",
        "available_to_trade": 50000.0,
        "cash_available_to_trade": 49000.0,
        "pledge_available_to_trade": 1000.0,
        "cash_margin_used": 500.0,
        "pledge_margin_used": 0.0,
        "unsettled_profit_today": 0.0,
        "unsettled_profit_previous_days": 0.0,
        "freshness": "CURRENT",
    }


def test_matching_positions_are_reported():
    result = build_canonical_portfolio_snapshot(
        portfolio_reader=jaguar_snapshot,
        broker_reader=broker_snapshot,
        account_reader=account_snapshot,
    )

    assert result["status"] == "AVAILABLE"
    assert result["reconciliation"]["status"] == "MATCH"
    assert len(result["reconciliation"]["matches"]) == 1
    assert result["account"]["available_to_trade"] == 50000.0
    assert "authorization_id" not in str(result)


def test_quantity_mismatch_is_not_silently_resolved():
    broker = broker_snapshot()
    broker["positions"][0]["quantity"] = 3.0

    result = build_canonical_portfolio_snapshot(
        portfolio_reader=jaguar_snapshot,
        broker_reader=lambda: broker,
        account_reader=account_snapshot,
    )

    assert result["status"] == "RECONCILIATION_MISMATCH"
    assert result["reconciliation"]["status"] == "MISMATCH"


def test_broker_only_position_is_explicit():
    broker = broker_snapshot()
    broker["positions"].append({
        "instrument_token": "NSE_EQ|EXTRA",
        "broker_symbol": "EXTRA",
        "quantity": 5.0,
        "average_price": 100.0,
        "pnl": 0.0,
        "unrealised_pnl": 0.0,
        "realised_pnl": 0.0,
        "last_price": 100.0,
        "value": 500.0,
        "exchange": "NSE",
        "product": "D",
    })

    result = build_canonical_portfolio_snapshot(
        portfolio_reader=jaguar_snapshot,
        broker_reader=lambda: broker,
        account_reader=account_snapshot,
    )

    assert result["reconciliation"]["status"] == "MISMATCH"
    assert result["reconciliation"]["unmatched_broker_positions"][0][
        "status"
    ] == "BROKER_POSITION_WITHOUT_JAGUAR"


def test_broker_unavailable_is_fail_closed():
    from core.broker_position_read_model import (
        BrokerPositionReadModelError,
    )

    def unavailable():
        raise BrokerPositionReadModelError("unavailable")

    result = build_canonical_portfolio_snapshot(
        portfolio_reader=jaguar_snapshot,
        broker_reader=unavailable,
        account_reader=account_snapshot,
    )

    assert result["status"] == "BROKER_UNAVAILABLE"
    assert result["reconciliation"]["status"] == "BROKER_UNAVAILABLE"


def test_account_unavailable_does_not_create_cash_values():
    from core.account_read_model import AccountReadModelError

    def unavailable():
        raise AccountReadModelError("unavailable")

    result = build_canonical_portfolio_snapshot(
        portfolio_reader=jaguar_snapshot,
        broker_reader=broker_snapshot,
        account_reader=unavailable,
    )

    assert result["status"] == "ACCOUNT_UNAVAILABLE"
    assert result["account"]["available_to_trade"] is None
    assert result["account"]["cash_available_to_trade"] is None


def test_invalid_jaguar_identity_is_unreconcilable():
    bad = jaguar_snapshot()
    bad["positions"][0] = dict(bad["positions"][0])
    bad["positions"][0]["instrument_token"] = None

    result = build_canonical_portfolio_snapshot(
        portfolio_reader=lambda: bad,
        broker_reader=broker_snapshot,
        account_reader=account_snapshot,
    )

    assert result["status"] == "RECONCILIATION_MISMATCH"
    assert result["reconciliation"]["status"] == "UNRECONCILABLE"
