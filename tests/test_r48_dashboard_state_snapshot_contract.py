from pathlib import Path
import re

P = Path("dashboard/command_center_v3.py")
src = P.read_text()

print("=== R48 DASHBOARD STATE SNAPSHOT CONTRACT ===")

# ------------------------------------------------------------
# Previous release boundaries must remain intact.
# ------------------------------------------------------------
for start, end, func in [
    (
        "/* R45_DASHBOARD_CANVAS_SIZE_STATE_START */",
        "/* R45_DASHBOARD_CANVAS_SIZE_STATE_END */",
        "function setDashboardCanvasSize(canvas,width,height){",
    ),
    (
        "/* R46_DASHBOARD_CANVAS_CONTEXT_STATE_START */",
        "/* R46_DASHBOARD_CANVAS_CONTEXT_STATE_END */",
        "function setDashboardCanvasContextState(ctx,name,value){",
    ),
    (
        "/* R47_DASHBOARD_CANVAS_DASH_STATE_START */",
        "/* R47_DASHBOARD_CANVAS_DASH_STATE_END */",
        "function setDashboardCanvasLineDash(ctx,dash){",
    ),
]:
    assert start in src
    assert end in src
    assert func in src

print("R45_BOUNDARY=PASS")
print("R46_BOUNDARY=PASS")
print("R47_BOUNDARY=PASS")

# ------------------------------------------------------------
# R48 boundary.
# ------------------------------------------------------------
start = "/* R48_DASHBOARD_STATE_SNAPSHOT_START */"
end = "/* R48_DASHBOARD_STATE_SNAPSHOT_END */"

assert start in src
assert end in src
assert "function setDashboardStateSnapshot(d){" in src

helper_match = re.search(
    re.escape(start) + r"(.*?)" + re.escape(end),
    src,
    re.S,
)
assert helper_match
helper = helper_match.group(1)

print("R48_BOUNDARY=PASS")

# ------------------------------------------------------------
# Helper owns exactly the canonical dashboard snapshot state.
# ------------------------------------------------------------
assert "state.ui=d.ui;" in helper
assert "state.candles=Array.isArray(d.candles)?d.candles:[];" in helper

assert helper.count("state.ui=") == 1
assert helper.count("state.candles=") == 1

print("R48_UI_STATE_OWNERSHIP=PASS")
print("R48_CANDLES_STATE_OWNERSHIP=PASS")

# ------------------------------------------------------------
# Helper must reject invalid snapshots safely.
# ------------------------------------------------------------
assert 'if(!d||typeof d!=="object")return;' in helper
assert 'if(!d.ui)return;' in helper

print("R48_INPUT_GUARD=PASS")

# ------------------------------------------------------------
# load() must invoke the helper once and render afterward.
# ------------------------------------------------------------
load_match = re.search(
    r"async function load\(\)\{(.*?)\n\}",
    src,
    re.S,
)
assert load_match

load_body = load_match.group(1)

assert load_body.count("setDashboardStateSnapshot(d);") == 1
assert "state.ui=d.ui;" not in load_body
assert "state.candles=Array.isArray(d.candles)?d.candles:[];" not in load_body

snapshot_pos = load_body.find("setDashboardStateSnapshot(d);")
render_pos = load_body.find("render();")

assert snapshot_pos >= 0
assert render_pos >= 0
assert snapshot_pos < render_pos

print("R48_LOAD_USES_CENTRAL_SETTER=PASS")
print("R48_RENDER_ORDER=PASS")

# ------------------------------------------------------------
# Scanner/news state remain separate.
# ------------------------------------------------------------


# ------------------------------------------------------------
# No storage/network/execution mutation inside R48 helper.
# ------------------------------------------------------------
for forbidden in [
    "sessionStorage",
    "localStorage",
    "fetch(",
    "XMLHttpRequest",
    "WebSocket",
    "IDM",
    "TradePlanner",
    "RiskManager",
    "ExecutionConfirmation",
    "ExecutionGateway",
    "execution_intent",
    "place_order",
    "submit_order",
    "state.decision",
    "state.trade",
    "state.risk",
    "state.execution",
]:
    assert forbidden not in helper

print("R48_NO_STORAGE=PASS")
print("R48_NO_NETWORK=PASS")
print("R48_NO_EXECUTION_AUTHORITY=PASS")

# ------------------------------------------------------------
# Application-level canonical state semantics.
# ------------------------------------------------------------
assert "const d=await r.json();" in load_body
assert 'if(!d||!d.ui) throw new Error("Invalid dashboard state");' in load_body
assert "setDashboardStateSnapshot(d);" in load_body
assert "render();" in load_body

print("R48_DASHBOARD_STATE_SEMANTICS=PASS")
# ------------------------------------------------------------
# Scanner/news remain outside the R48 snapshot helper.
# Later releases may centralize those domains independently.
# ------------------------------------------------------------
assert "state.scanner" not in helper
assert "state.news" not in helper
print("SCANNER_STATE_BOUNDARY_PRESERVED=PASS")
print("NEWS_STATE_BOUNDARY_PRESERVED=PASS")
print("R48_CONTRACT=PASS")
