from intelligence.live_broker_adapter import (
    LiveBrokerAdapter,
    LiveBrokerAdapterError,
)


class FakeTransport:
    def __init__(self):
        self.place_payload = None
        self.cancel_id = None
        self.details_id = None
        self.history_args = None
        self.place_response = {
            "status": "success",
            "data": {
                "order_ids": ["UPSTOX-ORDER-001"],
            },
        }
        self.cancel_response = {
            "status": "success",
            "data": {
                "order_id": "UPSTOX-ORDER-001",
            },
        }
        self.details_response = {
            "status": "success",
            "data": {
                "order_id": "UPSTOX-ORDER-001",
                "status": "complete",
                "quantity": 1,
                "filled_quantity": 1,
                "pending_quantity": 0,
                "average_price": 101.25,
                "instrument_token": "NSE_EQ|TEST001",
                "transaction_type": "BUY",
                "tag": "JGX-CLIENT-001",
                "exchange_order_id": "EXCHANGE-001",
            },
        }
        self.history_response = {
            "status": "success",
            "data": [
                {
                    "order_id": "UPSTOX-ORDER-001",
                    "status": "complete",
                    "tag": "JGX-CLIENT-001",
                }
            ],
        }
        self.positions_response = {
            "status": "success",
            "data": [
                {
                    "instrument_token": "NSE_EQ|TEST001",
                    "quantity": 1,
                    "product": "I",
                    "average_price": 101.25,
                }
            ],
        }

    def place_order(self, payload):
        self.place_payload = dict(payload)
        return self.place_response

    def cancel_order(self, order_id):
        self.cancel_id = order_id
        return self.cancel_response

    def get_order_details(self, order_id):
        self.details_id = order_id
        return self.details_response

    def get_order_history(self, order_id=None, tag=None):
        self.history_args = {
            "order_id": order_id,
            "tag": tag,
        }
        return self.history_response

    def get_positions(self):
        return self.positions_response


def valid_execution():
    return {
        "mode": "LIVE",
        "authorization_id": "AUTH-001",
        "client_order_id": "JGX-CLIENT-001",
        "symbol": "SBIN",
        "instrument_token": "NSE_EQ|TEST001",
        "decision": "ENTER_LONG",
        "position_size": 1,
        "entry": 100.0,
        "product": "I",
        "validity": "DAY",
        "order_type": "LIMIT",
        "trigger_price": 0,
        "slice": False,
        "market_protection": -1,
    }


fake = FakeTransport()
broker = LiveBrokerAdapter(transport=fake)

print("=== LIVE BROKER CONTRACT ===")

payload = broker.build_order_payload(valid_execution())

assert payload["quantity"] == 1
assert payload["transaction_type"] == "BUY"
assert payload["instrument_token"] == "NSE_EQ|TEST001"
assert payload["tag"] == "JGX-CLIENT-001"
assert payload["order_type"] == "LIMIT"
print("PAYLOAD_BUILD: PASS")

result = broker.submit_entry(valid_execution())

assert result["broker_order_id"] == "UPSTOX-ORDER-001"
assert result["status"] == "SUBMITTED"
assert result["requested_qty"] == 1
assert result["client_order_id"] == "JGX-CLIENT-001"
assert fake.place_payload["transaction_type"] == "BUY"
print("ORDER_PLACE_NORMALIZATION: PASS")

details = broker.get_order("UPSTOX-ORDER-001")

assert details["broker_order_id"] == "UPSTOX-ORDER-001"
assert details["status"] == "FILLED"
assert details["filled_qty"] == 1
assert details["remaining_qty"] == 0
assert details["average_fill_price"] == 101.25
assert details["tag"] == "JGX-CLIENT-001"
print("ORDER_DETAILS_NORMALIZATION: PASS")

history = broker.get_order_history(
    broker_order_id="UPSTOX-ORDER-001",
    client_order_id="JGX-CLIENT-001",
)

assert len(history) == 1
assert history[0]["order_id"] == "UPSTOX-ORDER-001"
assert fake.history_args["order_id"] == "UPSTOX-ORDER-001"
assert fake.history_args["tag"] == "JGX-CLIENT-001"
print("ORDER_HISTORY: PASS")

position = broker.get_position(
    "NSE_EQ|TEST001"
)

assert position["quantity"] == 1
print("POSITION_LOOKUP: PASS")

cancel = broker.cancel_entry(
    "UPSTOX-ORDER-001"
)

assert cancel["broker_order_id"] == "UPSTOX-ORDER-001"
assert cancel["status"] == "CANCELLED"
assert fake.cancel_id == "UPSTOX-ORDER-001"
print("CANCEL: PASS")

try:
    broker.close_position(
        "NSE_EQ|TEST001",
        1,
        101.25,
    )
except LiveBrokerAdapterError as exc:
    assert "not enabled" in str(exc)
    print("LIVE_CLOSE_FAIL_CLOSED: PASS")
else:
    raise AssertionError(
        "LIVE position close unexpectedly enabled"
    )

invalid = valid_execution()
invalid["mode"] = "PAPER"

try:
    broker.submit_entry(invalid)
except LiveBrokerAdapterError as exc:
    assert "mode=LIVE" in str(exc)
    print("PAPER_CONTRACT_FAIL_CLOSED: PASS")
else:
    raise AssertionError(
        "LIVE broker accepted PAPER contract"
    )

multi = valid_execution()
fake.place_response = {
    "status": "success",
    "data": {
        "order_ids": [
            "UPSTOX-ORDER-001",
            "UPSTOX-ORDER-002",
        ],
    },
}

try:
    broker.submit_entry(multi)
except LiveBrokerAdapterError as exc:
    assert "multiple broker order IDs" in str(exc)
    print("MULTI_ORDER_FAIL_CLOSED: PASS")
else:
    raise AssertionError(
        "Sliced multi-order response was accepted as one order"
    )

print("LIVE_BROKER_CONTRACT: PASS")

print("=== STRICT BOOLEAN CONTRACT ===")

boolean_contract = valid_execution()
boolean_contract["is_amo"] = "false"
boolean_contract["slice"] = "false"

payload = broker.build_order_payload(boolean_contract)

assert payload["is_amo"] is False
assert payload["slice"] is False
print("STRING_FALSE_NORMALIZATION: PASS")

boolean_contract["slice"] = "true"

payload = broker.build_order_payload(boolean_contract)

assert payload["slice"] is True
print("STRING_TRUE_NORMALIZATION: PASS")

boolean_contract["slice"] = "FALSE "

payload = broker.build_order_payload(boolean_contract)

assert payload["slice"] is False
print("WHITESPACE_BOOLEAN_NORMALIZATION: PASS")

boolean_contract["slice"] = "not-a-bool"

try:
    broker.build_order_payload(boolean_contract)
except LiveBrokerAdapterError as exc:
    assert "slice" in str(exc)
    print("INVALID_BOOLEAN_FAIL_CLOSED: PASS")
else:
    raise AssertionError(
        "Invalid slice boolean was accepted"
    )

print("STRICT_BOOLEAN_CONTRACT: PASS")

print("=== RECOVERY OBSERVATION CONTRACT ===")

observation_intent = {
    "authorization_id": "AUTH-001",
    "client_order_id": "JGX-CLIENT-001",
    "broker_order_id": "UPSTOX-ORDER-001",
    "symbol": "SBIN",
    "decision": "LONG",
    "instrument_token": "NSE_EQ|TEST001",
}

observed = broker.observe_order(
    observation_intent
)

assert observed["authorization_id"] == "AUTH-001"
assert observed["client_order_id"] == "JGX-CLIENT-001"
assert observed["broker_order_id"] == "UPSTOX-ORDER-001"
assert observed["symbol"] == "SBIN"
assert observed["side"] == "BUY"
assert observed["status"] == "FILLED"
assert observed["requested_qty"] == 1
assert observed["filled_qty"] == 1

print("RECOVERY_OBSERVATION: PASS")

bad_intent = dict(observation_intent)
bad_intent["client_order_id"] = "WRONG-CLIENT"

try:
    broker.observe_order(bad_intent)
except LiveBrokerAdapterError as exc:
    assert "client order identity" in str(exc).lower()
    print("CLIENT_ID_MISMATCH_FAIL_CLOSED: PASS")
else:
    raise AssertionError(
        "Mismatched client identity was accepted"
    )

bad_intent = dict(observation_intent)
bad_intent["instrument_token"] = "NSE_EQ|WRONG"

try:
    broker.observe_order(bad_intent)
except LiveBrokerAdapterError as exc:
    assert "instrument identity" in str(exc).lower()
    print("INSTRUMENT_MISMATCH_FAIL_CLOSED: PASS")
else:
    raise AssertionError(
        "Mismatched instrument identity was accepted"
    )

bad = valid_execution()
bad["market_protection"] = "invalid"

try:
    broker.build_order_payload(bad)
except LiveBrokerAdapterError as exc:
    assert "market_protection" in str(exc)
    print("MARKET_PROTECTION_TYPE_FAIL_CLOSED: PASS")
else:
    raise AssertionError(
        "Invalid market_protection was accepted"
    )

bad = valid_execution()
bad["order_type"] = "SL"
bad["trigger_price"] = 0

try:
    broker.build_order_payload(bad)
except LiveBrokerAdapterError as exc:
    assert "trigger_price" in str(exc)
    print("STOP_TRIGGER_FAIL_CLOSED: PASS")
else:
    raise AssertionError(
        "Zero stop trigger was accepted"
    )

print("RECOVERY_OBSERVATION_CONTRACT: PASS")
