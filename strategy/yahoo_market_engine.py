# strategy/yahoo_market_engine.py
import requests
import json
from datetime import datetime
import math
import time as _time
from core.asset_registry import get_yahoo_symbol, get_asset_metadata

def build_4h_candles(candles_1h):
    candles_4h = []

    for i in range(0, len(candles_1h), 4):
        group = candles_1h[i:i + 4]

        if len(group) < 4:
            break

        candles_4h.append({
            "time": group[0]["time"],
            "open": group[0]["open"],
            "high": max(c["high"] for c in group),
            "low": min(c["low"] for c in group),
            "close": group[-1]["close"],
            "volume": sum(c["volume"] for c in group),
        })

    return candles_4h

class YahooMarketEngine:
    def run(self, state, bus):
        bus.publish("MARKET_LOADING")

        raw_symbol = getattr(state, "symbol", None) or "BTCUSDT"
        canonical_symbol = raw_symbol

        yahoo_symbol = get_yahoo_symbol(raw_symbol)
        symbol = yahoo_symbol if yahoo_symbol else raw_symbol

        meta = get_asset_metadata(raw_symbol)
        if meta:
            state.asset_class = meta.get("asset_class")
            state.currency = meta.get("currency")
            state.exchange = meta.get("exchange")
            state.trading_hours = meta.get("trading_hours")
            state.timezone = meta.get("timezone")
            state.tick_size = meta.get("tick_size")
        else:
            state.asset_class = "unknown"
            state.currency = "USD"

        interval = getattr(state, "interval", None) or "15m"

        interval_map = {
            "1m": "1m",
            "5m": "5m",
            "15m": "15m",
            "30m": "30m",
            "1h": "60m",
            "4h": "1d",
            "1d": "1d"
        }
        yahoo_interval = interval_map.get(interval, "15m")

        range_map = {
            "1m": "1d",
            "5m": "5d",
            "15m": "1mo",
            "30m": "1mo",
            "1h": "2mo",
            "1d": "2y"
        }
        yahoo_range = range_map.get(interval, "1mo")

        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        headers = {"User-Agent": "Mozilla/5.0"}
        params = {
            "interval": yahoo_interval,
            "range": yahoo_range,
            "includePrePost": "false"
        }

        try:

            state.market = {}

            timeframes = ["15m", "1h", "1d"]

            for tf in timeframes:

                yahoo_interval = interval_map.get(tf, "15m")
                yahoo_range = range_map.get(tf, "1mo")

                params = {
                    "interval": yahoo_interval,
                    "range": yahoo_range,
                    "includePrePost": "false",
                }

                resp = requests.get(
                    url,
                    headers=headers,
                    params=params,
                    timeout=8,
                )

                if resp.status_code != 200:
                    raise Exception(
                        f"{tf} HTTP {resp.status_code}"
                    )

                data = resp.json()

                chart = data.get("chart", {})
                result = chart.get("result", [])

                if not result:
                    raise Exception(f"No data for {tf}")

                quotes = result[0]

                timestamps = quotes.get("timestamp", [])

                quote = (
                    quotes.get("indicators", {})
                    .get("quote", [{}])[0]
                )

                opens = quote.get("open", [])
                highs = quote.get("high", [])
                lows = quote.get("low", [])
                closes = quote.get("close", [])
                volumes = quote.get("volume", [])

                candles = []

                for i in range(len(timestamps)):

                    if closes[i] is None:
                        continue

                    candles.append({
                        "time": timestamps[i],
                        "open": float(opens[i] or 0),
                        "high": float(highs[i] or 0),
                        "low": float(lows[i] or 0),
                        "close": float(closes[i]),
                        "volume": float(volumes[i] or 0),
                    })

                if not candles:
                    raise Exception(f"No candles for {tf}")

                # ==================================================
                # DROP TRAILING ZERO-VOLUME CANDLES
                # ==================================================
                # Yahoo can expose a currently forming candle with
                # OHLC values but zero volume. It must not become
                # the execution reference candle.
                # ==================================================

                dropped_zero_volume = 0

                while (
                    len(candles) >= 2
                    and float(candles[-1].get("volume", 0) or 0) <= 0
                ):
                    candles.pop()
                    dropped_zero_volume += 1

                if dropped_zero_volume:
                    print(
                        f"⚠️ {tf}: dropped "
                        f"{dropped_zero_volume} trailing zero-volume candle(s)"
                    )

                if not candles:
                    raise Exception(
                        f"No valid candles for {tf} after "
                        "zero-volume cleanup"
                    )


                state.market[tf] = {
                    "symbol": symbol,
                    "interval": tf,
                    "candles": candles,
                    "exchange": "YAHOO",
                }

                print(f"✅ {tf}: {len(candles)} candles")

            state.timeframes = list(state.market.keys())

            # Build 4h candles from 1h candles
            if "1h" in state.market:

                candles_1h = state.market["1h"]["candles"]

                candles_4h = build_4h_candles(candles_1h)

                state.market["4h"] = {
                    "symbol": symbol,
                    "interval": "4h",
                    "candles": candles_4h,
                    "exchange": "YAHOO",
                }

                state.timeframes = list(state.market.keys())

                print(f"✅ 4h: {len(candles_4h)} candles (built from 1h)")

            state.market_current = state.market[interval]

            last = state.market_current["candles"][-1]

            # ==================================================
            # LIVE MARKET DATA INTEGRITY
            # ==================================================
            try:
                o = float(last["open"])
                h = float(last["high"])
                l = float(last["low"])
                c = float(last["close"])
                v = float(last["volume"])
                integrity_ok = (
                    all(map(math.isfinite, (o, h, l, c, v)))
                    and o > 0
                    and h > 0
                    and l > 0
                    and c > 0
                    and h >= max(o, c)
                    and l <= min(o, c)
                    and h > l
                    and v > 0
                )
            except (KeyError, TypeError, ValueError):
                integrity_ok = False

            state.market_metadata = {
                "source": "YAHOO",
                "synthetic": False,
                "live_data_valid": integrity_ok,
                "execution_allowed": integrity_ok,
            }

            state.price = last["close"]
            state.high = last["high"]
            state.low = last["low"]
            state.volume = last["volume"]

            state.symbol = canonical_symbol
            state.interval = interval

            print(
                f"✅ Loaded {len(state.timeframes)} timeframes for {symbol}"
            )
        except Exception as e:
            print(f"❌ Yahoo error: {e}")

            # ---- Deterministic synthetic MTF fallback ----
            #
            # Offline/research fixture only.
            # Generate a native 15m base series, then aggregate it
            # into 1h, 4h and 1d candles so MTF analysis receives
            # structurally different timeframes.
            #
            base_count = 28800
            base_step = 15 * 60
            now = int(_time.time())
            base_candles = []

            price = 100.0

            for i in range(base_count):
                # Deterministic multi-regime market path:
                # accumulation -> bullish expansion -> pullback
                # -> bearish expansion -> consolidation -> recovery.
                x = i / base_count

                if x < 0.18:
                    drift = 0.015
                elif x < 0.42:
                    drift = 0.055
                elif x < 0.52:
                    drift = -0.035
                elif x < 0.72:
                    drift = -0.060
                elif x < 0.86:
                    drift = 0.010
                else:
                    drift = 0.045

                wave_fast = math.sin(i * 0.37) * 0.45
                wave_slow = math.sin(i * 0.071) * 0.80

                previous = price
                price += drift + wave_fast + wave_slow

                # Keep the fixture numerically stable.
                price = max(price, 20.0)

                open_price = previous
                close_price = price

                spread = (
                    0.65
                    + abs(math.sin(i * 0.23)) * 0.45
                    + abs(drift) * 2.0
                )

                high = max(open_price, close_price) + spread
                low = min(open_price, close_price) - spread

                volume = (
                    900
                    + int(abs(math.sin(i * 0.11)) * 500)
                    + int(abs(drift) * 5000)
                )

                base_candles.append({
                    "time": now - (base_count - i) * base_step,
                    "open": round(open_price, 2),
                    "high": round(high, 2),
                    "low": round(low, 2),
                    "close": round(close_price, 2),
                    "volume": float(volume),
                })

            def aggregate_candles(candles, group_size, timeframe):
                aggregated = []

                for i in range(0, len(candles), group_size):
                    group = candles[i:i + group_size]

                    if len(group) < group_size:
                        break

                    aggregated.append({
                        "time": group[0]["time"],
                        "open": group[0]["open"],
                        "high": max(c["high"] for c in group),
                        "low": min(c["low"] for c in group),
                        "close": group[-1]["close"],
                        "volume": sum(c["volume"] for c in group),
                    })

                return aggregated

            candles_15m = base_candles
            candles_1h = aggregate_candles(
                candles_15m,
                4,
                "1h",
            )
            candles_4h = aggregate_candles(
                candles_15m,
                16,
                "4h",
            )
            candles_1d = aggregate_candles(
                candles_15m,
                96,
                "1d",
            )

            fallback_data = {
                "15m": candles_15m,
                "1h": candles_1h,
                "4h": candles_4h,
                "1d": candles_1d,
            }

            state.market = {}

            for tf, candles in fallback_data.items():
                state.market[tf] = {
                    "symbol": symbol,
                    "interval": tf,
                    "candles": candles,
                    "exchange": "OFFLINE",
                }

            state.timeframes = list(state.market.keys())

            # Preserve requested symbol and interval during fallback.
            state.symbol = canonical_symbol
            state.interval = interval

            state.market_current = state.market[state.interval]

            state.market_metadata = {
                "source": "offline_fallback",
                "synthetic": True,
                "live_data_valid": False,
                "execution_allowed": False,
                "base_interval": "15m",
                "aggregation": {
                    "15m": "native",
                    "1h": "4x15m",
                    "4h": "16x15m",
                    "1d": "96x15m",
                },
            }

            print("⚠️ Using fallback candle data (Yahoo timed out or error)")

        bus.publish("MARKET_READY")
        return state
