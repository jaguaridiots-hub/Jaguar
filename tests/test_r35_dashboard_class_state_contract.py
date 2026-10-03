from pathlib import Path
import re

DASHBOARD = Path("dashboard/command_center_v3.py")
text = DASHBOARD.read_text(encoding="utf-8")

R35_START = "/* R35_DASHBOARD_CLASS_STATE_START */"
R35_END = "/* R35_DASHBOARD_CLASS_STATE_END */"

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

r35_bounds = span(R35_START, R35_END)

check("R35_START_MARKER", R35_START in text)
check("R35_END_MARKER", R35_END in text)

check(
    "CLASS_STATE_SETTER_EXISTS",
    "function setDashboardClassState(" in js,
)

check(
    "CLASS_STATE_SETTER_USES_CLASSLIST",
    re.search(
        r"function setDashboardClassState\([\s\S]*?classList\.toggle",
        js,
    ) is not None,
)

outside = js

if r35_bounds:
    rel_start = r35_bounds[0] - script_start
    rel_end = r35_bounds[1] - script_start
    outside = (
        outside[:rel_start]
        + (" " * (rel_end - rel_start))
        + outside[rel_end:]
    )

direct_class_mutations = re.findall(
    r"\.classList\.(?:toggle|add|remove)\s*\(",
    outside,
)

check(
    "NO_DIRECT_CLASS_MUTATION_OUTSIDE_BOUNDARY",
    not direct_class_mutations,
)

check(
    "NO_DIRECT_CLASS_TOGGLE_OUTSIDE_BOUNDARY",
    ".classList.toggle(" not in outside,
)

check(
    "NO_DIRECT_CLASS_ADD_OUTSIDE_BOUNDARY",
    ".classList.add(" not in outside,
)

check(
    "NO_DIRECT_CLASS_REMOVE_OUTSIDE_BOUNDARY",
    ".classList.remove(" not in outside,
)

r35 = ""

if r35_bounds:
    r35 = text[r35_bounds[0]:r35_bounds[1]]

check(
    "R35_NO_STATE_MUTATION",
    not re.search(
        r"state\.[A-Za-z_][A-Za-z0-9_]*\s*[\+\-\*/]?=",
        r35,
    )
    and not re.search(
        r"state\.[A-Za-z_][A-Za-z0-9_]*\[[^]]+\]\s*=",
        r35,
    ),
)

check(
    "R35_NO_FILTER_MUTATION",
    "setDashboardFilter(" not in r35
    and "dashboardFilters[" not in r35,
)

check(
    "R35_NO_STORAGE",
    "sessionStorage" not in r35
    and "localStorage" not in r35,
)

check(
    "R35_NO_NETWORK",
    "fetch(" not in r35,
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
        token not in r35.lower(),
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
):
    check(f"PRESERVES_{marker}", marker in text)

failed = [name for name, ok in results if not ok]

print(
    f"R35_CONTRACT={'PASS' if not failed else 'FAIL'} "
    f"({sum(ok for _, ok in results)}/{len(results)})"
)

if failed:
    raise SystemExit(1)
