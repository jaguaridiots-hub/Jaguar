from pathlib import Path
import re

SOURCE_PATH = Path("dashboard/command_center_v3.py")
SOURCE = SOURCE_PATH.read_text()

START = "/* R43_DASHBOARD_EVENT_LISTENER_BINDING_START */"
END = "/* R43_DASHBOARD_EVENT_LISTENER_BINDING_END */"

assert START in SOURCE
assert END in SOURCE

start = SOURCE.index(START)
end = SOURCE.index(END, start)

HELPER = SOURCE[start:end]

# ------------------------------------------------------------
# Canonical helper
# ------------------------------------------------------------

assert "function setDashboardEventListener(" in HELPER

assert re.search(
    r'if\(\!element\|\|typeof eventName!=="string"\)return;',
    HELPER,
)

assert re.search(
    r'element\.addEventListener\(',
    HELPER,
)

assert "eventName," in HELPER
assert "handler" in HELPER

# ------------------------------------------------------------
# Exactly one helper definition
# ------------------------------------------------------------

assert len(
    re.findall(r'function setDashboardEventListener\(', SOURCE)
) == 1

# ------------------------------------------------------------
# Direct addEventListener must exist only inside the helper.
# ------------------------------------------------------------

helper_ranges = [(start, end + len(END))]

matches = list(
    re.finditer(
        r'\.addEventListener\(',
        SOURCE,
    )
)

for match in matches:
    assert any(
        begin <= match.start() < finish
        for begin, finish in helper_ranges
    ), "Direct addEventListener remains outside R43 helper"

assert len(matches) == 1, (
    "Expected exactly one direct addEventListener call "
    "inside the canonical R43 helper"
)

# ------------------------------------------------------------
# The two existing event-registration sites must be routed
# through the canonical helper.
# ------------------------------------------------------------

assert re.search(
    r'setDashboardEventListener\(\s*'
    r'document\.getElementById\(\s*"aiForm"\s*\)\s*,\s*'
    r'"submit"\s*,',
    SOURCE,
)

assert re.search(
    r'setDashboardEventListener\(\s*'
    r'window\s*,\s*"resize"\s*,',
    SOURCE,
)

assert SOURCE.count(
    'setDashboardEventListener('
) == 3
# 1 definition + 2 production call sites

# ------------------------------------------------------------
# Preserve the existing event semantics.
# ------------------------------------------------------------

ai_form = SOURCE[
    SOURCE.index('document.getElementById("aiForm")')
    :
]

assert "e.preventDefault();" in ai_form
assert 'fetch("/assistant/chat"' in ai_form

# After R43 the old direct listener syntax must disappear,
# while the resize behavior itself must still call renderChart().
assert 'window.addEventListener(' not in SOURCE
assert 'renderChart();' in SOURCE

# ------------------------------------------------------------
# R43 must not introduce application-state or execution authority.
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
# Existing R35-R42 boundaries remain present.
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
):
    assert marker in SOURCE

print("R43 EVENT LISTENER CONTRACT: PASS")
