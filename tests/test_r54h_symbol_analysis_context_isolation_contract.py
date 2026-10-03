from pathlib import Path
import json
import re
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


r27 = block(
    V3,
    "/* R27_WATCHLIST_STATE_START */",
    "/* R27_WATCHLIST_STATE_END */",
)

r28 = block(
    V3,
    "function setActiveSymbol(",
    "/* R28_DASHBOARD_STATE_MUTATION_END */",
)

r54b = block(
    V3,
    "/* R54B_ANALYSIS_CONTEXT_STATE_START */",
    "/* R54B_ANALYSIS_CONTEXT_STATE_END */",
)

r54d = block(
    V3,
    "/* R54D_ANALYSIS_CONTEXT_STORAGE_START */",
    "/* R54D_ANALYSIS_CONTEXT_STORAGE_END */",
)


# --------------------------------------------------
# Static ownership boundary
# --------------------------------------------------

assert "state.symbol=" in r28

for token in (
    "state.interval",
    "state.mode",
    "persistAnalysisContext",
    "restoreAnalysisContext",
):
    assert token not in r28, f"R54H_SYMBOL_COUPLING={token}"

assert "state.interval=" in r54b
assert "state.mode=" in r54b

for token in (
    "state.symbol",
    "persistR27ActiveWatchSymbol",
    "readR27ActiveWatchSymbol",
):
    assert token not in r54b, f"R54H_CONTEXT_COUPLING={token}"

assert "jaguarQuantXActiveWatchSymbol" in r27
assert "jaguar.r54d.analysisContext" not in r27

assert "jaguar.r54d.analysisContext" in r54d
assert "jaguarQuantXActiveWatchSymbol" not in r54d

print("R54H_STATIC_SYMBOL_CONTEXT_ISOLATION=PASS")


# --------------------------------------------------
# Runtime symbol → context isolation
# --------------------------------------------------

harness_symbol = f"""
const vm = require("node:vm");

const store = new Map();

const sessionStorage = {{
  getItem(key) {{
    return store.has(key) ? store.get(key) : null;
  }},
  setItem(key, value) {{
    store.set(key, String(value));
  }}
}};

const context = {{
  sessionStorage,

  state: {{
    symbol: "BTCUSDT",
    interval: "4h",
    mode: "SCALP"
  }},

  load() {{}},
  renderWatch() {{}},

  setDashboardEventHandler() {{}},
  setDashboardControlValue() {{}},

  document: {{
    getElementById() {{
      return null;
    }}
  }}
}};

vm.createContext(context);

vm.runInContext(`
{r27}

{r28}
`, context);

context.setActiveSymbol(
  "ETHUSDT",
  {{
    persistWatchlist:true,
    renderWatchlist:false,
    refresh:false
  }}
);

if (context.state.symbol !== "ETHUSDT") {{
  throw new Error("symbol did not change");
}}

if (context.state.interval !== "4h") {{
  throw new Error("interval changed during symbol switch");
}}

if (context.state.mode !== "SCALP") {{
  throw new Error("mode changed during symbol switch");
}}

if (
  store.get("jaguarQuantXActiveWatchSymbol") !==
  "ETHUSDT"
) {{
  throw new Error("R27 symbol persistence failed");
}}

console.log("R54H_SYMBOL_SWITCH_PRESERVES_CONTEXT=PASS");
console.log("R54H_SYMBOL_STORAGE_WRITE=PASS");
"""

result = subprocess.run(
    ["node", "-e", harness_symbol],
    cwd=ROOT,
    text=True,
    capture_output=True,
    check=True,
)

print(result.stdout, end="")


# --------------------------------------------------
# Runtime context → symbol isolation
# --------------------------------------------------

harness_context = f"""
const vm = require("node:vm");

const store = new Map();

const sessionStorage = {{
  getItem(key) {{
    return store.has(key) ? store.get(key) : null;
  }},
  setItem(key, value) {{
    store.set(key, String(value));
  }}
}};

const context = {{
  sessionStorage,

  state: {{
    symbol: "BTCUSDT",
    interval: "15m",
    mode: "SWING"
  }},

  load() {{}},
  renderWatch() {{}},

  getActiveInterval() {{
    return this.state.interval;
  }},

  getActiveMode() {{
    return this.state.mode;
  }},

  setDashboardEventHandler() {{}},
  setDashboardControlValue() {{}},

  document: {{
    getElementById() {{
      return null;
    }}
  }}
}};

vm.createContext(context);

vm.runInContext(`
{r54b}

{r54d}
`, context);

context.setActiveAnalysisContext({{
  interval:"1d",
  mode:"CLASSIC",
  refresh:false
}});

if (context.state.interval !== "1d") {{
  throw new Error("interval did not change");
}}

if (context.state.mode !== "CLASSIC") {{
  throw new Error("mode did not change");
}}

if (context.state.symbol !== "BTCUSDT") {{
  throw new Error("symbol changed during context switch");
}}

const persisted = JSON.parse(
  store.get("jaguar.r54d.analysisContext")
);

if (persisted.interval !== "1d") {{
  throw new Error("R54D interval persistence failed");
}}

if (persisted.mode !== "CLASSIC") {{
  throw new Error("R54D mode persistence failed");
}}

if (
  store.has("jaguarQuantXActiveWatchSymbol")
) {{
  throw new Error("analysis context created symbol storage");
}}

console.log("R54H_CONTEXT_SWITCH_PRESERVES_SYMBOL=PASS");
console.log("R54H_CONTEXT_STORAGE_WRITE=PASS");
"""

result = subprocess.run(
    ["node", "-e", harness_context],
    cwd=ROOT,
    text=True,
    capture_output=True,
    check=True,
)

print(result.stdout, end="")


# --------------------------------------------------
# No execution/trading coupling
# --------------------------------------------------

for forbidden in (
    "TradePlanner",
    "RiskManager",
    "ExecutionGateway",
    "execution_intent",
    "broker_order",
    "position_size",
    "risk_percent",
):
    assert forbidden not in r28
    assert forbidden not in r54b
    assert forbidden not in r54d

print("R54H_NO_TRADING_COUPLING=PASS")
print("R54H_SYMBOL_ANALYSIS_CONTEXT_ISOLATION_CONTRACT=PASS")
