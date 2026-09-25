from pathlib import Path
import re

P = Path("dashboard/command_center_v3.py")
src = P.read_text()

print("=== R50 DASHBOARD MUTATION CLOSURE CONTRACT ===")

# ------------------------------------------------------------
# All established release boundaries must still exist.
# ------------------------------------------------------------
boundaries = [
    ("R45", "R45_DASHBOARD_CANVAS_SIZE_STATE_START",
            "R45_DASHBOARD_CANVAS_SIZE_STATE_END"),
    ("R46", "R46_DASHBOARD_CANVAS_CONTEXT_STATE_START",
            "R46_DASHBOARD_CANVAS_CONTEXT_STATE_END"),
    ("R47", "R47_DASHBOARD_CANVAS_DASH_STATE_START",
            "R47_DASHBOARD_CANVAS_DASH_STATE_END"),
    ("R48", "R48_DASHBOARD_STATE_SNAPSHOT_START",
            "R48_DASHBOARD_STATE_SNAPSHOT_END"),
    ("R49S", "R49_DASHBOARD_SCANNER_STATE_START",
            "R49_DASHBOARD_SCANNER_STATE_END"),
    ("R49N", "R49_DASHBOARD_NEWS_STATE_START",
            "R49_DASHBOARD_NEWS_STATE_END"),
]

for name, start, end in boundaries:
    assert f"/* {start} */" in src
    assert f"/* {end} */" in src

print("R45_BOUNDARY=PASS")
print("R46_BOUNDARY=PASS")
print("R47_BOUNDARY=PASS")
print("R48_BOUNDARY=PASS")
print("R49_SCANNER_BOUNDARY=PASS")
print("R49_NEWS_BOUNDARY=PASS")

# ------------------------------------------------------------
# Canonical state assignments must remain exactly inside the
# established owners.
# ------------------------------------------------------------
expected_state_assignments = {
    "ui": 1,
    "candles": 1,
    "scanner": 1,
    "news": 1,
    "symbol": 1,
}

for field, expected in expected_state_assignments.items():
    count = len(
        re.findall(
            rf"\bstate\.{re.escape(field)}\s*=",
            src,
        )
    )
    assert count == expected, (
        f"state.{field} direct assignment count={count}, "
        f"expected={expected}"
    )

print("CANONICAL_STATE_ASSIGNMENTS=PASS")

# ------------------------------------------------------------
# Each canonical assignment is inside the correct helper.
# ------------------------------------------------------------
ownership = [
    (
        "state.ui=d.ui;",
        "R48_DASHBOARD_STATE_SNAPSHOT_START",
        "R48_DASHBOARD_STATE_SNAPSHOT_END",
    ),
    (
        "state.candles=Array.isArray(d.candles)?d.candles:[];",
        "R48_DASHBOARD_STATE_SNAPSHOT_START",
        "R48_DASHBOARD_STATE_SNAPSHOT_END",
    ),
    (
        "state.scanner=data;",
        "R49_DASHBOARD_SCANNER_STATE_START",
        "R49_DASHBOARD_SCANNER_STATE_END",
    ),
    (
        "state.news=data;",
        "R49_DASHBOARD_NEWS_STATE_START",
        "R49_DASHBOARD_NEWS_STATE_END",
    ),
]

for assignment, start, end in ownership:
    m = re.search(
        re.escape(f"/* {start} */") +
        r"(.*?)" +
        re.escape(f"/* {end} */"),
        src,
        re.S,
    )
    assert m
    assert assignment in m.group(1)

print("CANONICAL_STATE_OWNERSHIP=PASS")

# ------------------------------------------------------------
# R28 symbol ownership.
# ------------------------------------------------------------
r28 = re.search(
    r"/\* R28_DASHBOARD_STATE_MUTATION_START \*/"
    r"(.*?)"
    r"/\* R28_DASHBOARD_STATE_MUTATION_END \*/",
    src,
    re.S,
)

assert r28
assert "state.symbol=" in r28.group(1)

print("R28_SYMBOL_OWNERSHIP=PASS")

# ------------------------------------------------------------
# R29 chart indicator ownership.
# ------------------------------------------------------------
r29 = re.search(
    r"/\* R29_CHART_INDICATOR_STATE_START \*/"
    r"(.*?)"
    r"/\* R29_CHART_INDICATOR_STATE_END \*/",
    src,
    re.S,
)

assert r29
assert "state.chartIndicators[name]=!state.chartIndicators[name];" in r29.group(1)

# No equivalent direct chart-indicator mutation outside R29.
r29_start, r29_end = r29.span()
outside_r29 = src[:r29_start] + src[r29_end:]

assert "state.chartIndicators[name]=!state.chartIndicators[name];" not in outside_r29

print("R29_INDICATOR_OWNERSHIP=PASS")

# ------------------------------------------------------------
# Canvas presentation mutations:
# only established helper internals are allowed.
# ------------------------------------------------------------
ctx_props = re.findall(
    r"\bctx\.(fillStyle|font|strokeStyle|lineWidth|textAlign)\s*=",
    src,
)

assert ctx_props == [
    "fillStyle",
    "font",
    "strokeStyle",
    "lineWidth",
    "textAlign",
]

assert len(re.findall(r"\bctx\.setLineDash\s*\(", src)) == 1

print("CANVAS_STATE_CLOSED=PASS")

# ------------------------------------------------------------
# DOM presentation mutation assignments:
# direct assignments are allowed only inside established helpers.
# ------------------------------------------------------------
dom_assignments = [
    "element.value=",
    "element.disabled=",
    "element.hidden=",
    "element.className=",
    "element.scrollTop=",
    "element.textContent=",
    "element.innerHTML=",
    "canvas.width=",
    "canvas.height=",
]

for assignment in dom_assignments:
    assert src.count(assignment) == 1

print("DOM_STATE_HELPER_INTERNALS=PASS")

# ------------------------------------------------------------
# No new browser-global mutation.
# ------------------------------------------------------------
assert not re.search(
    r"\b(window|document)\.[A-Za-z_$][A-Za-z0-9_$]*\s*=",
    src,
)

print("GLOBAL_MUTATION=NONE")

# ------------------------------------------------------------
# No direct state writes for execution authority.
# ------------------------------------------------------------
for forbidden in [
    "state.decision=",
    "state.trade=",
    "state.risk=",
    "state.execution=",
    "execution_intent",
    "place_order",
    "submit_order",
]:
    assert forbidden not in src

print("EXECUTION_STATE_MUTATION=NONE")

# ------------------------------------------------------------
# Runtime scheduling is intentionally outside the state
# mutation boundary.
# ------------------------------------------------------------
assert "setInterval(load,10000);" in src

print("TIMER_RUNTIME_BOUNDARY=INTENTIONAL")

print("R50_MUTATION_SURFACE=CLOSED")
print("R50_IMPLEMENTATION=NOT_REQUIRED")
print("R50_CONTRACT=PASS")
