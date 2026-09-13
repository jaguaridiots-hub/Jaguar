from __future__ import annotations

import pytest

from core.account_read_model import (
    AccountReadModelError,
    build_account_snapshot,
)
from market.upstox_order_transport import (
    UpstoxOrderTransport,
    UpstoxOrderTransportError,
)


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


def test_get_funds_and_margin_uses_read_endpoint():
    session = FakeSession({
        "status": "success",
        "data": {
            "equity": {
                "available_margin": 90000.0,
                "used_margin": 10000.0,
                "payin_amount": 5000.0,
                "notional_cash": 95000.0,
            }
        },
    })

    transport = UpstoxOrderTransport(
        access_token="TEST_TOKEN",
        session=session,
    )

    response = transport.get_funds_and_margin("SEC")

    assert response["status"] == "success"
    assert session.calls[0]["url"] == (
        "https://api.upstox.com"
        "/v2/user/get-funds-and-margin"
    )
    assert session.calls[0]["params"] == {"segment": "SEC"}


def test_get_funds_and_margin_rejects_invalid_segment():
    transport = UpstoxOrderTransport(
        access_token="TEST_TOKEN",
        session=FakeSession({}),
    )

    with pytest.raises(
        UpstoxOrderTransportError,
        match="segment must be SEC or COM",
    ):
        transport.get_funds_and_margin("INVALID")


def test_account_read_model_normalizes_payload():
    transport = UpstoxOrderTransport(
        access_token="TEST_TOKEN",
        session=FakeSession({
            "status": "success",
            "data": {
                "equity": {
                    "available_margin": 90000,
                    "used_margin": 10000,
                    "payin_amount": 5000,
                    "notional_cash": 95000,
                }
            },
        }),
    )

    snapshot = build_account_snapshot(
        transport=transport,
        segment="SEC",
    )

    assert snapshot == {
        "authority": "UPSTOX_FUND_AND_MARGIN_API",
        "status": "AVAILABLE",
        "available_margin": 90000.0,
        "used_margin": 10000.0,
        "payin_amount": 5000.0,
        "notional_cash": 95000.0,
        "segment": "SEC",
        "freshness": "CURRENT",
    }


def test_account_read_model_does_not_fabricate_equity():
    transport = UpstoxOrderTransport(
        access_token="TEST_TOKEN",
        session=FakeSession({
            "status": "success",
            "data": {
                "equity": {
                    "available_margin": 70000,
                }
            },
        }),
    )

    snapshot = build_account_snapshot(
        transport=transport,
    )

    assert snapshot["available_margin"] == 70000.0
    assert "equity" not in snapshot
    assert "cash_balance" not in snapshot


def test_account_read_model_rejects_malformed_payload():
    transport = UpstoxOrderTransport(
        access_token="TEST_TOKEN",
        session=FakeSession({
            "status": "success",
            "data": [],
        }),
    )

    with pytest.raises(AccountReadModelError):
        build_account_snapshot(
            transport=transport,
        )
