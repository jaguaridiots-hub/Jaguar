from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]

API = (ROOT / "api.py").read_text(encoding="utf-8")
IDM = (ROOT / "intelligence" / "idm.py").read_text(encoding="utf-8")
UI = (ROOT / "dashboard" / "ui_state.py").read_text(encoding="utf-8")
V3 = (ROOT / "dashboard" / "command_center_v3.py").read_text(encoding="utf-8")


def block(source, start, end=None):
    pos = source.find(start)
    assert pos >= 0, f"MISSING={start}"
    if end is None:
        return source[pos:]
    end_pos = source.find(end, pos + len(start))
    assert end_pos >= 0, f"MISSING_END={end}"
    return source[pos:end_pos]


# --------------------------------------------------
# API boundary
# --------------------------------------------------

m = re.search(
    r'async def dashboard_state\(\s*'
    r'symbol:\s*str\s*=\s*"BTCUSDT",\s*'
    r'interval:\s*str\s*=\s*"15m",\s*'
    r'mode:\s*str\s*=\s*"SWING",',
    API,
    re.S,
)
assert m, "dashboard_state context signature missing"

assert (
    'if mode.upper() not in {"SCALP", "SWING", "CLASSIC"}'
    in API
)

assert "kernel.initialize(symbol, interval)" in API
assert "state.mode = mode.upper()" in API
assert "JaguarAnalysisEngine(kernel).run(symbol)" in API
assert "build_ui_state(canonical_state, report=report)" in API


# --------------------------------------------------
# Canonical IDM boundary
# --------------------------------------------------

idm_state = block(
    IDM,
    "state.idm = {",
    "}",
)

assert '"analysis_mode": analysis_mode["mode"]' in idm_state
assert (
    '"analysis_mode_contract": analysis_mode'
    in idm_state
)


# --------------------------------------------------
# UI adapter boundary
# --------------------------------------------------

ui_idm = block(
    UI,
    '"idm": {',
    '"decision": decision,',
)

assert '"analysis_mode": _text(' in ui_idm
assert re.search(
    r'master\.get\(\s*"analysis_mode",',
    ui_idm,
)
assert re.search(
    r'getattr\(\s*state,\s*"mode",\s*"SWING"\s*\)',
    ui_idm,
)
assert (
    '"analysis_mode_contract": _mapping('
    in ui_idm
)
assert re.search(
    r'master\.get\(\s*"analysis_mode_contract"\s*\)',
    ui_idm,
)


# --------------------------------------------------
# V3 request boundary
# --------------------------------------------------

assert "getActiveInterval()" in V3
assert "getActiveMode()" in V3

load_block = block(
    V3,
    "async function load(){",
    "initAnalysisContextControls();",
)

assert (
    '`&interval=${encodeURIComponent(getActiveInterval())}`'
    in load_block
)
assert (
    '`&mode=${encodeURIComponent(getActiveMode())}`'
    in load_block
)


# --------------------------------------------------
# Forbidden policy coupling
# --------------------------------------------------

policy_forbidden = (
    "score_threshold",
    "risk_percent",
    "atr_multiplier",
    "position_size",
    "execution_override",
    "broker_order",
)

analysis_context_area = (
    IDM[IDM.find("analysis_mode"):IDM.find("analysis_mode") + 2500]
)

for token in policy_forbidden:
    assert token not in analysis_context_area, (
        f"FORBIDDEN_POLICY_TOKEN={token}"
    )


print("R54C_API_CONTEXT_BOUNDARY=PASS")
print("R54C_IDM_CONTEXT_BOUNDARY=PASS")
print("R54C_UI_CONTEXT_BOUNDARY=PASS")
print("R54C_V3_CONTEXT_BOUNDARY=PASS")
print("R54C_NO_POLICY_COUPLING=PASS")
print("R54C_CONTEXT_CONVERGENCE_CONTRACT=PASS")
