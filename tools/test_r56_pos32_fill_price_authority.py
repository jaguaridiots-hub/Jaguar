from types import SimpleNamespace

import research.recorder as recorder


def make_state():
    return SimpleNamespace(
        symbol="BTCUSDT",
        interval="15m",
        price=101.5,
        high=102.0,
        low=100.5,
        volume=10.0,
        mode="PAPER",

        execution={
            "authorization_id": "AUTH-R56-POS32",
            "trade_uuid": "TRADE-R56-POS32",
            "symbol": "BTCUSDT",
            "timeframe": "15m",
            "mode": "PAPER",
            "decision": "ENTER_LONG",
            "entry": 100.0,
            "fill_price": 101.5,
            "stop_loss": 95.0,
            "targets": [110.0, 115.0, 120.0],
            "position_size": 1.0,
            "filled_quantity": 1.0,
            "order_status": "FILLED",
        },

        trade={
            "decision": "ENTER_LONG",
            "entry": 99.0,
            "stop_loss": 80.0,
            "targets": [130.0, 140.0, 150.0],
        },

        trade_plan={},

        idm={
            "decision": "ENTER_LONG",
            "confidence": 99,
            "score": 99,
        },
        master_decision={},
        ai_brain={"score": 99},
        probability={"score": 99},
        risk={},
        trade_validator={},
        brain_explain={},
        regime={},
        session={},
        mtf={},
        smc={},
        liquidity={},
        orderflow={},
        market={
            "regime_result": {},
            "liquidity_result": {},
            "structural_results": {
                "fvg": {},
            },
        },
        _decision_weights={},
    )


def main():
    captured = {}

    original_init_db = recorder.init_db
    original_get_asset_class = recorder.get_asset_class
    original_insert_open_trade = recorder.insert_open_trade

    try:
        recorder.init_db = lambda: None
        recorder.get_asset_class = lambda symbol: "CRYPTO"

        def capture_trade(data):
            captured.update(data)

        recorder.insert_open_trade = capture_trade

        state = make_state()

        recorded = recorder.record_trade_open(
            state,
            run_id="R56-POS32",
            entry_time="2026-09-30T00:00:00",
            trade_uuid="TRADE-R56-POS32",
            authorization_id="AUTH-R56-POS32",
        )

        assert recorded == "TRADE-R56-POS32"
        assert captured["entry_price"] == 101.5

        assert captured["entry_price"] != state.execution["entry"]
        assert captured["entry_price"] != state.trade["entry"]

        print(
            "R56_POS32_PAPER_PERSISTENCE_USES_BROKER_FILL_PRICE: PASS"
        )
        print(
            "R56_POS32_AUTHORIZED_ENTRY_CANNOT_OVERRIDE_FILL_PRICE: PASS"
        )
        print(
            "R56_POS32_MUTABLE_STATE_TRADE_CANNOT_OVERRIDE_FILL_PRICE: PASS"
        )

        # Missing fill evidence must fail closed.
        captured.clear()
        state.execution.pop("fill_price")

        try:
            recorder.record_trade_open(
                state,
                run_id="R56-POS32-MISSING",
                entry_time="2026-09-30T00:00:00",
                trade_uuid="TRADE-R56-POS32-MISSING",
                authorization_id="AUTH-R56-POS32",
            )
        except RuntimeError as exc:
            assert "fill price" in str(exc).lower()
            print(
                "R56_POS32_MISSING_FILL_PRICE_FAILS_CLOSED: PASS"
            )
        else:
            raise AssertionError(
                "Missing authoritative PAPER fill price was accepted"
            )

        print("R56_POS32_FILL_PRICE_AUTHORITY: PASS")

    finally:
        recorder.init_db = original_init_db
        recorder.get_asset_class = original_get_asset_class
        recorder.insert_open_trade = original_insert_open_trade


if __name__ == "__main__":
    main()
