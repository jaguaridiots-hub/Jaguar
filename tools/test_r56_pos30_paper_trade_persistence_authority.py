from types import SimpleNamespace

import research.recorder as recorder


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

        authorized_execution = {
            "authorization_id": "AUTH-R56-POS30",
            "trade_uuid": "TRADE-R56-POS30",
            "symbol": "BTCUSDT",
            "timeframe": "15m",
            "mode": "PAPER",
            "decision": "ENTER_LONG",
            "entry": 100.0,
            "stop_loss": 95.0,
            "targets": [110.0, 115.0, 120.0],
            "position_size": 1.0,
            "risk_amount": 5.0,
        }

        # Deliberately divergent mutable enterprise trade state.
        state = SimpleNamespace(
            symbol="BTCUSDT",
            interval="15m",
            price=100.0,
            high=101.0,
            low=99.0,
            volume=10.0,
            mode="PAPER",
            execution=dict(authorized_execution),
            trade={
                "decision": "ENTER_LONG",
                "entry": 90.0,
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
            ai_brain={},
            probability={},
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

        recorded = recorder.record_trade_open(
            state,
            run_id="R56-POS30",
            entry_time="2026-09-30T00:00:00",
            trade_uuid="TRADE-R56-POS30",
            authorization_id="AUTH-R56-POS30",
        )

        assert recorded == "TRADE-R56-POS30"

        assert captured["entry_price"] == 100.0
        assert captured["stop_loss"] == 95.0
        assert captured["take_profit"] == 110.0

        assert captured["entry_price"] != state.trade["entry"]
        assert captured["stop_loss"] != state.trade["stop_loss"]
        assert captured["take_profit"] != state.trade["targets"][0]

        print(
            "R56_POS30_PAPER_PERSISTENCE_USES_AUTHORIZED_ENTRY: PASS"
        )
        print(
            "R56_POS30_PAPER_PERSISTENCE_USES_AUTHORIZED_STOP: PASS"
        )
        print(
            "R56_POS30_PAPER_PERSISTENCE_USES_AUTHORIZED_TP1: PASS"
        )
        print(
            "R56_POS30_DIVERGENT_STATE_TRADE_CANNOT_OVERRIDE_AUTHORITY: PASS"
        )

    finally:
        recorder.init_db = original_init_db
        recorder.get_asset_class = original_get_asset_class
        recorder.insert_open_trade = original_insert_open_trade


if __name__ == "__main__":
    main()
