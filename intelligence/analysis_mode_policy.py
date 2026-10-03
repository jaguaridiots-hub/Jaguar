"""
Jaguar Quant X Enterprise
Canonical Analysis Mode Contract

R54-A establishes the analysis-context vocabulary only.

Supported modes:
    SCALP
    SWING
    CLASSIC

This module intentionally contains NO:
- scoring adjustments
- score thresholds
- risk percentages
- ATR multipliers
- execution overrides
- directional logic
"""

ANALYSIS_MODES = (
    "SCALP",
    "SWING",
    "CLASSIC",
)

DEFAULT_ANALYSIS_MODE = "SWING"


def normalize_analysis_mode(value):
    mode = str(
        value or DEFAULT_ANALYSIS_MODE
    ).upper().strip()

    if mode in ANALYSIS_MODES:
        return mode

    return DEFAULT_ANALYSIS_MODE


def analysis_mode_contract(value):
    mode = normalize_analysis_mode(value)

    return {
        "mode": mode,
        "supported_modes": list(ANALYSIS_MODES),
        "default_mode": DEFAULT_ANALYSIS_MODE,
        "policy_version": "R54-A",
    }
