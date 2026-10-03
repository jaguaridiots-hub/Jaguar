from core.market_state import MarketState
from intelligence.execution_gateway_v2 import ExecutionGatewayV2

import market.live_loader as live_loader


CANDLE = {
    "time": 1_700_000_000_000,
    "close_time": 1_700_000_900_000,
    "open": 100.0,
    "high": 101.0,
    "low": 99.0,
    "close": 100.5,
    "volume": 1000.0,
}


class FakeMarketAdapter:
    @staticmethod
    def load(
        symbol,
        interval="15m",
        limit=500,
        *,
        intraday=None,
        to_date=None,
        from_date=None,
        as_of=None,
    ):
        assert symbol == "RELIANCE.NS"
        assert interval == "15m"
        return [dict(CANDLE)]

    @staticmethod
    def load_with_identity(*args, **kwargs):
        raise AssertionError(
            "NSE must use normal canonical candle routing"
        )


def test_nse_market_data_is_valid_but_not_execution_authorized(
    monkeypatch,
):
    monkeypatch.setattr(
        live_loader,
        "MarketAdapter",
        FakeMarketAdapter,
    )

    state = MarketState()
    state.symbol = "RELIANCE.NS"
    state.timeframe = "15m"
    state.market = {}

    result = live_loader.update_state(
        state,
        "RELIANCE.NS",
        now_ms=CANDLE["close_time"],
    )

    assert result is state

    metadata = state.market_metadata

    assert metadata["source"] == "YAHOO_NSE"
    assert metadata["synthetic"] is False
    assert metadata["live_data_valid"] is True
    assert metadata["execution_allowed"] is False


def test_execution_gateway_blocks_nse_yahoo_data(
    monkeypatch,
):
    monkeypatch.setattr(
        live_loader,
        "MarketAdapter",
        FakeMarketAdapter,
    )

    state = MarketState()
    state.symbol = "RELIANCE.NS"
    state.timeframe = "15m"
    state.market = {}

    live_loader.update_state(
        state,
        "RELIANCE.NS",
        now_ms=CANDLE["close_time"],
    )

    gateway = ExecutionGatewayV2()
    result = gateway.process(state)

    assert result is state
    assert result.execution["approved"] is False
    assert result.execution["status"] == "BLOCKED"
    assert result.execution["gate"] == "MARKET_DATA"
    assert "instrument_token" not in result.execution


if __name__ == "__main__":
    print(
        "NSE_LIVE_MARKET_SAFETY_CONTRACT: "
        "RUN WITH PYTEST"
    )
