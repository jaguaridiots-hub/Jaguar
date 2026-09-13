from core.broker_position_read_model import (
    BrokerPositionReadModelError,
    build_broker_position_snapshot,
)


class FakeAdapter:
    def __init__(self, positions):
        self.positions = positions
        self.calls = 0

    def get_positions(self):
        self.calls += 1
        return self.positions


def test_normalizes_authoritative_upstox_position_fields():
    adapter = FakeAdapter([
        {
            "instrument_token": "MCX_FO|GOLDM_TEST",
            "trading_symbol": "GOLDM",
            "quantity": 2,
            "average_price": 5867.0,
            "pnl": 6005.0,
            "unrealised": 100.0,
            "realised": 5905.0,
            "last_price": 6005.0,
            "value": 5867.0,
            "exchange": "MCX",
            "product": "D",
        }
    ])

    result = build_broker_position_snapshot(
        adapter=adapter
    )

    assert adapter.calls == 1
    assert result["authority"] == (
        "UPSTOX_SHORT_TERM_POSITIONS"
    )
    assert result["status"] == "AVAILABLE"
    assert result["freshness"] == "CURRENT"
    assert result["quantity_source"] == (
        "UPSTOX_POSITION_API"
    )

    assert result["positions"] == [{
        "instrument_token": "MCX_FO|GOLDM_TEST",
        "broker_symbol": "GOLDM",
        "quantity": 2.0,
        "average_price": 5867.0,
        "pnl": 6005.0,
        "unrealised_pnl": 100.0,
        "realised_pnl": 5905.0,
        "last_price": 6005.0,
        "value": 5867.0,
        "exchange": "MCX",
        "product": "D",
    }]


def test_zero_quantity_positions_are_not_open_positions():
    adapter = FakeAdapter([
        {
            "instrument_token": "NSE_EQ|ZERO",
            "quantity": 0,
            "pnl": 0,
        },
        {
            "instrument_token": "NSE_EQ|LIVE",
            "quantity": 5,
            "pnl": 10,
        },
    ])

    result = build_broker_position_snapshot(
        adapter=adapter
    )

    assert len(result["positions"]) == 1
    assert result["positions"][0]["instrument_token"] == (
        "NSE_EQ|LIVE"
    )


def test_missing_instrument_identity_fails_closed():
    adapter = FakeAdapter([
        {
            "quantity": 5,
        }
    ])

    import pytest

    with pytest.raises(BrokerPositionReadModelError):
        build_broker_position_snapshot(
            adapter=adapter
        )


def test_negative_quantity_fails_closed():
    adapter = FakeAdapter([
        {
            "instrument_token": "NSE_EQ|BAD",
            "quantity": -5,
        }
    ])

    import pytest

    with pytest.raises(BrokerPositionReadModelError):
        build_broker_position_snapshot(
            adapter=adapter
        )


def test_read_model_never_exposes_authorization_id():
    adapter = FakeAdapter([
        {
            "instrument_token": "NSE_EQ|SAFE",
            "quantity": 1,
            "authorization_id": "MUST-NOT-LEAK",
        }
    ])

    result = build_broker_position_snapshot(
        adapter=adapter
    )

    assert "authorization_id" not in str(result)
