from market.cache import MarketCache
from market.nse_provider import NSEProvider


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        import json
        return json.dumps(self._payload).encode("utf-8")


def yahoo_payload():
    timestamps = [
        1700000100,
        1700001000,
        1700001900,
    ]

    return {
        "chart": {
            "error": None,
            "result": [{
                "timestamp": timestamps,
                "indicators": {
                    "quote": [{
                        "open": [100, 101, 102],
                        "high": [101, 102, 103],
                        "low": [99, 100, 101],
                        "close": [100.5, 101.5, 102.5],
                        "volume": [1000, 1100, 1200],
                    }]
                },
            }],
        }
    }


def main():
    MarketCache.clear()

    calls = {"count": 0}

    def fake_opener(request, timeout):
        calls["count"] += 1
        return FakeResponse(yahoo_payload())

    provider = NSEProvider(opener=fake_opener)

    first = provider.load("RELIANCE.NS", "15m", 300)
    second = provider.load("RELIANCE.NS", "15m", 300)

    assert calls["count"] == 1
    assert first == second
    assert len(second) == 3

    print("NSE_PROVIDER_CACHE_CONTRACT: PASS")
    print("NETWORK_CALLS:", calls["count"])


if __name__ == "__main__":
    main()
