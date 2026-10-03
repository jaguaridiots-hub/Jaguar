from pathlib import Path
import re

DASHBOARD = Path("dashboard/command_center_v3.py")
text = DASHBOARD.read_text(encoding="utf-8")

R34_START = "/* R34_DASHBOARD_CONTROL_DISABLED_STATE_START */"
R34_END = "/* R34_DASHBOARD_CONTROL_DISABLED_STATE_END */"

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


def mask(value, bounds):
    if bounds is None:
        return value
    start, end = bounds
    return value[:start] + (" " * (end - start)) + value[end:]


script_start = text.find("<script>")
script_end = text.find("</script>", script_start)

if script_start < 0 or script_end < 0:
    raise SystemExit("Dashboard script block not found")

js = text[script_start:script_end]

r34_bounds = span(R34_START, R34_END)

check("R34_START_MARKER", R34_START in text)
check("R34_END_MARKER", R34_END in text)

check(
    "CONTROL_DISABLED_SETTER_EXISTS",
    "function setDashboardControlDisabled(" in js,
)

outside = js

if r34_bounds:
    rel_start = r34_bounds[0] - script_start
    rel_end = r34_bounds[1] - script_start
    outside = (
        outside[:rel_start]
        + (" " * (rel_end - rel_start))
        + outside[rel_end:]
    )

disabled_assignments = re.findall(
    r"\b[A-Za-z_$][A-Za-z0-9_$]*\.disabled\s*=",
    outside,
)

check(
    "NO_DIRECT_CONTROL_DISABLED_ASSIGNMENT_OUTSIDE_BOUNDARY",
    not disabled_assignments,
)

check(
    "NO_DIRECT_DISABLED_ASSIGNMENT_OUTSIDE_BOUNDARY",
    not re.search(
        r"\b[A-Za-z_$][A-Za-z0-9_$]*\.disabled\s*=\s*(?:true|false)",
        outside,
    ),
)

check(
    "DISABLED_SETTER_USES_PROPERTY",
    re.search(
        r"function setDashboardControlDisabled\([\s\S]*?\.disabled\s*=",
        js,
    )
    is not None,
)

r34 = ""

if r34_bounds:
    r34 = text[r34_bounds[0]:r34_bounds[1]]

check(
    "R34_NO_STATE_MUTATION",
    not re.search(
        r"state\.[A-Za-z_][A-Za-z0-9_]*\s*[\+\-\*/]?=",
        r34,
    )
    and not re.search(
        r"state\.[A-Za-z_][A-Za-z0-9_]*\[[^]]+\]\s*=",
        r34,
    ),
)

check(
    "R34_NO_FILTER_MUTATION",
    "setDashboardFilter(" not in r34
    and "dashboardFilters[" not in r34,
)

check(
    "R34_NO_STORAGE",
    "sessionStorage" not in r34
    and "localStorage" not in r34,
)

check(
    "R34_NO_NETWORK",
    "fetch(" not in r34,
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
        token not in r34.lower(),
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
):
    check(f"PRESERVES_{marker}", marker in text)

failed = [name for name, ok in results if not ok]

print(
    f"R34_CONTRACT={'PASS' if not failed else 'FAIL'} "
    f"({sum(ok for _, ok in results)}/{len(results)})"
)

if failed:
    raise SystemExit(1)
