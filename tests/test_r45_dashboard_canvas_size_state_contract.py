from pathlib import Path
import re

SOURCE_PATH = Path("dashboard/command_center_v3.py")
SOURCE = SOURCE_PATH.read_text()

START = "/* R45_DASHBOARD_CANVAS_SIZE_STATE_START */"
END = "/* R45_DASHBOARD_CANVAS_SIZE_STATE_END */"

# ------------------------------------------------------------
# Helper markers
# ------------------------------------------------------------

assert START in SOURCE
assert END in SOURCE

start = SOURCE.index(START)
end = SOURCE.index(END, start)

HELPER = SOURCE[start:end]

# ------------------------------------------------------------
# Canonical helper
# ------------------------------------------------------------

assert "function setDashboardCanvasSize(" in HELPER

assert re.search(
    r'if\(\!canvas\|\|!\("width" in canvas\)\|\|!\("height" in canvas\)\)return;',
    HELPER,
)

assert re.search(
    r'canvas\.width\s*=\s*width;',
    HELPER,
)

assert re.search(
    r'canvas\.height\s*=\s*height;',
    HELPER,
)

# ------------------------------------------------------------
# Exactly one helper definition.
# ------------------------------------------------------------

assert len(
    re.findall(r'function setDashboardCanvasSize\(', SOURCE)
) == 1

# ------------------------------------------------------------
# Direct canvas dimension assignments must exist only inside
# the canonical R45 helper.
# ------------------------------------------------------------

helper_range = (start, end + len(END))

width_matches = list(
    re.finditer(r'\bcanvas\.width\s*=', SOURCE)
)

height_matches = list(
    re.finditer(r'\bcanvas\.height\s*=', SOURCE)
)

assert len(width_matches) == 1, (
    "Expected exactly one direct canvas.width assignment"
)

assert len(height_matches) == 1, (
    "Expected exactly one direct canvas.height assignment"
)

for match in width_matches + height_matches:
    assert helper_range[0] <= match.start() < helper_range[1], (
        "Direct canvas dimension assignment remains outside R45 helper"
    )

# ------------------------------------------------------------
# Existing renderChart() must route through the helper.
# ------------------------------------------------------------

assert SOURCE.count("setDashboardCanvasSize(") == 2
# 1 helper definition + 1 production call site

assert "setDashboardCanvasSize(canvas,width,height);" in SOURCE

# ------------------------------------------------------------
# Preserve chart rendering lifecycle.
# ------------------------------------------------------------

assert "function renderChart(" in SOURCE
assert "canvas.getBoundingClientRect()" in SOURCE
assert "window.devicePixelRatio" in SOURCE
assert 'canvas.getContext("2d")' in SOURCE
assert "ctx.clearRect(" in SOURCE

# The canvas helper must not absorb drawing-context state.
assert "ctx.fillStyle" not in HELPER
assert "ctx.strokeStyle" not in HELPER
assert "ctx.lineWidth" not in HELPER
assert "ctx.font" not in HELPER
assert "ctx.textAlign" not in HELPER

# ------------------------------------------------------------
# No application state / execution authority in R45 helper.
# ------------------------------------------------------------

assert not re.search(
    r'\bstate\.(?:decision|trade|risk|execution)\s*=',
    HELPER,
)

for forbidden in (
    "execution_intent",
    "place_order",
    "submit_order",
    "TradePlanner",
    "RiskManager",
    "ExecutionConfirmation",
    "ExecutionGateway",
):
    assert forbidden not in HELPER

# ------------------------------------------------------------
# Preserve all previous state boundaries.
# ------------------------------------------------------------

for marker in (
    "R35_DASHBOARD_CLASS_STATE_START",
    "R36_DASHBOARD_CONTROL_ATTRIBUTE_STATE_START",
    "R37_DASHBOARD_VISIBILITY_STATE_START",
    "R38_DASHBOARD_CLASSNAME_STATE_START",
    "R39_DASHBOARD_SCROLL_STATE_START",
    "R40_DASHBOARD_EVENT_BINDING_START",
    "R41_DASHBOARD_DATASET_STATE_START",
    "R42_DASHBOARD_TEXT_CONTENT_STATE_START",
    "R42_DASHBOARD_INNERHTML_STATE_START",
    "R42_DASHBOARD_HTML_APPEND_STATE_START",
    "R43_DASHBOARD_EVENT_LISTENER_BINDING_START",
    "R44_DASHBOARD_FOCUS_STATE_START",
):
    assert marker in SOURCE

# ------------------------------------------------------------
# R45 remains canvas-only.
# ------------------------------------------------------------

assert "setDashboardTextContent(" in SOURCE
assert "setDashboardInnerHTML(" in SOURCE
assert "appendDashboardHTML(" in SOURCE
assert "setDashboardEventListener(" in SOURCE
assert "setDashboardFocus(" in SOURCE

print("R45 CANVAS SIZE STATE CONTRACT: PASS")
