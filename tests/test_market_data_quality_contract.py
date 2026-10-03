from market.data_quality import validate_candle_series


def make_candle(timestamp, **overrides):
    candle = {
        "time": timestamp,
        "close_time": timestamp + 899_999,
        "open": 100.0,
        "high": 105.0,
        "low": 99.0,
        "close": 103.0,
        "volume": 1000.0,
    }
    candle.update(overrides)
    return candle


def valid_series():
    base = 1_700_000_000_000
    return [
        make_candle(base),
        make_candle(base + 900_000),
        make_candle(base + 1_800_000),
    ]


def test_valid_crypto_series():
    result = validate_candle_series(
        valid_series(),
        interval="15m",
        market_identity="CRYPTO",
    )
    assert result["status"] == "VALID"
    assert result["integrity_ok"] is True
    assert result["schema_valid"] is True
    assert result["ohlcv_valid"] is True
    assert result["timestamps_valid"] is True
    assert result["monotonic"] is True
    assert result["duplicates_clear"] is True
    assert result["interval_consistent"] is True
    assert result["gap_detected"] is False


def test_duplicate_timestamp_fails_closed():
    series = valid_series()
    series[2]["time"] = series[1]["time"]

    result = validate_candle_series(
        series, "15m", "CRYPTO"
    )

    assert result["integrity_ok"] is False
    assert result["duplicates_clear"] is False


def test_non_monotonic_timestamp_fails_closed():
    series = valid_series()
    series[2]["time"] = series[0]["time"] - 900_000

    result = validate_candle_series(
        series, "15m", "CRYPTO"
    )

    assert result["integrity_ok"] is False
    assert result["monotonic"] is False
    assert result["timestamps_valid"] is False


def test_off_interval_spacing_fails_closed():
    series = valid_series()
    series[2]["time"] = series[1]["time"] + 1_000_000

    result = validate_candle_series(
        series, "15m", "CRYPTO"
    )

    assert result["integrity_ok"] is False
    assert result["interval_consistent"] is False


def test_crypto_gap_fails_closed():
    series = valid_series()
    series[2]["time"] = series[1]["time"] + 1_800_000

    result = validate_candle_series(
        series, "15m", "CRYPTO"
    )

    assert result["gap_detected"] is True
    assert result["gap_count"] == 1
    assert result["integrity_ok"] is False
    assert result["gap_policy"] == "STRICT_CONTINUOUS"


def test_session_market_gap_is_explicit_but_allowed():
    series = valid_series()

    session_gap_time = (
        series[1]["time"] + 10 * 900_000
    )

    series[2]["time"] = session_gap_time
    series[2]["close_time"] = (
        session_gap_time + 899_999
    )

    result = validate_candle_series(
        series, "15m", "NSE"
    )

    assert result["gap_detected"] is True
    assert result["gap_count"] == 1
    assert result["status"] == "VALID_WITH_GAPS"
    assert result["integrity_ok"] is True
    assert result["gap_policy"] == "SESSION_GAPS_ALLOWED"


def test_invalid_ohlc_fails_closed():
    series = valid_series()
    series[1]["high"] = 90.0

    result = validate_candle_series(
        series, "15m", "CRYPTO"
    )

    assert result["integrity_ok"] is False
    assert result["ohlcv_valid"] is False


def test_non_finite_value_fails_closed():
    series = valid_series()
    series[1]["close"] = float("nan")

    result = validate_candle_series(
        series, "15m", "CRYPTO"
    )

    assert result["integrity_ok"] is False
    assert result["ohlcv_valid"] is False


def test_zero_volume_fails_closed():
    series = valid_series()
    series[1]["volume"] = 0.0

    result = validate_candle_series(
        series, "15m", "CRYPTO"
    )

    assert result["integrity_ok"] is False
    assert result["ohlcv_valid"] is False


def test_invalid_temporal_bounds_fail_closed():
    series = valid_series()
    series[1]["close_time"] = series[1]["time"]

    result = validate_candle_series(
        series, "15m", "CRYPTO"
    )

    assert result["integrity_ok"] is False
    assert result["timestamps_valid"] is False


def test_unsupported_interval_fails_closed():
    result = validate_candle_series(
        valid_series(), "7m", "CRYPTO"
    )

    assert result["integrity_ok"] is False
    assert result["status"] == "INVALID"
