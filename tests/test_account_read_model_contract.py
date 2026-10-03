from __future__ import annotations

import pytest

from core.account_read_model import (
    AccountReadModelError,
    build_account_snapshot,
)
from market.upstox_order_transport import UpstoxOrderTransport


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def get(self, url, headers, params, timeout):
        self.calls.append({
            "url": url,
            "headers": headers,
            "params": params,
            "timeout": timeout,
        })
        return FakeResponse(self.payload)


def v3_payload():
    return {
        "status": "success",
        "data": {
            "available_to_trade": {
                "total": 5379.03,
                "cash_available_to_trade": {
                    "total": 5117.34,
                    "margin_used": {
                        "total": 0.0,
                    },
                },
                "pledge_available_to_trade": {
                    "total": 261.69,
                    "margin_used": {
                        "total": 1.8,
                    },
                },
            },
            "unavailable_to_trade": {
                "cash_unavailable_to_trade": {
                    "unsettled_profit": {
                        "todays_profit": 12.5,
                        "previous_days": -3.5,
                    },
                },
                "pledge_unavailable_to_trade": {
                    "equity": 0.0,
                    "mutual_funds": 0.0,
                },
            },
        },
    }


def test_v3_transport_uses_current_endpoint_and_api_version():
    session = FakeSession(v3_payload())

    transport = UpstoxOrderTransport(
        access_token="TEST_TOKEN",
        session=session,
    )

    response = transport.get_funds_and_margin_v3()

    assert response["status"] == "success"
    assert session.calls[0]["url"] == (
        "https://api.upstox.com"
        "/v3/user/get-funds-and-margin"
    )
    assert session.calls[0]["params"] is None
    assert session.calls[0]["headers"]["Api-Version"] == "3.0"
    assert (
        session.calls[0]["headers"]["Authorization"]
        == "Bearer TEST_TOKEN"
    )


def test_account_read_model_normalizes_v3():
    transport = UpstoxOrderTransport(
        access_token="TEST_TOKEN",
        session=FakeSession(v3_payload()),
    )

    result = build_account_snapshot(
        transport=transport,
    )

    assert result == {
        "authority": "UPSTOX_FUND_AND_MARGIN_V3",
        "status": "AVAILABLE",
        "available_to_trade": 5379.03,
        "cash_available_to_trade": 5117.34,
        "pledge_available_to_trade": 261.69,
        "cash_margin_used": 0.0,
        "pledge_margin_used": 1.8,
        "unsettled_profit_today": 12.5,
        "unsettled_profit_previous_days": -3.5,
        "freshness": "CURRENT",
    }


def test_v3_model_does_not_fabricate_equity_or_cash_balance():
    transport = UpstoxOrderTransport(
        access_token="TEST_TOKEN",
        session=FakeSession(v3_payload()),
    )

    result = build_account_snapshot(
        transport=transport,
    )

    assert "equity" not in result
    assert "cash_balance" not in result
    assert "available_margin" not in result
    assert "notional_cash" not in result


def test_v3_model_rejects_missing_available_to_trade():
    payload = v3_payload()
    payload["data"].pop("available_to_trade")

    transport = UpstoxOrderTransport(
        access_token="TEST_TOKEN",
        session=FakeSession(payload),
    )

    with pytest.raises(AccountReadModelError):
        build_account_snapshot(
            transport=transport,
        )


def test_v3_model_rejects_non_finite_values():
    payload = v3_payload()
    payload["data"]["available_to_trade"]["total"] = "nan"

    transport = UpstoxOrderTransport(
        access_token="TEST_TOKEN",
        session=FakeSession(payload),
    )

    with pytest.raises(AccountReadModelError):
        build_account_snapshot(
            transport=transport,
        )
