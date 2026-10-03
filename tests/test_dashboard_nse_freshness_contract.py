from types import SimpleNamespace

from dashboard.ui_state import build_ui_state


def main():
    state = SimpleNamespace(
        symbol="RELIANCE.NS",
        timeframe="15m",
        mode="SWING",
        market_metadata={
            "source": "YAHOO_NSE",
            "synthetic": False,
            "live_data_valid": True,
            "execution_allowed": False,
            "freshness": "SESSION_CLOSED",
        },
        market={
            "candles": [
                {
                    "time": 1789724700000,
                    "close_time": 1789725600000,
                    "open": 1243.4,
                    "high": 1243.4,
                    "low": 1226.4,
                    "close": 1226.4,
                    "volume": 7528935.0,
                }
            ]
        },
        idm={},
        execution={},
        risk={},
        mtf_indicators={},
    )

    ui = build_ui_state(state, {"enterprise": {}, "engines": {}})

    assert ui["freshness"]["initial_status"] == "SESSION_CLOSED"

    print("DASHBOARD_NSE_FRESHNESS_CONTRACT: PASS")


if __name__ == "__main__":
    main()
