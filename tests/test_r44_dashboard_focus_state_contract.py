from pathlib import Path
import re

SOURCE_PATH = Path("dashboard/command_center_v3.py")
SOURCE = SOURCE_PATH.read_text()

START = "/* R44_DASHBOARD_FOCUS_STATE_START */"
END = "/* R44_DASHBOARD_FOCUS_STATE_END */"

assert START in SOURCE
assert END in SOURCE

start = SOURCE.index(START)
end = SOURCE.index(END, start)

HELPER = SOURCE[start:end]

# ------------------------------------------------------------
# Canonical helper
# ------------------------------------------------------------

assert "function setDashboardFocus(" in HELPER

assert re.search(
    r'if\(\!element\|\|typeof element\.focus!=="function"\)return;',
    HELPER,
)

assert re.search(
    r'element\.focus\(',
    HELPER,
)

# ------------------------------------------------------------
# Exactly one helper definition
# ------------------------------------------------------------

assert len(
    re.findall(r'function setDashboardFocus\(', SOURCE)
) == 1

# ------------------------------------------------------------
# Direct focus() must exist only inside the R44 helper.
# ------------------------------------------------------------

matches = list(
    re.finditer(
        r'\.focus\(',
        SOURCE,
    )
)

helper_range = (start, end + len(END))

for match in matches:
    assert helper_range[0] <= match.start() < helper_range[1], (
        "Direct focus() remains outside R44 helper"
    )

assert len(matches) == 1, (
    "Expected exactly one direct focus() call inside R44 helper"
)

# ------------------------------------------------------------
# Existing focus call site must route through helper.
# ------------------------------------------------------------

assert SOURCE.count("setDashboardFocus(") == 2
# 1 definition + 1 production call site

# ------------------------------------------------------------
# No blur/select/click scope added by R44.
# ------------------------------------------------------------

assert not re.search(r'\.blur\(', SOURCE)
assert not re.search(r'\.select\(', SOURCE)
assert not re.search(r'\.click\(', SOURCE)

# ------------------------------------------------------------
# Preserve existing keyboard-navigation behavior.
# ------------------------------------------------------------

assert 'setDashboardEventHandler(button,"onkeydown"' in SOURCE
assert 'focusButton' in SOURCE

# Existing event-binding architecture remains intact.
assert "R40_DASHBOARD_EVENT_BINDING_START" in SOURCE
assert "function setDashboardEventHandler(" in SOURCE

# ------------------------------------------------------------
# R44 helper must not introduce application state or
# execution authority.
# ------------------------------------------------------------

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

assert not re.search(
    r'\bstate\.(?:decision|trade|risk|execution)\s*=',
    HELPER,
)

# ------------------------------------------------------------
# Preserve prior boundaries.
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
):
    assert marker in SOURCE

print("R44 FOCUS STATE CONTRACT: PASS")
