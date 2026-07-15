import json
import urllib.parse
import urllib.request


def get_data(symbol):
    encoded_symbol = urllib.parse.quote(symbol, safe="")
    params = urllib.parse.urlencode(
        {
            "interval": "1d",
            "range": "1y",
        }
    )
    url = (
        "https://query1.finance.yahoo.com/v8/finance/chart/"
        + encoded_symbol
        + "?"
        + params
    )

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        },
        method="GET",
    )

    with urllib.request.urlopen(request, timeout=15) as response:
        payload = json.loads(response.read().decode("utf-8"))

    chart = payload["chart"]

    if chart.get("error") is not None:
        raise RuntimeError(f"NSE market data error: {chart['error']}")

    results = chart.get("result")

    if not isinstance(results, list) or not results:
        raise RuntimeError("NSE market data returned no result")

    result = results[0]
    timestamps = result.get("timestamp")
    indicators = result.get("indicators")

    if not isinstance(timestamps, list):
        raise RuntimeError("NSE market data returned invalid timestamps")

    if not isinstance(indicators, dict):
        raise RuntimeError("NSE market data returned invalid indicators")

    quotes = indicators.get("quote")

    if not isinstance(quotes, list) or not quotes:
        raise RuntimeError("NSE market data returned no quote series")

    quote = quotes[0]

    if not isinstance(quote, dict):
        raise RuntimeError("NSE market data returned invalid quote series")

    required_fields = (
        "open",
        "high",
        "low",
        "close",
        "volume",
    )

    for field in required_fields:
        values = quote.get(field)

        if not isinstance(values, list):
            raise RuntimeError(
                f"NSE market data returned invalid {field} series"
            )

        if len(values) != len(timestamps):
            raise RuntimeError(
                f"NSE market data returned misaligned {field} series"
            )

    candles = []

    for index, timestamp in enumerate(timestamps):
        open_value = quote["open"][index]
        high_value = quote["high"][index]
        low_value = quote["low"][index]
        close_value = quote["close"][index]
        volume_value = quote["volume"][index]

        values = (
            open_value,
            high_value,
            low_value,
            close_value,
            volume_value,
        )

        if timestamp is None or any(value is None for value in values):
            continue

        candles.append(
            {
                "time": int(timestamp) * 1000,
                "open": float(open_value),
                "high": float(high_value),
                "low": float(low_value),
                "close": float(close_value),
                "volume": float(volume_value),
            }
        )

    candles = candles[-300:]

    if not candles:
        raise RuntimeError("NSE market data returned no complete candles")

    latest = candles[-1]

    return {
        "market": "NSE",
        "symbol": symbol,
        "price": latest["close"],
        "high": latest["high"],
        "low": latest["low"],
        "volume": latest["volume"],
        "candles": candles,
    }
