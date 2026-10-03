from pathlib import Path
import re

DASHBOARD = Path("dashboard/command_center_v3.py")
text = DASHBOARD.read_text(encoding="utf-8")

R32_START = "/* R32_DASHBOARD_CONTEXT_ACCESS_START */"
R32_END = "/* R32_DASHBOARD_CONTEXT_ACCESS_END */"

R31_START = "/* R31_DASHBOARD_CONTEXT_RESOLUTION_START */"
R31_END = "/* R31_DASHBOARD_CONTEXT_RESOLUTION_END */"

R28_START = "/* R28_DASHBOARD_STATE_MUTATION_START */"
R28_END = "/* R28_DASHBOARD_STATE_MUTATION_END */"

results = []


def check(name, condition):
    results.append((name, bool(condition)))
    print(f"{name}={'PASS' if condition else 'FAIL'}")


def span(start_marker, end_marker):
    start = text.find(start_marker)
    end = text.find(end_marker)
    if start < 0 or end < 0 or end < start:
        return None
    return start, end + len(end_marker)


def mask_span(value, bounds):
    if bounds is None:
        return value
    start, end = bounds
    return value[:start] + (" " * (end - start)) + value[end:]


check("R32_START_MARKER", R32_START in text)
check("R32_END_MARKER", R32_END in text)

check("R31_START_MARKER", R31_START in text)
check("R31_END_MARKER", R31_END in text)

check(
    "GET_ACTIVE_SYMBOL_EXISTS",
    "function getActiveSymbol()" in text,
)

check(
    "GET_ACTIVE_INTERVAL_EXISTS",
    "function getActiveInterval()" in text,
)

check(
    "GET_ACTIVE_MODE_EXISTS",
    "function getActiveMode()" in text,
)

check(
    "GET_ACTIVE_SYMBOL_CALLS",
    text.count("getActiveSymbol()") >= 3,
)

check(
    "GET_ACTIVE_INTERVAL_CALLS",
    text.count("getActiveInterval()") >= 3,
)

check(
    "GET_ACTIVE_MODE_CALLS",
    text.count("getActiveMode()") >= 2,
)

# Remove authoritative/allowed regions before checking for direct context reads.
outside = text

for bounds in (
    span(R31_START, R31_END),
    span(R28_START, R28_END),
):
    outside = mask_span(outside, bounds)

# The initial state declaration is the canonical initial value, not a read-path.
state_decl = re.search(
    r"const state=\{.*?\n\};",
    outside,
    re.S,
)

if state_decl:
    outside = (
        outside[:state_decl.start()]
        + (" " * (state_decl.end() - state_decl.start()))
        + outside[state_decl.end():]
    )

check(
    "NO_DIRECT_ACTIVE_SYMBOL_READ_OUTSIDE_ACCESSOR_BOUNDARIES",
    not re.search(r"\bstate\.symbol\b", outside),
)

check(
    "NO_DIRECT_ACTIVE_INTERVAL_READ_OUTSIDE_ACCESSOR_BOUNDARIES",
    not re.search(r"\bstate\.interval\b", outside),
)

check(
    "NO_DIRECT_ACTIVE_MODE_READ_OUTSIDE_ACCESSOR_BOUNDARIES",
    not re.search(r"\bstate\.mode\b", outside),
)

check(
    "NO_DIRECT_SYMBOL_STRING_FALLBACK",
    'String(state.symbol||"").trim()' not in outside,
)

# R32 must remain a read-path/UI hardening boundary.
r32 = ""
r32_bounds = span(R32_START, R32_END)

if r32_bounds:
    r32 = text[r32_bounds[0] : r32_bounds[1]]

check(
    "R32_NO_STATE_MUTATION",
    not re.search(
        r"state\.[A-Za-z_][A-Za-z0-9_]*\s*[\+\-\*/]?=",
        r32,
    )
    and not re.search(
        r"state\.[A-Za-z_][A-Za-z0-9_]*\[[^]]+\]\s*=",
        r32,
    ),
)

check(
    "R32_NO_FILTER_MUTATION",
    "setDashboardFilter(" not in r32
    and "dashboardFilters[" not in r32,
)

check(
    "R32_NO_STORAGE",
    "sessionStorage" not in r32 and "localStorage" not in r32,
)

check(
    "R32_NO_NETWORK",
    "fetch(" not in r32,
)

# Execution authority must remain completely outside this dashboard hardening phase.
authority_tokens = (
    "execution_intent",
    "place_order",
    "submit_order",
    "tradeplanner",
    "riskmanager",
    "executionconfirmation",
    "executiongateway",
    "state.decision",
    "state.trade",
    "state.risk",
    "state.execution",
)

for token in authority_tokens:
    check(
        f"NO_{token.upper().replace('.', '_')}",
        token not in r32.lower(),
    )

# Prior boundaries must remain intact.
for marker in (
    "R24_DASHBOARD_TABS_UI_START",
    "R25_DASHBOARD_TABS_HARDENING_START",
    "R26_DASHBOARD_TAB_STATE_START",
    "R27_WATCHLIST_STATE_START",
    "R28_DASHBOARD_STATE_MUTATION_START",
    "R29_CHART_INDICATOR_STATE_START",
    "R30_DASHBOARD_FILTER_STATE_START",
    "R31_DASHBOARD_CONTEXT_RESOLUTION_START",
):
    check(f"PRESERVES_{marker}", marker in text)

failed = [name for name, ok in results if not ok]
print(f"R32_CONTRACT={'PASS' if not failed else 'FAIL'} ({sum(ok for _, ok in results)}/{len(results)})")

if failed:
    raise SystemExit(1)
