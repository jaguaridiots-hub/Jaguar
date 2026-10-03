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


r26 = block(
    V3,
    "/* R26_DASHBOARD_TAB_STATE_START */",
    "/* R26_DASHBOARD_TAB_STATE_END */",
)

r27 = block(
    V3,
    "/* R27_WATCHLIST_STATE_START */",
    "/* R27_WATCHLIST_STATE_END */",
)

r54d = block(
    V3,
    "/* R54D_ANALYSIS_CONTEXT_STORAGE_START */",
    "/* R54D_ANALYSIS_CONTEXT_STORAGE_END */",
)


# --------------------------------------------------
# Exact storage keys
# --------------------------------------------------

r26_match = re.search(
    r'R26_TAB_STORAGE_KEY\s*=\s*"([^"]+)"',
    r26,
)
r27_match = re.search(
    r'R27_WATCH_STORAGE_KEY\s*=\s*"([^"]+)"',
    r27,
)
r54d_match = re.search(
    r'R54D_ANALYSIS_CONTEXT_STORAGE_KEY\s*=\s*"([^"]+)"',
    r54d,
)

assert r26_match
assert r27_match
assert r54d_match

r26_key = r26_match.group(1)
r27_key = r27_match.group(1)
r54d_key = r54d_match.group(1)

assert r54d_key == "jaguar.r54d.analysisContext"

assert len({r26_key, r27_key, r54d_key}) == 3

print("R54G_STORAGE_KEYS_UNIQUE=PASS")


# --------------------------------------------------
# Cross-feature source isolation
# --------------------------------------------------

assert r54d_key not in r26
assert r54d_key not in r27

assert "R26_" not in r54d
assert "R27_" not in r54d

assert "localStorage" not in r54d

print("R54G_R26_R54D_SOURCE_ISOLATION=PASS")
print("R54G_R27_R54D_SOURCE_ISOLATION=PASS")


# --------------------------------------------------
# Execute the real R54-D storage block
# --------------------------------------------------

harness = f"""
const vm = require("node:vm");

const store = new Map([
  [{json.dumps(r26_key)}, "market"],
  [{json.dumps(r27_key)}, "BTCUSDT"]
]);

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
    interval: "15m",
    mode: "SWING"
  }}
}};

vm.createContext(context);

vm.runInContext(`
function normalizeAnalysisInterval(value){{
  const valid = new Set(["15m","1h","4h","1d"]);
  const interval = String(value||"").trim().toLowerCase();
  return valid.has(interval) ? interval : "15m";
}}

function normalizeAnalysisMode(value){{
  const valid = new Set(["SCALP","SWING","CLASSIC"]);
  const mode = String(value||"").trim().toUpperCase();
  return valid.has(mode) ? mode : "SWING";
}}

{r54d}
`, context);

context.state.interval = "4h";
context.state.mode = "SCALP";

context.persistAnalysisContext();

if (store.get({json.dumps(r26_key)}) !== "market") {{
  throw new Error("R26 storage changed");
}}

if (store.get({json.dumps(r27_key)}) !== "BTCUSDT") {{
  throw new Error("R27 storage changed");
}}

const persisted = JSON.parse(
  store.get({json.dumps(r54d_key)})
);

if (persisted.interval !== "4h") {{
  throw new Error("R54D interval missing");
}}

if (persisted.mode !== "SCALP") {{
  throw new Error("R54D mode missing");
}}

console.log("R54G_RUNTIME_R26_R27_ISOLATION=PASS");
console.log("R54G_RUNTIME_R54D_WRITE=PASS");
"""

result = subprocess.run(
    ["node", "-e", harness],
    cwd=ROOT,
    text=True,
    capture_output=True,
    check=True,
)

print(result.stdout, end="")


# --------------------------------------------------
# Runtime key independence
# --------------------------------------------------

runtime_output = result.stdout

assert "R54G_RUNTIME_R26_R27_ISOLATION=PASS" in runtime_output
assert "R54G_RUNTIME_R54D_WRITE=PASS" in runtime_output

print("R54G_RUNTIME_STORAGE_SCOPE_ISOLATION=PASS")


# --------------------------------------------------
# No execution/trading state in storage boundary
# --------------------------------------------------

for forbidden in (
    "execution_intent",
    "broker_order",
    "position_size",
    "risk_percent",
    "execution_override",
    "TradePlanner",
    "RiskManager",
    "ExecutionGateway",
):
    assert forbidden not in r54d, (
        f"FORBIDDEN_R54G_TOKEN={forbidden}"
    )

print("R54G_NO_TRADING_STATE_IN_STORAGE=PASS")
print("R54G_STORAGE_SCOPE_ISOLATION_CONTRACT=PASS")
