from intelligence.live_broker_adapter import LiveBrokerAdapter, LiveBrokerAdapterError


class FakeTransport:
    def __init__(self, order_ids=None):
        self.order_ids = (
            ["PROTECT-001"]
            if order_ids is None
            else list(order_ids)
        )
        self.place_payload = None

    def place_order(self, payload):
        self.place_payload = dict(payload)
        return {
            "status": "success",
            "data": {
                "order_ids": list(self.order_ids),
            },
        }


def intent(decision="LONG"):
    return {
        "authorization_id": "AUTH-V9-D",
        "client_order_id": "CLIENT-V9-D",
        "symbol": "SBIN",
        "instrument_token": "NSE_EQ|TEST001",
        "decision": decision,
        "product": "I",
        "validity": "DAY",
        "is_amo": False,
    }


def protection(
    protection_type="STOP_LOSS",
    requested_price=95.0,
    requested_qty=10,
    target_index=0,
):
    return {
        "protection_type": protection_type,
        "requested_price": requested_price,
        "requested_qty": requested_qty,
        "target_index": target_index,
    }


def main():
    # LONG -> SELL stop-loss
    fake = FakeTransport()
    broker = LiveBrokerAdapter(transport=fake)

    result = broker.submit_protection(
        intent(),
        protection(),
    )

    assert result["broker_order_id"] == "PROTECT-001"
    assert result["transaction_type"] == "SELL"
    assert result["order_type"] == "SL-M"
    assert result["requested_qty"] == 10
    assert result["requested_price"] == 95.0
    assert fake.place_payload["transaction_type"] == "SELL"
    assert fake.place_payload["order_type"] == "SL-M"
    assert fake.place_payload["trigger_price"] == 95.0
    assert fake.place_payload["price"] == 0.0
    assert fake.place_payload["slice"] is False
    print("LIVE_PROTECTION_LONG_STOP: PASS")

    # LONG -> SELL take-profit
    fake = FakeTransport(["PROTECT-002"])
    broker = LiveBrokerAdapter(transport=fake)

    result = broker.submit_protection(
        intent(),
        protection(
            protection_type="TAKE_PROFIT",
            requested_price=110.0,
            target_index=0,
        ),
    )

    assert result["broker_order_id"] == "PROTECT-002"
    assert result["transaction_type"] == "SELL"
    assert result["order_type"] == "LIMIT"
    assert fake.place_payload["transaction_type"] == "SELL"
    assert fake.place_payload["order_type"] == "LIMIT"
    assert fake.place_payload["price"] == 110.0
    assert fake.place_payload["trigger_price"] == 0.0
    print("LIVE_PROTECTION_LONG_TARGET: PASS")

    # SHORT -> BUY stop-loss
    fake = FakeTransport(["PROTECT-003"])
    broker = LiveBrokerAdapter(transport=fake)

    result = broker.submit_protection(
        intent("SHORT"),
        protection(
            protection_type="STOP_LOSS",
            requested_price=105.0,
        ),
    )

    assert result["transaction_type"] == "BUY"
    assert fake.place_payload["transaction_type"] == "BUY"
    print("LIVE_PROTECTION_SHORT_STOP: PASS")

    # SHORT -> BUY take-profit
    fake = FakeTransport(["PROTECT-004"])
    broker = LiveBrokerAdapter(transport=fake)

    result = broker.submit_protection(
        intent("SHORT"),
        protection(
            protection_type="TAKE_PROFIT",
            requested_price=90.0,
        ),
    )

    assert result["transaction_type"] == "BUY"
    assert fake.place_payload["transaction_type"] == "BUY"
    print("LIVE_PROTECTION_SHORT_TARGET: PASS")

    # Multi-ID protection must fail closed.
    fake = FakeTransport(["PROTECT-005", "PROTECT-006"])
    broker = LiveBrokerAdapter(transport=fake)

    try:
        broker.submit_protection(
            intent(),
            protection(),
        )
    except LiveBrokerAdapterError as exc:
        assert "multiple broker order IDs" in str(exc)
        print("LIVE_PROTECTION_MULTI_ID_FAIL_CLOSED: PASS")
    else:
        raise AssertionError(
            "Multiple protection order IDs were accepted"
        )

    # Invalid direction must fail closed.
    bad = intent()
    bad["decision"] = "ENTER_LONG"

    try:
        broker.submit_protection(
            bad,
            protection(),
        )
    except LiveBrokerAdapterError:
        print("LIVE_PROTECTION_INVALID_DIRECTION_FAIL_CLOSED: PASS")
    else:
        raise AssertionError(
            "Invalid protection direction was accepted"
        )

    # Invalid quantity must fail closed.
    try:
        broker.submit_protection(
            intent(),
            protection(requested_qty=0),
        )
    except LiveBrokerAdapterError:
        print("LIVE_PROTECTION_ZERO_QTY_FAIL_CLOSED: PASS")
    else:
        raise AssertionError(
            "Zero protection quantity was accepted"
        )

    # Invalid requested price must fail closed.
    try:
        broker.submit_protection(
            intent(),
            protection(requested_price=0),
        )
    except LiveBrokerAdapterError:
        print("LIVE_PROTECTION_ZERO_PRICE_FAIL_CLOSED: PASS")
    else:
        raise AssertionError(
            "Zero protection price was accepted"
        )

    print("LIVE_PROTECTION_SUBMISSION_V9: PASS")


if __name__ == "__main__":
    main()
