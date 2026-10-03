from pathlib import Path
import re

DASHBOARD = Path("dashboard/command_center_v3.py")
text = DASHBOARD.read_text(encoding="utf-8")

R33_START = "/* R33_DASHBOARD_CONTROL_INPUT_ACCESS_START */"
R33_END = "/* R33_DASHBOARD_CONTROL_INPUT_ACCESS_END */"

BOUNDARIES = (
    ("R24", "/* R24_DASHBOARD_TABS_UI_START */", "/* R24_DASHBOARD_TABS_UI_END */"),
    ("R25", "/* R25_DASHBOARD_TABS_HARDENING_START */", "/* R25_DASHBOARD_TABS_HARDENING_END */"),
    ("R26", "/* R26_DASHBOARD_TAB_STATE_START */", "/* R26_DASHBOARD_TAB_STATE_END */"),
    ("R27", "/* R27_WATCHLIST_STATE_START */", "/* R27_WATCHLIST_STATE_END */"),
    ("R28", "/* R28_DASHBOARD_STATE_MUTATION_START */", "/* R28_DASHBOARD_STATE_MUTATION_END */"),
    ("R29", "/* R29_CHART_INDICATOR_STATE_START */", "/* R29_CHART_INDICATOR_STATE_END */"),
    ("R30", "/* R30_DASHBOARD_FILTER_STATE_START */", "/* R30_DASHBOARD_FILTER_STATE_END */"),
    ("R31", "/* R31_DASHBOARD_CONTEXT_RESOLUTION_START */", "/* R31_DASHBOARD_CONTEXT_RESOLUTION_END */"),
    ("R32", "/* R32_DASHBOARD_CONTEXT_ACCESS_START */", "/* R32_DASHBOARD_CONTEXT_ACCESS_END */"),
)

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


# Work only on JavaScript contained in the dashboard script.
script_start = text.find("<script>")
script_end = text.find("</script>", script_start)

if script_start < 0 or script_end < 0:
    raise SystemExit("Dashboard script block not found")

js = text[script_start:script_end]

r33_bounds = span(R33_START, R33_END)

check(
    "R33_START_MARKER",
    R33_START in text,
)

check(
    "R33_END_MARKER",
    R33_END in text,
)

check(
    "CONTROL_VALUE_READER_EXISTS",
    "function getDashboardControlValue(" in js,
)

check(
    "CONTROL_VALUE_WRITER_EXISTS",
    "function setDashboardControlValue(" in js,
)

# Remove the R33 boundary before testing callers.
outside = js

if r33_bounds:
    js_start = script_start
    rel_start = r33_bounds[0] - js_start
    rel_end = r33_bounds[1] - js_start
    outside = outside[:rel_start] + (" " * (rel_end - rel_start)) + outside[rel_end:]

# Direct value access is the behavior R33 centralizes.
direct_value_access = re.findall(
    r"\b[A-Za-z_$][A-Za-z0-9_$]*\.value\b",
    outside,
)

check(
    "NO_DIRECT_CONTROL_VALUE_ACCESS_OUTSIDE_BOUNDARY",
    not direct_value_access,
)

check(
    "NO_DIRECT_VALUE_ASSIGNMENT_OUTSIDE_BOUNDARY",
    not re.search(
        r"\b[A-Za-z_$][A-Za-z0-9_$]*\.value\s*=",
        outside,
    ),
)

check(
    "CONTROL_READER_USES_VALUE",
    re.search(
        r"function getDashboardControlValue\([\s\S]*?\.value",
        js,
    ) is not None,
)

check(
    "CONTROL_WRITER_ASSIGNMENT_IS_CENTRAL",
    re.search(
        r"function setDashboardControlValue\([\s\S]*?\.value\s*=",
        js,
    ) is not None,
)

# The boundary must remain UI-only.
r33 = ""

if r33_bounds:
    r33 = text[r33_bounds[0]:r33_bounds[1]]

check(
    "R33_NO_STATE_MUTATION",
    not re.search(
        r"state\.[A-Za-z_][A-Za-z0-9_]*\s*[\+\-\*/]?=",
        r33,
    )
    and not re.search(
        r"state\.[A-Za-z_][A-Za-z0-9_]*\[[^]]+\]\s*=",
        r33,
    ),
)

check(
    "R33_NO_FILTER_MUTATION",
    "setDashboardFilter(" not in r33
    and "dashboardFilters[" not in r33,
)

check(
    "R33_NO_STORAGE",
    "sessionStorage" not in r33
    and "localStorage" not in r33,
)

check(
    "R33_NO_NETWORK",
    "fetch(" not in r33,
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
        token not in r33.lower(),
    )

# Preserve previous architectural boundaries.
for name, start, end in BOUNDARIES:
    check(f"PRESERVES_{name}_START", start in text)
    check(f"PRESERVES_{name}_END", end in text)

failed = [name for name, ok in results if not ok]

print(
    f"R33_CONTRACT={'PASS' if not failed else 'FAIL'} "
    f"({sum(ok for _, ok in results)}/{len(results)})"
)

if failed:
    raise SystemExit(1)
