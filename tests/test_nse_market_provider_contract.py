from market.provider import MarketProvider
from market.nse_provider import NSEProvider


def test_nse_routes_through_canonical_provider(monkeypatch):
    calls = []

    def fake_load(self, symbol, interval="15m", limit=300):
        calls.append((symbol, interval, limit))
        return [
            {
                "time": 1700000000000,
                "close_time": 1700000900000,
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.5,
                "volume": 1000.0,
            }
        ]

    monkeypatch.setattr(NSEProvider, "load", fake_load)

    candles = MarketProvider.load(
        "RELIANCE.NS",
        "15m",
        300,
    )

    assert calls == [
        ("RELIANCE.NS", "15m", 300),
    ]

    assert candles[0]["close_time"] == (
        candles[0]["time"] + 900_000
    )


if __name__ == "__main__":
    import pytest

    with pytest.MonkeyPatch.context() as monkeypatch:
        test_nse_routes_through_canonical_provider(monkeypatch)

    print("NSE_MARKET_PROVIDER_CONTRACT: PASS")
