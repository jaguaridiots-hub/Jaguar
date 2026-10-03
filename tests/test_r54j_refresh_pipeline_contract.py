from pathlib import Path
import re
import subprocess
import textwrap

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = ROOT / "dashboard" / "command_center_v3.py"
SRC = SRC_PATH.read_text()


def extract_function(source: str, name: str) -> str:
    m = re.search(
        rf"function\s+{re.escape(name)}\s*\(",
        source,
    )
    if not m:
        raise AssertionError(f"missing function: {name}")

    # First close the function parameter list. This matters for
    # destructured parameters such as:
    # function foo({value=...}={}){ ... }
    paren = source.find("(", m.start())
    if paren < 0:
        raise AssertionError(f"missing parameter list: {name}")

    depth = 0
    in_string = None
    escaped = False
    i = paren

    while i < len(source):
        ch = source[i]

        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == in_string:
                in_string = None
        else:
            if ch in ('"', "'", "`"):
                in_string = ch
            elif ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    break

        i += 1

    if depth != 0:
        raise AssertionError(f"unterminated parameter list: {name}")

    # The next opening brace is the actual function body.
    brace = source.find("{", i + 1)
    if brace < 0:
        raise AssertionError(f"missing function body: {name}")

    depth = 0
    in_string = None
    escaped = False
    i = brace

    while i < len(source):
        ch = source[i]

        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == in_string:
                in_string = None
        else:
            if ch in ('"', "'", "`"):
                in_string = ch
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return source[m.start(): i + 1]

        i += 1

    raise AssertionError(f"unterminated function: {name}")


setter = extract_function(SRC, "setActiveAnalysisContext")
snapshot = extract_function(SRC, "setDashboardStateSnapshot")
watch = extract_function(SRC, "renderWatch")
render = extract_function(SRC, "render")
load = extract_function(SRC, "load")
controls = extract_function(SRC, "initAnalysisContextControls")


# --------------------------------------------------
# Static: control -> setter authority
# --------------------------------------------------

assert 'getDashboardControlValue(intervalEl)' in controls
assert 'getActiveMode()' in controls
assert 'setActiveAnalysisContext({' in controls
assert 'refresh:true' in controls

assert 'getDashboardControlValue(modeEl)' in controls
assert 'getActiveInterval()' in controls

print("R54J_CONTROL_BINDING_REFRESH=PASS")


# --------------------------------------------------
# Static: setter refresh sequence
# --------------------------------------------------

setter_compact = re.sub(r"\s+", "", setter)

required_setter = [
    "state.interval=normalizeAnalysisInterval(interval);",
    "state.mode=normalizeAnalysisMode(mode);",
    "persistAnalysisContext();",
    "syncAnalysisContextControls();",
    "renderWatch();",
    "if(refresh){load();}",
]

for token in required_setter:
    if token not in setter_compact:
        raise AssertionError(
            f"missing setter token: {token}"
        )

assert setter_compact.index("persistAnalysisContext();") < \
       setter_compact.index("syncAnalysisContextControls();")
assert setter_compact.index("syncAnalysisContextControls();") < \
       setter_compact.index("renderWatch();")
assert setter_compact.index("renderWatch();") < \
       setter_compact.index("if(refresh){load();}")

print("R54J_SETTER_REFRESH_SEQUENCE=PASS")


# --------------------------------------------------
# Static: load uses active browser context
# --------------------------------------------------

assert "getActiveSymbol()" in load
assert "getActiveInterval()" in load
assert "getActiveMode()" in load
assert "/dashboard/state?symbol=" in load
assert "setDashboardStateSnapshot(d);" in load
assert "render();" in load

load_compact = re.sub(r"\s+", "", load)

for token in (
    "getActiveSymbol()",
    "getActiveInterval()",
    "getActiveMode()",
):
    assert token in load_compact

assert load_compact.index("setDashboardStateSnapshot(d);") < \
       load_compact.index("render();")

print("R54J_LOAD_ACTIVE_CONTEXT=PASS")
print("R54J_LOAD_SNAPSHOT_RENDER_ORDER=PASS")


# --------------------------------------------------
# Static: snapshot is not context authority
# --------------------------------------------------

assert "state.ui=d.ui;" in snapshot
assert "state.candles=Array.isArray(d.candles)?d.candles:[];" in snapshot

for forbidden in (
    "state.symbol=",
    "state.interval=",
    "state.mode=",
    "sessionStorage.setItem(",
):
    assert forbidden not in snapshot

print("R54J_SNAPSHOT_CONTEXT_ISOLATION=PASS")


# --------------------------------------------------
# Static: watch render reflects active context
# --------------------------------------------------

assert "getActiveSymbol()" in watch
assert "getActiveInterval()" in watch
assert "getActiveMode()" in watch

print("R54J_WATCH_ACTIVE_CONTEXT=PASS")


# --------------------------------------------------
# Static: main render consumes hydrated UI state
# --------------------------------------------------

for token in (
    "const u=state.ui||{};",
    "const market=u.market||{};",
    "const idm=u.idm||{};",
    "const decisionGate=u.decision_gate||{};",
    "const risk=u.risk||{};",
    "const exe=u.execution||{};",
):
    assert token in render

print("R54J_RENDER_UISNAPSHOT_AUTHORITY=PASS")


# --------------------------------------------------
# Static: no execution coupling in refresh authority
# --------------------------------------------------

refresh_sources = "\n".join(
    (setter, snapshot, watch, load, controls)
)

forbidden = re.compile(
    r"execution_intent|ExecutionGateway|TradePlanner|"
    r"RiskManager|place_order|broker|"
    r"state\.decision|state\.trade|state\.risk|state\.execution",
    re.I,
)

if forbidden.search(refresh_sources):
    raise AssertionError(
        "forbidden execution coupling found in R54-J refresh functions"
    )

print("R54J_NO_EXECUTION_COUPLING=PASS")


# --------------------------------------------------
# Runtime: actual setter body
# --------------------------------------------------

runtime_js = textwrap.dedent(
    f"""
    const vm = require("node:vm");

    const context = {{
      state: {{
        symbol: "BTCUSDT",
        interval: "15m",
        mode: "SWING"
      }},
      persistCalls: 0,
      syncCalls: 0,
      watchCalls: 0,
      loadCalls: 0
    }};

    vm.createContext(context);

    vm.runInContext(`
      function normalizeAnalysisInterval(value){{
        const valid=new Set(["15m","1h","4h","1d"]);
        const interval=String(value||"").trim().toLowerCase();
        return valid.has(interval) ? interval : "15m";
      }}

      function normalizeAnalysisMode(value){{
        const valid=new Set(["SCALP","SWING","CLASSIC"]);
        const mode=String(value||"").trim().toUpperCase();
        return valid.has(mode) ? mode : "SWING";
      }}

      function getActiveInterval(){{
        return state.interval;
      }}

      function getActiveMode(){{
        return state.mode;
      }}

      function persistAnalysisContext(){{
        globalThis.persistCalls += 1;
      }}

      function syncAnalysisContextControls(){{
        globalThis.syncCalls += 1;
      }}

      function renderWatch(){{
        globalThis.watchCalls += 1;
      }}

      function load(){{
        globalThis.loadCalls += 1;
      }}

      {setter}
    `, context);

    vm.runInContext(`
      setActiveAnalysisContext({{
        interval:"4h",
        mode:"SCALP",
        refresh:true
      }});

      if(state.symbol !== "BTCUSDT")
        throw new Error("symbol changed");

      if(state.interval !== "4h")
        throw new Error("interval not updated");

      if(state.mode !== "SCALP")
        throw new Error("mode not updated");

      if(globalThis.persistCalls !== 1)
        throw new Error("persist count");

      if(globalThis.syncCalls !== 1)
        throw new Error("sync count");

      if(globalThis.watchCalls !== 1)
        throw new Error("watch count");

      if(globalThis.loadCalls !== 1)
        throw new Error("load count");
    `, context);

    console.log("R54J_RUNTIME_ACTUAL_SETTER=PASS");
    console.log("R54J_RUNTIME_SINGLE_REFRESH=PASS");
    console.log("R54J_RUNTIME_CONTEXT_PRESERVED=PASS");
    """
)

result = subprocess.run(
    ["node", "-e", runtime_js],
    cwd=ROOT,
    text=True,
    capture_output=True,
    check=True,
)

print(result.stdout, end="")


print("R54J_REFRESH_PIPELINE_CONTRACT=PASS")
