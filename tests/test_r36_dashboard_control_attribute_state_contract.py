from pathlib import Path
import re

DASHBOARD = Path("dashboard/command_center_v3.py")
text = DASHBOARD.read_text(encoding="utf-8")

R36_START = "/* R36_DASHBOARD_CONTROL_ATTRIBUTE_STATE_START */"
R36_END = "/* R36_DASHBOARD_CONTROL_ATTRIBUTE_STATE_END */"

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


script_start = text.find("<script>")
script_end = text.find("</script>", script_start)

if script_start < 0 or script_end < 0:
    raise SystemExit("Dashboard script block not found")

js = text[script_start:script_end]

r36_bounds = span(R36_START, R36_END)

check("R36_START_MARKER", R36_START in text)
check("R36_END_MARKER", R36_END in text)

check(
    "CONTROL_ATTRIBUTE_SETTER_EXISTS",
    "function setDashboardControlAttribute(" in js,
)

check(
    "CONTROL_ATTRIBUTE_SETTER_USES_SETATTRIBUTE",
    re.search(
        r"function setDashboardControlAttribute\([\s\S]*?\.setAttribute\(",
        js,
    ) is not None,
)

outside = js

if r36_bounds:
    rel_start = r36_bounds[0] - script_start
    rel_end = r36_bounds[1] - script_start
    outside = (
        outside[:rel_start]
        + (" " * (rel_end - rel_start))
        + outside[rel_end:]
    )

check(
    "NO_DIRECT_SETATTRIBUTE_OUTSIDE_BOUNDARY",
    ".setAttribute(" not in outside,
)

check(
    "NO_DIRECT_REMOVEATTRIBUTE_OUTSIDE_BOUNDARY",
    ".removeAttribute(" not in outside,
)

check(
    "NO_DIRECT_TOGGLEATTRIBUTE_OUTSIDE_BOUNDARY",
    ".toggleAttribute(" not in outside,
)

check(
    "ARIA_SELECTED_PRESERVED",
    '"aria-selected"' in js,
)

check(
    "TABINDEX_PRESERVED",
    '"tabindex"' in js,
)

r36 = ""

if r36_bounds:
    r36 = text[r36_bounds[0]:r36_bounds[1]]

check(
    "R36_NO_STATE_MUTATION",
    not re.search(
        r"state\.[A-Za-z_][A-Za-z0-9_]*\s*[\+\-\*/]?=",
        r36,
    )
    and not re.search(
        r"state\.[A-Za-z_][A-Za-z0-9_]*\[[^]]+\]\s*=",
        r36,
    ),
)

check(
    "R36_NO_FILTER_MUTATION",
    "setDashboardFilter(" not in r36
    and "dashboardFilters[" not in r36,
)

check(
    "R36_NO_STORAGE",
    "sessionStorage" not in r36
    and "localStorage" not in r36,
)

check(
    "R36_NO_NETWORK",
    "fetch(" not in r36,
)

for token in (
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
):
    check(
        f"NO_{token.upper().replace('.', '_')}",
        token not in r36.lower(),
    )

for marker in (
    "R24_DASHBOARD_TABS_UI_START",
    "R25_DASHBOARD_TABS_HARDENING_START",
    "R26_DASHBOARD_TAB_STATE_START",
    "R27_WATCHLIST_STATE_START",
    "R28_DASHBOARD_STATE_MUTATION_START",
    "R29_CHART_INDICATOR_STATE_START",
    "R30_DASHBOARD_FILTER_STATE_START",
    "R31_DASHBOARD_CONTEXT_RESOLUTION_START",
    "R32_DASHBOARD_CONTEXT_ACCESS_START",
    "R33_DASHBOARD_CONTROL_INPUT_ACCESS_START",
    "R34_DASHBOARD_CONTROL_DISABLED_STATE_START",
    "R35_DASHBOARD_CLASS_STATE_START",
):
    check(f"PRESERVES_{marker}", marker in text)

failed = [name for name, ok in results if not ok]

print(
    f"R36_CONTRACT={'PASS' if not failed else 'FAIL'} "
    f"({sum(ok for _, ok in results)}/{len(results)})"
)

if failed:
    raise SystemExit(1)
