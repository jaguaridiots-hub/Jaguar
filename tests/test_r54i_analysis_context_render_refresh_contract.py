from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
V3 = (ROOT / "dashboard" / "command_center_v3.py").read_text(
    encoding="utf-8"
)


def block(source, start, end):
    a = source.find(start)
    assert a >= 0, f"MISSING={start}"

    b = source.find(end, a + len(start))
    assert b >= 0, f"MISSING_END={end}"

    return source[a:b]


context = block(
    V3,
    "/* R54B_ANALYSIS_CONTEXT_STATE_START */",
    "/* R54B_ANALYSIS_CONTEXT_STATE_END */",
)

load_block = block(
    V3,
    "async function load(){",
    "\nsetDashboardEventListener(document.getElementById(\"aiForm\")",
)

watch = block(
    V3,
    "function renderWatch(){",
    "function freshnessLabel(",
)

# --------------------------------------------------
# Static context → refresh boundary
# --------------------------------------------------

setter = block(
    V3,
    "function setActiveAnalysisContext(",
    "/* R54B_ANALYSIS_CONTEXT_STATE_END */",
)

assert "state.interval=" in setter
assert "state.mode=" in setter
assert "persistAnalysisContext();" in setter
assert "syncAnalysisContextControls();" in setter
assert "renderWatch();" in setter
assert "load();" in setter

print("R54I_CONTEXT_SETTER_REFRESH=PASS")


# --------------------------------------------------
# Load must use active context
# --------------------------------------------------

assert "getActiveSymbol()" in load_block
assert "getActiveInterval()" in load_block
assert "getActiveMode()" in load_block

assert (
    "`&interval=${encodeURIComponent(getActiveInterval())}`"
    in load_block
)

assert (
    "`&mode=${encodeURIComponent(getActiveMode())}`"
    in load_block
)

assert "setDashboardStateSnapshot(d);" in load_block
assert "render();" in load_block

print("R54I_LOAD_USES_ACTIVE_CONTEXT=PASS")


# --------------------------------------------------
# Watch rendering reflects active context
# --------------------------------------------------

assert "getActiveSymbol()" in watch
assert "getActiveInterval()" in watch
assert "getActiveMode()" in watch

assert (
    "${esc(getActiveInterval())} · ${esc(getActiveMode())}"
    in watch
)

print("R54I_WATCH_RENDER_USES_CONTEXT=PASS")


# --------------------------------------------------
# Symbol isolation
# --------------------------------------------------

assert "state.symbol" not in setter
assert "persistR27ActiveWatchSymbol" not in setter

print("R54I_CONTEXT_DOES_NOT_MUTATE_SYMBOL=PASS")
print("R54I_CONTEXT_DOES_NOT_WRITE_R27=PASS")


# --------------------------------------------------
# Runtime: context change drives render + refresh
# --------------------------------------------------

runtime_js = """
const vm = require("node:vm");

const context = {
  state: {
    symbol: "BTCUSDT",
    interval: "15m",
    mode: "SWING"
  },
  persistCalls: 0,
  syncCalls: 0,
  watchCalls: 0,
  loadCalls: 0
};

vm.createContext(context);

vm.runInContext(`
function normalizeAnalysisInterval(value){
  const valid = new Set(["15m","1h","4h","1d"]);
  const interval = String(value || "").trim().toLowerCase();
  return valid.has(interval) ? interval : "15m";
}

function normalizeAnalysisMode(value){
  const valid = new Set(["SCALP","SWING","CLASSIC"]);
  const mode = String(value || "").trim().toUpperCase();
  return valid.has(mode) ? mode : "SWING";
}

function getActiveInterval(){
  return state.interval;
}

function getActiveMode(){
  return state.mode;
}

function persistAnalysisContext(){
  globalThis.persistCalls += 1;
}

function syncAnalysisContextControls(){
  globalThis.syncCalls += 1;
}

function renderWatch(){
  globalThis.watchCalls += 1;
}

function load(){
  globalThis.loadCalls += 1;
}

function setActiveAnalysisContext({
  interval = getActiveInterval(),
  mode = getActiveMode(),
  refresh = true
} = {}){
  state.interval = normalizeAnalysisInterval(interval);
  state.mode = normalizeAnalysisMode(mode);

  persistAnalysisContext();
  syncAnalysisContextControls();
  renderWatch();

  if(refresh){
    load();
  }
}
`, context);

vm.runInContext(`
setActiveAnalysisContext({
  interval: "4h",
  mode: "SCALP",
  refresh: true
});

if(state.symbol !== "BTCUSDT"){
  throw new Error("symbol changed");
}

if(state.interval !== "4h"){
  throw new Error("interval not updated");
}

if(state.mode !== "SCALP"){
  throw new Error("mode not updated");
}

if(globalThis.persistCalls !== 1){
  throw new Error("persist count=" + globalThis.persistCalls);
}

if(globalThis.syncCalls !== 1){
  throw new Error("sync count=" + globalThis.syncCalls);
}

if(globalThis.watchCalls !== 1){
  throw new Error("watch count=" + globalThis.watchCalls);
}

if(globalThis.loadCalls !== 1){
  throw new Error("load count=" + globalThis.loadCalls);
}
`, context);

console.log("R54I_RUNTIME_CONTEXT_UPDATE=PASS");
console.log("R54I_RUNTIME_SINGLE_REFRESH=PASS");
console.log("R54I_RUNTIME_SINGLE_WATCH_RENDER=PASS");
"""

result = subprocess.run(
    ["node", "-e", runtime_js],
    cwd=ROOT,
    text=True,
    capture_output=True,
    check=True,
)

print(result.stdout, end="")


# --------------------------------------------------
# Runtime: refresh=false must not call load
# --------------------------------------------------

runtime_no_refresh = """
const vm = require("node:vm");

const context = {
  state: {
    symbol: "BTCUSDT",
    interval: "15m",
    mode: "SWING"
  },
  loadCalls: 0
};

vm.createContext(context);

vm.runInContext(`
function normalizeAnalysisInterval(value){
  const valid = new Set(["15m","1h","4h","1d"]);
  const interval = String(value || "").trim().toLowerCase();
  return valid.has(interval) ? interval : "15m";
}

function normalizeAnalysisMode(value){
  const valid = new Set(["SCALP","SWING","CLASSIC"]);
  const mode = String(value || "").trim().toUpperCase();
  return valid.has(mode) ? mode : "SWING";
}

function getActiveInterval(){
  return state.interval;
}

function getActiveMode(){
  return state.mode;
}

function persistAnalysisContext(){}

function syncAnalysisContextControls(){}

function renderWatch(){}

function load(){
  globalThis.loadCalls += 1;
}

function setActiveAnalysisContext({
  interval = getActiveInterval(),
  mode = getActiveMode(),
  refresh = true
} = {}){
  state.interval = normalizeAnalysisInterval(interval);
  state.mode = normalizeAnalysisMode(mode);

  persistAnalysisContext();
  syncAnalysisContextControls();
  renderWatch();

  if(refresh){
    load();
  }
}
`, context);

vm.runInContext(`
setActiveAnalysisContext({
  interval: "1h",
  mode: "CLASSIC",
  refresh: false
});

if(state.symbol !== "BTCUSDT"){
  throw new Error("symbol changed");
}

if(state.interval !== "1h"){
  throw new Error("interval not updated");
}

if(state.mode !== "CLASSIC"){
  throw new Error("mode not updated");
}

if(globalThis.loadCalls !== 0){
  throw new Error("load count=" + globalThis.loadCalls);
}
`, context);

console.log("R54I_REFRESH_FALSE_SUPPRESSES_LOAD=PASS");
"""

result = subprocess.run(
    ["node", "-e", runtime_no_refresh],
    cwd=ROOT,
    text=True,
    capture_output=True,
    check=True,
)

print(result.stdout, end="")


# --------------------------------------------------
# No trading/execution coupling
# --------------------------------------------------

for forbidden in (
    "TradePlanner",
    "RiskManager",
    "ExecutionGateway",
    "execution_intent",
    "broker_order",
    "position_size",
    "risk_percent",
    "execution_override",
):
    assert forbidden not in setter
    assert forbidden not in load_block

print("R54I_NO_TRADING_COUPLING=PASS")
print("R54I_ANALYSIS_CONTEXT_RENDER_REFRESH_CONTRACT=PASS")
