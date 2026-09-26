from types import SimpleNamespace

from intelligence.analysis_mode_policy import (
    ANALYSIS_MODES,
    DEFAULT_ANALYSIS_MODE,
    analysis_mode_contract,
    normalize_analysis_mode,
)


def run():
    assert ANALYSIS_MODES == (
        "SCALP",
        "SWING",
        "CLASSIC",
    )

    assert DEFAULT_ANALYSIS_MODE == "SWING"

    assert normalize_analysis_mode("SCALP") == "SCALP"
    assert normalize_analysis_mode("scalp") == "SCALP"
    assert normalize_analysis_mode("SWING") == "SWING"
    assert normalize_analysis_mode("CLASSIC") == "CLASSIC"
    assert normalize_analysis_mode("invalid") == "SWING"
    assert normalize_analysis_mode(None) == "SWING"

    for mode in ANALYSIS_MODES:
        contract = analysis_mode_contract(mode)

        assert contract["mode"] == mode
        assert contract["supported_modes"] == [
            "SCALP",
            "SWING",
            "CLASSIC",
        ]
        assert contract["default_mode"] == "SWING"
        assert contract["policy_version"] == "R54-A"

    # Context only: no trading-policy fields are permitted.
    forbidden = {
        "score",
        "min_score",
        "confidence",
        "min_confidence",
        "risk_percent",
        "atr_multiplier",
        "stop_multiplier",
        "target_multiplier",
    }

    contract = analysis_mode_contract("SCALP")

    assert forbidden.isdisjoint(contract)

    # Verify state.mode can be represented without changing it.
    state = SimpleNamespace(mode="CLASSIC")

    assert analysis_mode_contract(state.mode)["mode"] == "CLASSIC"

    print("R54A_ANALYSIS_CONTEXT=PASS")
    print("R54A_SUPPORTED_MODES=PASS")
    print("R54A_NO_TRADING_PARAMETERS=PASS")


if __name__ == "__main__":
    run()
