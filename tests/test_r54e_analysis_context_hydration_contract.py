from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
V3 = (ROOT / "dashboard" / "command_center_v3.py").read_text(
    encoding="utf-8"
)


def bounded_block(source, start, end):
    start_pos = source.find(start)
    assert start_pos >= 0, f"MISSING={start}"

    end_pos = source.find(end, start_pos + len(start))
    assert end_pos >= 0, f"MISSING_END={end}"

    return source[start_pos:end_pos]


# --------------------------------------------------
# R48 snapshot boundary
# --------------------------------------------------

snapshot = bounded_block(
    V3,
    "function setDashboardStateSnapshot(d){",
    "/* R48_DASHBOARD_STATE_SNAPSHOT_END */",
)

for forbidden in (
    "state.interval",
    "state.mode",
    "state.symbol",
    "setActiveAnalysisContext",
    "restoreAnalysisContext",
    "persistAnalysisContext",
):
    assert forbidden not in snapshot, (
        f"R54E_SNAPSHOT_CONTEXT_MUTATION={forbidden}"
    )

assert "state.ui=d.ui;" in snapshot
assert "state.candles=" in snapshot

print("R54E_SNAPSHOT_ISOLATION=PASS")


# --------------------------------------------------
# Startup runtime order
# --------------------------------------------------

startup_pos = V3.rfind("<script>")
assert startup_pos >= 0, "R54E_SCRIPT_MISSING"

startup = V3[startup_pos:]

restore = startup.find("restoreAnalysisContext();")
initial_symbol = startup.find(
    "const initialSymbol=readR27ActiveWatchSymbol();"
)
symbol_setup = startup.find(
    "setActiveSymbol(",
    initial_symbol,
)
controls = startup.find("initAnalysisContextControls();")
startup_load = startup.find("\nload();")
timer = startup.find("setInterval(load,10000);")

assert restore >= 0, "R54E_RESTORE_CALL_MISSING"
assert initial_symbol >= 0, "R54E_INITIAL_SYMBOL_MISSING"
assert symbol_setup >= 0, "R54E_SYMBOL_SETUP_MISSING"
assert controls >= 0, "R54E_CONTROL_INIT_MISSING"
assert startup_load >= 0, "R54E_STARTUP_LOAD_MISSING"
assert timer >= 0, "R54E_TIMER_MISSING"

assert restore < initial_symbol
assert initial_symbol < symbol_setup
assert symbol_setup < controls
assert controls < startup_load
assert startup_load < timer

print("R54E_RESTORE_ORDER=PASS")
print("R54E_STARTUP_LOAD_ORDER=PASS")


# --------------------------------------------------
# Load hydration ordering
# --------------------------------------------------

load_start = V3.find("async function load(){")
assert load_start >= 0, "R54E_LOAD_FUNCTION_MISSING"

load_end = V3.find("\n}", load_start)
assert load_end >= 0, "R54E_LOAD_FUNCTION_END_MISSING"

load_block = V3[load_start:load_end + 2]

snapshot_pos = load_block.find(
    "setDashboardStateSnapshot(d);"
)
render_pos = load_block.find("render();")

assert snapshot_pos >= 0
assert render_pos >= 0
assert snapshot_pos < render_pos

print("R54E_SNAPSHOT_BEFORE_RENDER=PASS")


# --------------------------------------------------
# R54-D persistence remains the source of restore
# --------------------------------------------------

storage = bounded_block(
    V3,
    "/* R54D_ANALYSIS_CONTEXT_STORAGE_START */",
    "/* R54D_ANALYSIS_CONTEXT_STORAGE_END */",
)

assert "sessionStorage.getItem" in storage
assert "sessionStorage.setItem" in storage
assert "restoreAnalysisContext" in storage
assert "persistAnalysisContext" in storage
assert "normalizeAnalysisInterval" in storage
assert "normalizeAnalysisMode" in storage

print("R54E_R54D_STORAGE_PRESERVED=PASS")


# --------------------------------------------------
# No server/UI snapshot becomes a second authority
# --------------------------------------------------

assert "setDashboardStateSnapshot(d);" in load_block

snapshot_calls = load_block.count(
    "setActiveAnalysisContext("
)

assert snapshot_calls == 0

print("R54E_NO_SNAPSHOT_CONTEXT_AUTHORITY=PASS")

print("R54E_ANALYSIS_CONTEXT_HYDRATION_CONTRACT=PASS")
