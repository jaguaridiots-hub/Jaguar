from pathlib import Path
import re

PATH = Path("dashboard/command_center_v3.py")
text = PATH.read_text(encoding="utf-8")

checks = []


def check(name, condition):
    checks.append((name, bool(condition)))


def compact(value):
    return "".join(value.split())


# R28 mutation boundary
start_marker = "/* R28_DASHBOARD_STATE_MUTATION_START */"
end_marker = "/* R28_DASHBOARD_STATE_MUTATION_END */"

check(
    "R28_START_MARKER",
    start_marker in text,
)

check(
    "R28_END_MARKER",
    end_marker in text,
)

if start_marker in text and end_marker in text:
    r28 = text.split(start_marker, 1)[1].split(end_marker, 1)[0]
else:
    r28 = ""

check(
    "SET_ACTIVE_SYMBOL_FUNCTION",
    "function setActiveSymbol(" in r28,
)

check(
    "SET_ACTIVE_SYMBOL_VALIDATES_SYMBOL",
    'const value=String(symbol||"").trim();' in r28
    and 'if(!value){' in r28,
)

check(
    "SET_ACTIVE_SYMBOL_SINGLE_STATE_ASSIGNMENT",
    "state.symbol=value;" in r28,
)

check(
    "SETTER_PERSISTS_ONLY_WHEN_REQUESTED",
    "if(persistWatchlist){" in r28
    and "persistR27ActiveWatchSymbol(value);" in r28,
)

check(
    "SETTER_RENDERS_ONLY_WHEN_REQUESTED",
    "if(renderWatchlist){" in r28
    and "renderWatch();" in r28,
)

check(
    "SETTER_REFRESHES_ONLY_WHEN_REQUESTED",
    "if(refresh){" in r28
    and "load();" in r28,
)

# There must be exactly one direct state.symbol assignment in the entire file,
# and it must live inside the R28 setter.
assignments = re.findall(r"^\s*state\.symbol\s*=", text, re.MULTILINE)

check(
    "ONLY_ONE_DIRECT_STATE_SYMBOL_ASSIGNMENT",
    len(assignments) == 1,
)

check(
    "DIRECT_ASSIGNMENT_IS_INSIDE_R28_SETTER",
    "state.symbol=value;" in r28,
)

# Watchlist preserves R27 semantics.
compact_text = compact(text)

check(
    "WATCHLIST_USES_CENTRAL_SETTER",
    compact(
        "setActiveSymbol("
        "b.dataset.symbol,"
        "{"
        "persistWatchlist:true,"
        "renderWatchlist:true,"
        "refresh:true"
        "}"
        ");"
    ) in compact_text,
)

# Market coverage remains ephemeral. It must not persist to R27 storage.
check(
    "MARKET_COVERAGE_USES_CENTRAL_SETTER",
    "setActiveSymbol(btn.dataset.symbol);" in text,
)

# Startup restores the persisted R27 symbol but does not write it back or
# trigger a second load before the existing explicit load().
check(
    "STARTUP_USES_CENTRAL_SETTER",
    compact(
        "setActiveSymbol("
        "initialSymbol,"
        "{"
        "renderWatchlist:true,"
        "refresh:false"
        "}"
        ");"
    ) in compact_text,
)

check(
    "STARTUP_DOES_NOT_PERSIST",
    "setActiveSymbol(initialSymbol,{persistWatchlist:true" not in text,
)

# R27 storage contract remains intact.
check(
    "R27_STORAGE_KEY_UNCHANGED",
    'const R27_WATCH_STORAGE_KEY="jaguarQuantXActiveWatchSymbol";' in text,
)

# R26 storage contract remains intact.
check(
    "R26_STORAGE_KEY_UNCHANGED",
    'const R26_TAB_STORAGE_KEY="jaguarQuantXActiveDashboardTab";' in text,
)

failed = [(name, ok) for name, ok in checks if not ok]

for name, ok in checks:
    print(f"{name}={'PASS' if ok else 'FAIL'}")

if failed:
    print(f"R28_CONTRACT=FAIL ({len(checks)-len(failed)}/{len(checks)})")
    raise SystemExit(1)

print(f"R28_CONTRACT=PASS ({len(checks)}/{len(checks)})")
