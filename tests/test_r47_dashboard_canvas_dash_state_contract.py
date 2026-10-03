from pathlib import Path
import re

P = Path("dashboard/command_center_v3.py")
src = P.read_text()

print("=== R47 CANVAS DASH STATE CONTRACT ===")

# ------------------------------------------------------------
# Previous boundaries must remain intact.
# ------------------------------------------------------------
assert "/* R45_DASHBOARD_CANVAS_SIZE_STATE_START */" in src
assert "/* R45_DASHBOARD_CANVAS_SIZE_STATE_END */" in src
assert "/* R46_DASHBOARD_CANVAS_CONTEXT_STATE_START */" in src
assert "/* R46_DASHBOARD_CANVAS_CONTEXT_STATE_END */" in src
assert "/* R47_DASHBOARD_CANVAS_DASH_STATE_START */" in src
assert "/* R47_DASHBOARD_CANVAS_DASH_STATE_END */" in src

assert "function setDashboardCanvasSize(canvas,width,height){" in src
assert "function setDashboardCanvasContextState(ctx,name,value){" in src
assert "function setDashboardCanvasLineDash(ctx,dash){" in src

print("R45_BOUNDARY=PASS")
print("R46_BOUNDARY=PASS")
print("R47_BOUNDARY=PASS")

# ------------------------------------------------------------
# renderChart() remains present and preserves save/restore.
# ------------------------------------------------------------
assert "function renderChart(){" in src
assert "ctx.save();" in src
assert "ctx.restore();" in src

render_match = re.search(
    r"function renderChart\(\)\{(.*?)\n\}",
    src,
    re.S,
)
assert render_match, "renderChart() body not found"
render_body = render_match.group(1)

print("RENDER_CHART_FLOW=PASS")

# ------------------------------------------------------------
# Direct setLineDash() must be removed from renderChart().
# Exactly one helper call must remain.
# ------------------------------------------------------------
direct_dash = re.findall(
    r"\bctx\.setLineDash\s*\(",
    render_body,
)
assert direct_dash == []

helper_dash = re.findall(
    r"setDashboardCanvasLineDash\(\s*ctx\s*,\s*dash\s*\)",
    render_body,
)
assert helper_dash == [
    "setDashboardCanvasLineDash(ctx,dash)"
]

print("DIRECT_SETLINEDASH_REMOVED=PASS")
print("R47_SETLINEDASH_ROUTED=1")

# ------------------------------------------------------------
# Preserve save -> dash -> restore ordering.
# ------------------------------------------------------------
save_pos = render_body.find("ctx.save();")
dash_pos = render_body.find(
    "setDashboardCanvasLineDash(ctx,dash);"
)
restore_pos = render_body.find("ctx.restore();")

assert save_pos >= 0
assert dash_pos >= 0
assert restore_pos >= 0
assert save_pos < dash_pos < restore_pos

print("SAVE_DASH_RESTORE_ORDER=PASS")

# ------------------------------------------------------------
# Helper itself must contain the sole direct setLineDash
# mutation.
# ------------------------------------------------------------
helper_match = re.search(
    r"/\* R47_DASHBOARD_CANVAS_DASH_STATE_START \*/"
    r"(.*?)"
    r"/\* R47_DASHBOARD_CANVAS_DASH_STATE_END \*/",
    src,
    re.S,
)
assert helper_match

helper = helper_match.group(1)

assert "function setDashboardCanvasLineDash(ctx,dash){" in helper
assert "if(!ctx||typeof ctx.setLineDash!==\"function\")return;" in helper
assert "ctx.setLineDash(dash);" in helper

print("R47_HELPER_DIRECT_MUTATION=PASS")

# ------------------------------------------------------------
# No execution-authority identifiers inside the R47 helper.
# ------------------------------------------------------------
for forbidden in [
    "IDM",
    "TradePlanner",
    "RiskManager",
    "ExecutionConfirmation",
    "ExecutionGateway",
    "execution_intent",
    "place_order",
    "submit_order",
]:
    assert forbidden not in helper

print("R47_HELPER_AUTHORITY=PASS")

# ------------------------------------------------------------
# R46 property boundary remains exactly five direct property
# assignments, all inside the R46 helper.
# ------------------------------------------------------------
direct_props = re.findall(
    r"\bctx\.(fillStyle|font|strokeStyle|lineWidth|textAlign)\s*=",
    src,
)

assert direct_props == [
    "fillStyle",
    "font",
    "strokeStyle",
    "lineWidth",
    "textAlign",
]

print("R46_CTX_PROPERTY_BOUNDARY=PASS")

# ------------------------------------------------------------
# R47 must not introduce application state, storage, network,
# or execution mutation.
# ------------------------------------------------------------
r47_block = helper

for forbidden in [
    "state.",
    "sessionStorage",
    "localStorage",
    "fetch(",
    "XMLHttpRequest",
    "IDM",
    "TradePlanner",
    "RiskManager",
    "ExecutionConfirmation",
    "ExecutionGateway",
    "execution_intent",
    "place_order",
    "submit_order",
]:
    assert forbidden not in r47_block

print("R47_NO_APP_STATE=PASS")
print("R47_NO_EXECUTION_AUTHORITY=PASS")
print("R47_CONTRACT=PASS")
