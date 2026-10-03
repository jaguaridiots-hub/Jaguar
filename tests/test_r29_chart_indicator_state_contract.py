from pathlib import Path
import re

PATH = Path("dashboard/command_center_v3.py")
SOURCE = PATH.read_text(encoding="utf-8")

START = "/* R29_CHART_INDICATOR_STATE_START */"
END = "/* R29_CHART_INDICATOR_STATE_END */"


def compact(value):
    return "".join(value.split())


def block():
    if START not in SOURCE or END not in SOURCE:
        return ""

    start = SOURCE.index(START)
    end = SOURCE.index(END, start)
    return SOURCE[start:end + len(END)]


checks = []


def check(name, condition):
    checks.append((name, bool(condition)))


r29 = block()
compact_source = compact(SOURCE)
compact_r29 = compact(r29)


# Marker integrity
check(
    "R29_START_MARKER",
    SOURCE.count(START) == 1,
)

check(
    "R29_END_MARKER",
    SOURCE.count(END) == 1,
)


# Central mutation boundary
check(
    "TOGGLE_CHART_INDICATOR_FUNCTION",
    "function toggleChartIndicator(" in r29,
)

check(
    "INDICATOR_VALIDATION",
    "R29_VALID_CHART_INDICATORS.has" in r29,
)

check(
    "INVALID_INDICATOR_IS_IGNORED",
    "if(!R29_VALID_CHART_INDICATORS.has(name)){" in r29,
)

check(
    "ONLY_CENTRAL_CHART_INDICATOR_MUTATION",
    "state.chartIndicators[name]=!state.chartIndicators[name];" in r29,
)

# Direct mutation count must remain exactly one.
mutations = re.findall(
    r"state\.chartIndicators\[[^]]+\]\s*=",
    SOURCE,
)

check(
    "ONLY_ONE_DIRECT_CHART_INDICATOR_MUTATION",
    len(mutations) == 1,
)

# Toolbar must use the mutation boundary.
toolbar_start = SOURCE.index("function initIndicatorControls(){")
toolbar_end = SOURCE.index(
    "/* R23_SCANNER_ALERT_CONTEXT_UI_START */",
    toolbar_start,
)
toolbar = SOURCE[toolbar_start:toolbar_end]
compact_toolbar = compact(toolbar)

check(
    "TOOLBAR_USES_CENTRAL_SETTER",
    "toggleChartIndicator(name);" in compact_toolbar,
)

check(
    "TOOLBAR_NO_DIRECT_INDICATOR_MUTATION",
    "state.chartIndicators[name]=" not in toolbar,
)

check(
    "TOOLBAR_STILL_RERENDERS_CHART",
    "renderChart();" in toolbar,
)

# No persistence is introduced by R29.
check(
    "R29_HAS_NO_STORAGE_MUTATION",
    "sessionStorage" not in r29
    and "localStorage" not in r29,
)

# Existing indicator defaults remain intact.
for indicator in (
    "EMA20",
    "EMA50",
    "EMA100",
    "EMA200",
    "VWAP",
    "FIB_RETR",
    "FIB_EXT",
):
    check(
        f"DEFAULT_{indicator}_PRESERVED",
        f"{indicator}:true" in compact_source,
    )

# Existing R24-R28 layers remain present.
for marker in (
    "R24_DASHBOARD_TABS_UI_START",
    "R25_DASHBOARD_TABS_HARDENING_START",
    "R26_DASHBOARD_TAB_STATE_START",
    "R27_WATCHLIST_STATE_START",
    "R28_DASHBOARD_STATE_MUTATION_START",
):
    check(
        f"PRESERVES_{marker}",
        marker in SOURCE,
    )


failed = [(name, ok) for name, ok in checks if not ok]

for name, ok in checks:
    print(f"{name}={'PASS' if ok else 'FAIL'}")

if failed:
    print(
        f"R29_CONTRACT=FAIL "
        f"({len(checks)-len(failed)}/{len(checks)})"
    )
    raise SystemExit(1)

print(f"R29_CONTRACT=PASS ({len(checks)}/{len(checks)})")
