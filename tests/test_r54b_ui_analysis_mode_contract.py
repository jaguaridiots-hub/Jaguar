from pathlib import Path


def run():
    src = Path(
        "dashboard/ui_state.py"
    ).read_text()

    start = src.index('        "idm": {')
    end = src.index(
        '        "structure": {',
        start,
    )

    block = src[start:end]

    assert '"analysis_mode": _text(' in block
    assert '"analysis_mode_contract": _mapping(' in block
    assert 'master.get("analysis_mode_contract")' in block
    assert 'getattr(state, "mode", "SWING")' in block

    forbidden = (
        "min_score",
        "min_confidence",
        "risk_percent",
        "atr_multiplier",
        "stop_multiplier",
        "target_multiplier",
        "ExecutionGateway",
        "TradePlanner",
        "RiskManager",
    )

    for token in forbidden:
        assert token not in block, (
            f"R54B_UI_FORBIDDEN={token}"
        )

    print("R54B_UI_ANALYSIS_MODE_CONTRACT=PASS")
    print("R54B_UI_NO_TRADING_POLICY=PASS")


if __name__ == "__main__":
    run()
