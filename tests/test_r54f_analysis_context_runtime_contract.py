from pathlib import Path
import json
import re
import subprocess


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


r54b = bounded_block(
    V3,
    "/* R54B_ANALYSIS_CONTEXT_STATE_START */",
    "/* R54B_ANALYSIS_CONTEXT_STATE_END */",
)

r54d = bounded_block(
    V3,
    "/* R54D_ANALYSIS_CONTEXT_STORAGE_START */",
    "/* R54D_ANALYSIS_CONTEXT_STORAGE_END */",
)


def run_node(storage_seed=None, storage_error=False):
    seed = json.dumps(storage_seed) if storage_seed is not None else "null"
    error_flag = "true" if storage_error else "false"

    js = f"""
const vm = require("node:vm");

const seed = {seed};
const storageError = {error_flag};

const storage = {{
  value: seed,
  getItem(key) {{
    if (storageError) throw new Error("storage unavailable");
    return this.value;
  }},
  setItem(key, value) {{
    if (storageError) throw new Error("storage unavailable");
    this.value = String(value);
  }}
}};

const context = {{
  console,
  sessionStorage: storage,

  state: {{
    interval: "15m",
    mode: "SWING"
  }},

  getActiveInterval() {{
    return this.state.interval;
  }},

  getActiveMode() {{
    return this.state.mode;
  }},

  setDashboardControlValue() {{}},
  document: {{
    getElementById() {{
      return {{}};
    }}
  }},
  renderWatch() {{}},
  load() {{}}
}};

vm.createContext(context);

vm.runInContext(`
{r54b}

{r54d}
`, context);

function assert(condition, message) {{
  if (!condition) throw new Error(message);
}}

if (seed === null && !storageError) {{
  assert(
    context.state.interval === "15m" &&
    context.state.mode === "SWING",
    "default context changed"
  );

  context.setActiveAnalysisContext({{
    interval: "4h",
    mode: "SCALP",
    refresh: false
  }});

  assert(
    context.state.interval === "4h" &&
    context.state.mode === "SCALP",
    "context setter failed"
  );

  const persisted = JSON.parse(storage.value);

  assert(persisted.interval === "4h", "persisted interval mismatch");
  assert(persisted.mode === "SCALP", "persisted mode mismatch");

  console.log("R54F_PERSIST_4H_SCALP=PASS");
  process.stdout.write(storage.value);
}} else {{
  context.restoreAnalysisContext();

  console.log(
    "RESTORED=" +
    context.state.interval +
    "/" +
    context.state.mode
  );

  process.stdout.write(
    JSON.stringify({{
      interval: context.state.interval,
      mode: context.state.mode
    }})
  );
}}
"""

    result = subprocess.run(
        ["node", "-e", js],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    return result.stdout, result.stderr


# --------------------------------------------------
# Persist valid context
# --------------------------------------------------

stdout, _ = run_node()

lines = stdout.strip().splitlines()
persisted = json.loads(lines[-1])

assert persisted == {
    "interval": "4h",
    "mode": "SCALP",
}

print("R54F_PERSIST_VALID_CONTEXT=PASS")


# --------------------------------------------------
# Restore valid context
# --------------------------------------------------

stdout, _ = run_node(
    storage_seed=json.dumps({
        "interval": "4h",
        "mode": "SCALP",
    })
)

assert "RESTORED=4h/SCALP" in stdout

print("R54F_RESTORE_VALID_CONTEXT=PASS")


# --------------------------------------------------
# Invalid values normalize safely
# --------------------------------------------------

stdout, _ = run_node(
    storage_seed=json.dumps({
        "interval": "99m",
        "mode": "UNKNOWN",
    })
)

assert "RESTORED=15m/SWING" in stdout

print("R54F_INVALID_CONTEXT_NORMALIZATION=PASS")


# --------------------------------------------------
# Partial context normalizes field-by-field
# --------------------------------------------------

stdout, _ = run_node(
    storage_seed=json.dumps({
        "interval": "1h",
        "mode": "INVALID",
    })
)

assert "RESTORED=1h/SWING" in stdout

print("R54F_PARTIAL_CONTEXT_NORMALIZATION=PASS")


# --------------------------------------------------
# Malformed JSON is fail-safe
# --------------------------------------------------

stdout, _ = run_node(storage_seed="{not-valid-json")

assert "RESTORED=15m/SWING" in stdout

print("R54F_MALFORMED_STORAGE_FAILSAFE=PASS")


# --------------------------------------------------
# Non-object JSON is fail-safe
# --------------------------------------------------

stdout, _ = run_node(storage_seed=json.dumps(["4h", "SCALP"]))

assert "RESTORED=15m/SWING" in stdout

print("R54F_NON_OBJECT_STORAGE_FAILSAFE=PASS")


# --------------------------------------------------
# Storage unavailability is fail-safe
# --------------------------------------------------

stdout, _ = run_node(storage_error=True)

assert "RESTORED=15m/SWING" in stdout

print("R54F_STORAGE_UNAVAILABLE_FAILSAFE=PASS")


# --------------------------------------------------
# Static isolation
# --------------------------------------------------

for forbidden in (
    "localStorage",
    "broker_order",
    "position_size",
    "risk_percent",
    "execution_override",
    "execution_intent",
):
    assert forbidden not in r54d, (
        f"FORBIDDEN_R54F_STORAGE_TOKEN={forbidden}"
    )

print("R54F_RUNTIME_STORAGE_ISOLATION=PASS")
print("R54F_ANALYSIS_CONTEXT_RUNTIME_CONTRACT=PASS")
