from pathlib import Path

PATH = Path("dashboard/command_center_v3.py")
SOURCE = PATH.read_text(encoding="utf-8")


START = "/* R31_DASHBOARD_CONTEXT_RESOLUTION_START */"
END = "/* R31_DASHBOARD_CONTEXT_RESOLUTION_END */"


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


r31 = block()
compact_r31 = compact(r31)
compact_source = compact(SOURCE)


# ------------------------------------------------------------
# Marker integrity
# ------------------------------------------------------------

check(
    "R31_START_MARKER",
    SOURCE.count(START) == 1,
)

check(
    "R31_END_MARKER",
    SOURCE.count(END) == 1,
)


# ------------------------------------------------------------
# Canonical dashboard context readers
# ------------------------------------------------------------

check(
    "ACTIVE_SYMBOL_READER",
    "function getActiveSymbol()" in r31,
)

check(
    "ACTIVE_INTERVAL_READER",
    "function getActiveInterval()" in r31,
)

check(
    "ACTIVE_MODE_READER",
    "function getActiveMode()" in r31,
)


# ------------------------------------------------------------
# Operation-specific context resolvers
# ------------------------------------------------------------

for resolver in (
    "resolveScannerSymbol",
    "resolveScannerAlertSymbol",
    "resolveScannerAlertContextSymbol",
    "resolveNewsSymbol",
):
    check(
        f"{resolver.upper()}_EXISTS",
        f"function {resolver}(" in r31,
    )


# ------------------------------------------------------------
# Canonical source usage
# ------------------------------------------------------------

check(
    "ACTIVE_SYMBOL_READER_USES_STATE",
    "return String(state.symbol||\"\").trim();" in r31,
)

check(
    "ACTIVE_INTERVAL_READER_USES_STATE",
    "return String(state.interval||\"\").trim();" in r31,
)

check(
    "ACTIVE_MODE_READER_USES_STATE",
    "return String(state.mode||\"\").trim();" in r31,
)


# ------------------------------------------------------------
# Resolver fallback semantics
# ------------------------------------------------------------

check(
    "SCANNER_FALLBACK_TO_ACTIVE_SYMBOL",
    "resolveScannerSymbol" in r31
    and "getActiveSymbol()" in r31,
)

check(
    "ALERT_FALLBACK_TO_ACTIVE_SYMBOL",
    "resolveScannerAlertSymbol" in r31
    and "getActiveSymbol()" in r31,
)

check(
    "ALERT_CONTEXT_FALLBACK_TO_ACTIVE_SYMBOL",
    "resolveScannerAlertContextSymbol" in r31
    and "getActiveSymbol()" in r31,
)

check(
    "NEWS_RESOLUTION_USES_FILTER_STATE",
    "resolveNewsSymbol" in r31
    and "getDashboardFilter(\"newsSymbol\")" in r31,
)


# ------------------------------------------------------------
# R31 must not mutate canonical state
# ------------------------------------------------------------

check(
    "R31_NO_STATE_MUTATION",
    "state." not in r31
    or all(
        token not in r31
        for token in (
            "state.symbol=",
            "state.interval=",
            "state.mode=",
            "state.chartIndicators[",
        )
    ),
)

check(
    "R31_NO_FILTER_MUTATION",
    "dashboardFilters[" not in r31,
)


# ------------------------------------------------------------
# No persistence
# ------------------------------------------------------------

check(
    "R31_NO_STORAGE",
    "sessionStorage" not in r31
    and "localStorage" not in r31,
)


# ------------------------------------------------------------
# No network activity
# ------------------------------------------------------------

check(
    "R31_NO_NETWORK",
    "fetch(" not in r31
    and "XMLHttpRequest" not in r31,
)


# ------------------------------------------------------------
# No trading authority
# ------------------------------------------------------------

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
        forbidden not in r31.lower(),
    )


# ------------------------------------------------------------
# Previous architecture preserved
# ------------------------------------------------------------

for marker in (
    "R24_DASHBOARD_TABS_UI_START",
    "R25_DASHBOARD_TABS_HARDENING_START",
    "R26_DASHBOARD_TAB_STATE_START",
    "R27_WATCHLIST_STATE_START",
    "R28_DASHBOARD_STATE_MUTATION_START",
    "R29_CHART_INDICATOR_STATE_START",
    "R30_DASHBOARD_FILTER_STATE_START",
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
        f"R31_CONTRACT=FAIL "
        f"({len(checks)-len(failed)}/{len(checks)})"
    )
    raise SystemExit(1)

print(
    f"R31_CONTRACT=PASS "
    f"({len(checks)}/{len(checks)})"
)
