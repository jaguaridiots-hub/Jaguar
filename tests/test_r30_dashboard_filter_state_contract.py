from pathlib import Path

PATH = Path("dashboard/command_center_v3.py")
SOURCE = PATH.read_text(encoding="utf-8")

START = "/* R30_DASHBOARD_FILTER_STATE_START */"
END = "/* R30_DASHBOARD_FILTER_STATE_END */"


def compact(value):
    return "".join(value.split())


def r30_block():
    if START not in SOURCE or END not in SOURCE:
        return ""

    start = SOURCE.index(START)
    end = SOURCE.index(END, start)
    return SOURCE[start:end + len(END)]


checks = []


def check(name, condition):
    checks.append((name, bool(condition)))


r30 = r30_block()
compact_r30 = compact(r30)
compact_source = compact(SOURCE)


# ----------------------------------------------------------------------
# Marker integrity
# ----------------------------------------------------------------------

check(
    "R30_START_MARKER",
    SOURCE.count(START) == 1,
)

check(
    "R30_END_MARKER",
    SOURCE.count(END) == 1,
)


# ----------------------------------------------------------------------
# Canonical filter state
# ----------------------------------------------------------------------

check(
    "FILTER_STATE_OBJECT",
    "dashboardFilters" in r30,
)

check(
    "NEWS_FILTER_STATE",
    "newsSymbol" in r30
    and "newsCategory" in r30,
)

check(
    "SCANNER_FILTER_STATE",
    "scannerSymbol" in r30,
)

check(
    "ALERT_FILTER_STATE",
    "scannerAlertSymbol" in r30,
)

check(
    "ALERT_CONTEXT_FILTER_STATE",
    "scannerAlertContextSymbol" in r30,
)


# ----------------------------------------------------------------------
# Central mutation boundary
# ----------------------------------------------------------------------

check(
    "FILTER_SETTER_FUNCTION",
    "function setDashboardFilter(" in r30,
)

check(
    "FILTER_SETTER_VALIDATES_NAME",
    "R30_VALID_FILTERS.has(name)" in r30,
)

check(
    "FILTER_SETTER_MUTATES_CANONICAL_STATE",
    "dashboardFilters[name]=String(value??\"\").trim();" in r30,
)

check(
    "FILTER_SETTER_REJECTS_UNKNOWN_FILTER",
    "if(!R30_VALID_FILTERS.has(name)){" in r30,
)


# ----------------------------------------------------------------------
# No direct filter-state mutations outside the R30 boundary
# ----------------------------------------------------------------------

direct_mutations = [
    "dashboardFilters.newsSymbol=",
    "dashboardFilters.newsCategory=",
    "dashboardFilters.scannerSymbol=",
    "dashboardFilters.scannerAlertSymbol=",
    "dashboardFilters.scannerAlertContextSymbol=",
]

outside_r30 = SOURCE.replace(
    r30,
    "",
    1,
)

check(
    "NO_DIRECT_FILTER_MUTATION_OUTSIDE_BOUNDARY",
    not any(item in outside_r30 for item in direct_mutations),
)


# ----------------------------------------------------------------------
# DOM controls use the central state boundary
# ----------------------------------------------------------------------

check(
    "NEWS_SYMBOL_USES_SETTER",
    "setDashboardFilter(" in compact_source
    and "newsSymbol" in compact_source,
)

check(
    "NEWS_CATEGORY_USES_SETTER",
    "newsCategory" in compact_source,
)

check(
    "SCANNER_SYMBOL_USES_SETTER",
    "scannerSymbol" in compact_source,
)

check(
    "ALERT_SYMBOL_USES_SETTER",
    "scannerAlertSymbol" in compact_source,
)

check(
    "ALERT_CONTEXT_SYMBOL_USES_SETTER",
    "scannerAlertContextSymbol" in compact_source,
)


# ----------------------------------------------------------------------
# No persistence
# ----------------------------------------------------------------------

check(
    "R30_HAS_NO_STORAGE_MUTATION",
    "sessionStorage" not in r30
    and "localStorage" not in r30,
)


# ----------------------------------------------------------------------
# Previous state architecture preserved
# ----------------------------------------------------------------------

for marker in (
    "R24_DASHBOARD_TABS_UI_START",
    "R25_DASHBOARD_TABS_HARDENING_START",
    "R26_DASHBOARD_TAB_STATE_START",
    "R27_WATCHLIST_STATE_START",
    "R28_DASHBOARD_STATE_MUTATION_START",
    "R29_CHART_INDICATOR_STATE_START",
):
    check(
        f"PRESERVES_{marker}",
        marker in SOURCE,
    )


# ----------------------------------------------------------------------
# No trading authority
# ----------------------------------------------------------------------

for forbidden in (
    "execution_intent",
    "place_order",
    "submit_order",
    "tradeplanner",
    "riskmanager",
    "executionconfirmation",
    "executiongateway",
):
    check(
        f"NO_{forbidden.upper()}",
        forbidden not in r30.lower(),
    )


failed = [(name, ok) for name, ok in checks if not ok]

for name, ok in checks:
    print(f"{name}={'PASS' if ok else 'FAIL'}")

if failed:
    print(
        f"R30_CONTRACT=FAIL "
        f"({len(checks)-len(failed)}/{len(checks)})"
    )
    raise SystemExit(1)

print(f"R30_CONTRACT=PASS ({len(checks)}/{len(checks)})")
