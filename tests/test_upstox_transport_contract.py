"""
Jaguar Quant X Enterprise
Upstox Transport Contract v1

Purpose:
Prove deterministic Upstox request construction using a
fully synthetic HTTP session.

No real credential is required.
No network request is executed.
"""

from market.upstox_transport import (
    UpstoxTransport,
    UpstoxTransportError,
)


TEST_TOKEN = "JAGUAR_TEST_TOKEN_DO_NOT_USE"


class FakeResponse:

    def __init__(
        self,
        payload,
    ):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class FakeSession:

    def __init__(self):
        self.calls = []

    def get(
        self,
        url,
        headers=None,
        params=None,
        timeout=None,
    ):
        self.calls.append(
            {
                "url": url,
                "headers": dict(
                    headers or {}
                ),
                "params": (
                    dict(params)
                    if params is not None
                    else None
                ),
                "timeout": timeout,
            }
        )

        return FakeResponse(
            {
                "status": "success",
                "data": {
                    "synthetic": True,
                },
            }
        )


def main():

    failures = []

    session = FakeSession()

    transport = UpstoxTransport(
        access_token=TEST_TOKEN,
        session=session,
        timeout=7,
    )

    # ======================================================
    # INSTRUMENT SEARCH REQUEST
    # ======================================================

    payload = transport.search_instruments(
        query="GOLDM",
        exchange="MCX",
        segment="MCX_FO",
        instrument_type="FUT",
    )

    if payload.get("status") != "success":

        failures.append(
            {
                "contract": "SEARCH_PAYLOAD",
                "actual": payload,
            }
        )

    search_call = session.calls[-1]

    if search_call["url"] != (
        "https://api.upstox.com"
        "/instruments/search"
    ):

        failures.append(
            {
                "contract": "SEARCH_URL",
                "actual": search_call["url"],
            }
        )

    expected_params = {
        "query": "GOLDM",
        "exchange": "MCX",
        "segment": "MCX_FO",
        "instrument_type": "FUT",
    }

    if search_call["params"] != expected_params:

        failures.append(
            {
                "contract": "SEARCH_PARAMS",
                "expected": expected_params,
                "actual": search_call["params"],
            }
        )

    # ======================================================
    # HISTORICAL V3 REQUEST
    # ======================================================

    transport.historical_candles(
        instrument_key="MCX_FO|GOLDM_AUG",
        unit="minutes",
        interval=15,
        to_date="2026-07-14",
        from_date="2026-07-01",
    )

    historical_call = session.calls[-1]

    expected_historical_url = (
        "https://api.upstox.com"
        "/v3/historical-candle/"
        "MCX_FO%7CGOLDM_AUG/"
        "minutes/15/"
        "2026-07-14/"
        "2026-07-01"
    )

    if (
        historical_call["url"]
        != expected_historical_url
    ):

        failures.append(
            {
                "contract": "HISTORICAL_URL",
                "expected": expected_historical_url,
                "actual": historical_call["url"],
            }
        )

    # ======================================================
    # INTRADAY V3 REQUEST
    # ======================================================

    transport.intraday_candles(
        instrument_key="NSE_EQ|INE848E01016",
        unit="hours",
        interval=4,
    )

    intraday_call = session.calls[-1]

    expected_intraday_url = (
        "https://api.upstox.com"
        "/v3/historical-candle/intraday/"
        "NSE_EQ%7CINE848E01016/"
        "hours/4"
    )

    if (
        intraday_call["url"]
        != expected_intraday_url
    ):

        failures.append(
            {
                "contract": "INTRADAY_URL",
                "expected": expected_intraday_url,
                "actual": intraday_call["url"],
            }
        )

    # ======================================================
    # HEADER / TIMEOUT CONTRACT
    # ======================================================

    for call in session.calls:

        headers = call["headers"]

        if headers.get("Accept") != (
            "application/json"
        ):

            failures.append(
                {
                    "contract": "ACCEPT_HEADER",
                    "actual": headers,
                }
            )

        if headers.get("Authorization") != (
            f"Bearer {TEST_TOKEN}"
        ):

            failures.append(
                {
                    "contract": "AUTHORIZATION_HEADER",
                    "actual": headers,
                }
            )

        if call["timeout"] != 7.0:

            failures.append(
                {
                    "contract": "TIMEOUT",
                    "actual": call["timeout"],
                }
            )

    # ======================================================
    # FAIL-CLOSED INPUTS
    # ======================================================

    try:

        transport.search_instruments(
            query="   "
        )

    except UpstoxTransportError:
        pass

    else:

        failures.append(
            {
                "contract": "EMPTY_SEARCH_FAIL_CLOSED",
                "actual": "SEARCH ALLOWED",
            }
        )

    try:

        transport.intraday_candles(
            instrument_key="",
            unit="minutes",
            interval=15,
        )

    except UpstoxTransportError:
        pass

    else:

        failures.append(
            {
                "contract": "EMPTY_KEY_FAIL_CLOSED",
                "actual": "REQUEST ALLOWED",
            }
        )

    # ======================================================
    # NETWORK IS SYNTHETIC
    # ======================================================

    if len(session.calls) != 3:

        failures.append(
            {
                "contract": "SYNTHETIC_CALL_COUNT",
                "expected": 3,
                "actual": len(session.calls),
            }
        )

    # ======================================================
    # RESULT
    # ======================================================

    if failures:

        print(
            "UPSTOX_TRANSPORT_CONTRACT: FAIL"
        )

        for failure in failures:

            print(
                "FAIL:",
                failure,
            )

        raise AssertionError(
            "Upstox transport contract violated"
        )

    print(
        "UPSTOX_TRANSPORT_CONTRACT: PASS"
    )

    print(
        "Synthetic GET calls:",
        len(session.calls),
    )

    print(
        "Historical V3 routing: PASS"
    )

    print(
        "Intraday V3 routing: PASS"
    )

    print(
        "Instrument search routing: PASS"
    )

    print(
        "Bearer authorization: PASS"
    )

    print(
        "Network required: NO"
    )


if __name__ == "__main__":
    main()
