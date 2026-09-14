import market.live_loader as live_loader


BASE_CANDLE = {
    "time": 1_000_000,
    "close_time": 1_899_999,
    "open": 100.0,
    "high": 105.0,
    "low": 99.0,
    "close": 103.0,
    "volume": 1000.0,
}


def test_current_candle_is_accepted():
    result = live_loader._validate_candle_temporal_freshness(
        BASE_CANDLE,
        now_ms=1_500_000,
    )
    assert result["freshness"] == "CURRENT"


def test_candle_within_lateness_tolerance_is_accepted():
    result = live_loader._validate_candle_temporal_freshness(
        BASE_CANDLE,
        now_ms=1_929_999,
    )
    assert result["freshness"] == "CURRENT"


def test_stale_candle_is_rejected():
    try:
        live_loader._validate_candle_temporal_freshness(
            BASE_CANDLE,
            now_ms=1_930_000,
        )
    except live_loader.LiveMarketLoaderError as exc:
        assert "stale" in str(exc).lower()
    else:
        raise AssertionError("stale candle was accepted")


def test_future_candle_is_rejected():
    try:
        live_loader._validate_candle_temporal_freshness(
            BASE_CANDLE,
            now_ms=999_999,
        )
    except live_loader.LiveMarketLoaderError as exc:
        assert "future" in str(exc).lower()
    else:
        raise AssertionError("future candle was accepted")


def test_reversed_candle_times_are_rejected():
    candle = dict(BASE_CANDLE)
    candle["close_time"] = candle["time"]

    try:
        live_loader._validate_candle_temporal_freshness(
            candle,
            now_ms=1_500_000,
        )
    except live_loader.LiveMarketLoaderError as exc:
        assert "close_time" in str(exc)
    else:
        raise AssertionError("reversed candle timestamps were accepted")
