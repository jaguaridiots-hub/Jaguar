from pathlib import Path
import re
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / "dashboard" / "command_center_v3.py").read_text()


def extract_function(source: str, name: str) -> str:
    m = re.search(
        rf"(?:async\s+)?function\s+{re.escape(name)}\s*\(",
        source,
    )
    if not m:
        raise AssertionError(f"missing function: {name}")

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
        raise AssertionError(
            f"unterminated parameter list: {name}"
        )

    brace = source.find("{", i + 1)
    if brace < 0:
        raise AssertionError(
            f"missing function body: {name}"
        )

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
                    return source[m.start():i + 1]

        i += 1

    raise AssertionError(
        f"unterminated function: {name}"
    )


snapshot = extract_function(
    SRC,
    "setDashboardStateSnapshot",
)

load = extract_function(
    SRC,
    "load",
)


# --------------------------------------------------
# Static: 10-second periodic refresh authority
# --------------------------------------------------

assert re.search(
    r"setInterval\s*\(\s*load\s*,\s*10000\s*\)",
    SRC,
)

assert re.search(
    r"load\(\);\s*setInterval\s*\(\s*load\s*,\s*10000\s*\)",
    SRC,
)

print("R54K_PERIODIC_LOAD_AUTHORITY=PASS")


# --------------------------------------------------
# Static: snapshot may hydrate data only
# --------------------------------------------------

snapshot_compact = re.sub(r"\s+", "", snapshot)

for token in (
    "state.ui=d.ui;",
    "state.candles=Array.isArray(d.candles)?d.candles:[];",
):
    assert token in snapshot_compact, (
        f"missing snapshot token: {token}"
    )

for forbidden in (
    "state.symbol=",
    "state.interval=",
    "state.mode=",
    "sessionStorage.setItem(",
):
    assert forbidden not in snapshot_compact, (
        f"snapshot mutates context: {forbidden}"
    )

print("R54K_SNAPSHOT_CONTEXT_ISOLATION=PASS")


# --------------------------------------------------
# Static: production load uses active context
# --------------------------------------------------

load_compact = re.sub(r"\s+", "", load)

for token in (
    "getActiveSymbol()",
    "getActiveInterval()",
    "getActiveMode()",
    "/dashboard/state?symbol=",
    "setDashboardStateSnapshot(d);",
    "render();",
):
    assert token in load_compact, (
        f"load missing token: {token}"
    )

assert load_compact.index(
    "setDashboardStateSnapshot(d);"
) < load_compact.index(
    "render();"
)

print("R54K_LOAD_ACTIVE_CONTEXT=PASS")
print("R54K_REFRESH_SNAPSHOT_RENDER_ORDER=PASS")


# --------------------------------------------------
# Static: refresh path does not mutate context
# --------------------------------------------------

for forbidden in (
    "state.symbol=",
    "state.interval=",
    "state.mode=",
):
    assert forbidden not in load_compact, (
        f"load mutates context: {forbidden}"
    )

print("R54K_LOAD_CONTEXT_PRESERVATION=PASS")


# --------------------------------------------------
# Static: no execution coupling
# --------------------------------------------------

refresh_sources = "\n".join(
    (
        snapshot,
        load,
        re.search(
            r"setInterval\s*\(\s*load\s*,\s*10000\s*\)",
            SRC,
        ).group(0),
    )
)

forbidden = re.compile(
    r"execution_intent|ExecutionGateway|TradePlanner|"
    r"RiskManager|place_order|broker|"
    r"state\.decision|state\.trade|state\.risk|state\.execution",
    re.I,
)

assert not forbidden.search(refresh_sources), (
    "forbidden execution coupling found"
)

print("R54K_NO_EXECUTION_COUPLING=PASS")


# --------------------------------------------------
# Runtime: execute actual production snapshot + load
# twice and prove context survives refreshes.
# --------------------------------------------------

runtime_source_prefix = """function getActiveSymbol(){
  return state.symbol;
}

function getActiveInterval(){
  return state.interval;
}

function getActiveMode(){
  return state.mode;
}

function render(){
  globalThis.renderCalls += 1;
}

function fetch(url, options){
  globalThis.fetchCalls.push(String(url));
  globalThis.responseNumber += 1;

  const responseNo = globalThis.responseNumber;

  return Promise.resolve({
    ok: true,
    status: 200,
    async json(){
      return {
        ui: {
          marker: "REFRESH-" + responseNo
        },
        candles: [
          {
            close: responseNo
          }
        ]
      };
    }
  });
}

function setDashboardTextContent(){}
function setDashboardClassName(){}
"""

runtime_source = runtime_source_prefix + snapshot + "\n" + load

runtime_js = """
const vm = require("node:vm");

const context = {
  state: {
    symbol: "ETHUSDT",
    interval: "4h",
    mode: "SCALP",
    ui: null,
    candles: []
  },
  fetchCalls: [],
  renderCalls: 0,
  responseNumber: 0
};

vm.createContext(context);

vm.runInContext(
  __R54K_RUNTIME_SOURCE__,
  context
);

(async()=>{
  await vm.runInContext("load()", context);

  if(context.fetchCalls.length !== 1){
    throw new Error(
      "first fetch count=" + context.fetchCalls.length
    );
  }

  if(!context.fetchCalls[0].includes("symbol=ETHUSDT")){
    throw new Error(
      "first symbol missing: " + context.fetchCalls[0]
    );
  }

  if(!context.fetchCalls[0].includes("interval=4h")){
    throw new Error(
      "first interval missing: " + context.fetchCalls[0]
    );
  }

  if(!context.fetchCalls[0].includes("mode=SCALP")){
    throw new Error(
      "first mode missing: " + context.fetchCalls[0]
    );
  }

  if(context.state.symbol !== "ETHUSDT"){
    throw new Error("symbol mutated after first refresh");
  }

  if(context.state.interval !== "4h"){
    throw new Error("interval mutated after first refresh");
  }

  if(context.state.mode !== "SCALP"){
    throw new Error("mode mutated after first refresh");
  }

  if(!context.state.ui || context.state.ui.marker !== "REFRESH-1"){
    throw new Error("first snapshot not hydrated");
  }

  if(
    !Array.isArray(context.state.candles) ||
    context.state.candles[0].close !== 1
  ){
    throw new Error("first candles not hydrated");
  }

  await vm.runInContext("load()", context);

  if(context.fetchCalls.length !== 2){
    throw new Error(
      "second fetch count=" + context.fetchCalls.length
    );
  }

  if(context.fetchCalls[1] !== context.fetchCalls[0]){
    throw new Error(
      "refresh context changed: " +
      context.fetchCalls[0] +
      " -> " +
      context.fetchCalls[1]
    );
  }

  if(context.state.symbol !== "ETHUSDT"){
    throw new Error("symbol mutated after second refresh");
  }

  if(context.state.interval !== "4h"){
    throw new Error("interval mutated after second refresh");
  }

  if(context.state.mode !== "SCALP"){
    throw new Error("mode mutated after second refresh");
  }

  if(!context.state.ui || context.state.ui.marker !== "REFRESH-2"){
    throw new Error("second snapshot not hydrated");
  }

  if(
    !Array.isArray(context.state.candles) ||
    context.state.candles[0].close !== 2
  ){
    throw new Error("second candles not hydrated");
  }

  if(context.renderCalls !== 2){
    throw new Error(
      "render count=" + context.renderCalls
    );
  }

  console.log("R54K_RUNTIME_REFRESH_1=PASS");
  console.log("R54K_RUNTIME_REFRESH_2=PASS");
  console.log("R54K_RUNTIME_CONTEXT_PRESERVED=PASS");
  console.log("R54K_RUNTIME_ACTIVE_CONTEXT_REUSED=PASS");
  console.log("R54K_RUNTIME_SNAPSHOT_HYDRATION=PASS");
})().catch(err=>{
  console.error(err);
  process.exit(1);
});
"""

runtime_js = runtime_js.replace(
    "__R54K_RUNTIME_SOURCE__",
    json.dumps(runtime_source)
)

result = subprocess.run(
    ["node", "-e", runtime_js],
    cwd=ROOT,
    text=True,
    capture_output=True,
    check=False,
)

print("=== R54K NODE STDOUT ===")
print(result.stdout, end="")
print("=== R54K NODE STDERR ===")
print(result.stderr, end="")

if result.returncode != 0:
    raise SystemExit(
        f"R54K_NODE_RUNTIME_FAILED exit={result.returncode}"
    )


print("R54K_PERIODIC_REFRESH_CONTEXT_CONTRACT=PASS")
