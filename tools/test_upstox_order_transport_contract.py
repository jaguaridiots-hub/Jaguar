from market.upstox_order_transport import (
    UpstoxOrderTransport,
    UpstoxOrderTransportError,
)


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests
            raise requests.HTTPError(
                f"HTTP {self.status_code}"
            )

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self):
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append(
            ("POST", url, kwargs)
        )
        return FakeResponse({
            "status": "success",
            "data": {
                "order_ids": [
                    "ORDER-POST-001"
                ]
            },
        })

    def delete(self, url, **kwargs):
        self.calls.append(
            ("DELETE", url, kwargs)
        )
        return FakeResponse({
            "status": "success",
            "data": {
                "order_id": "ORDER-POST-001"
            },
        })

    def get(self, url, **kwargs):
        self.calls.append(
            ("GET", url, kwargs)
        )
        return FakeResponse({
            "status": "success",
            "data": [],
        })


session = FakeSession()

transport = UpstoxOrderTransport(
    access_token="TEST-TOKEN-NOT-REAL",
    session=session,
    timeout=7.5,
)

print("=== UPSTOX ORDER TRANSPORT ===")

place = transport.place_order({
    "quantity": 1,
    "product": "I",
    "validity": "DAY",
    "price": 100.0,
    "tag": "TEST",
    "instrument_token": "NSE_EQ|TEST001",
    "order_type": "LIMIT",
    "transaction_type": "BUY",
    "disclosed_quantity": 0,
    "trigger_price": 0,
    "is_amo": False,
    "slice": False,
})

assert place["data"]["order_ids"] == ["ORDER-POST-001"]
method, url, kwargs = session.calls[-1]

assert method == "POST"
assert url == (
    "https://api-hft.upstox.com/v3/order/place"
)
assert kwargs["timeout"] == 7.5
assert kwargs["headers"]["Authorization"] == (
    "Bearer TEST-TOKEN-NOT-REAL"
)
assert kwargs["json"]["quantity"] == 1

print("PLACE_ROUTE: PASS")

cancel = transport.cancel_order(
    "ORDER-POST-001"
)

assert cancel["data"]["order_id"] == "ORDER-POST-001"

method, url, kwargs = session.calls[-1]

assert method == "DELETE"
assert url == (
    "https://api-hft.upstox.com/v3/order/cancel"
)
assert kwargs["params"] == {
    "order_id": "ORDER-POST-001"
}

print("CANCEL_ROUTE: PASS")

details = transport.get_order_details(
    "ORDER-POST-001"
)

assert details["status"] == "success"

method, url, kwargs = session.calls[-1]

assert method == "GET"
assert url == (
    "https://api.upstox.com/v2/order/details"
)
assert kwargs["params"] == {
    "order_id": "ORDER-POST-001"
}

print("ORDER_DETAILS_ROUTE: PASS")

history = transport.get_order_history(
    order_id="ORDER-POST-001",
    tag="TEST-TAG",
)

assert history["status"] == "success"

method, url, kwargs = session.calls[-1]

assert method == "GET"
assert url == (
    "https://api.upstox.com/v2/order/history"
)
assert kwargs["params"] == {
    "order_id": "ORDER-POST-001",
    "tag": "TEST-TAG",
}

print("ORDER_HISTORY_ROUTE: PASS")

positions = transport.get_positions()

assert positions["status"] == "success"

method, url, kwargs = session.calls[-1]

assert method == "GET"
assert url == (
    "https://api.upstox.com/v2/portfolio/short-term-positions"
)

print("POSITIONS_ROUTE: PASS")

try:
    transport.cancel_order("")
except UpstoxOrderTransportError as exc:
    assert "order_id" in str(exc)
    print("INVALID_CANCEL_ID_FAIL_CLOSED: PASS")
else:
    raise AssertionError(
        "Invalid cancel order ID was accepted"
    )

try:
    UpstoxOrderTransport(
        access_token="",
        session=session,
    )
except UpstoxOrderTransportError as exc:
    assert "access token" in str(exc).lower()
    print("EMPTY_CREDENTIAL_FAIL_CLOSED: PASS")
else:
    raise AssertionError(
        "Empty access token was accepted"
    )

print("UPSTOX_ORDER_TRANSPORT: PASS")
