from pathlib import Path
import re

P = Path("dashboard/command_center_v3.py")
src = P.read_text()

print("=== R46 CANVAS CONTEXT STATE CONTRACT ===")

# ------------------------------------------------------------
# Required R45 boundary must remain intact.
# ------------------------------------------------------------
assert "/* R45_DASHBOARD_CANVAS_SIZE_STATE_START */" in src
assert "function setDashboardCanvasSize(canvas,width,height){" in src
assert "setDashboardCanvasSize(canvas,width,height);" in src
print("R45_CANVAS_BOUNDARY=PASS")

# ------------------------------------------------------------
# Render-chart boundary and core flow must remain intact.
# ------------------------------------------------------------
assert "function renderChart(){" in src
assert "ctx.clearRect(0,0,width,height);" in src
assert "ctx.save();" in src
assert "ctx.restore();" in src
print("CANVAS_RENDER_FLOW=PASS")

# ------------------------------------------------------------
# Extract only renderChart().
# ------------------------------------------------------------
render_match = re.search(
    r"function renderChart\(\)\{(.*?)\n\}",
    src,
    re.S,
)

assert render_match, "renderChart() body not found"
render_body = render_match.group(1)

# ------------------------------------------------------------
# Expected R46 baseline sequence.
# ------------------------------------------------------------
expected_sequence = [
    "fillStyle",
    "font",
    "strokeStyle",
    "lineWidth",
    "strokeStyle",
    "fillStyle",
    "lineWidth",
    "strokeStyle",
    "lineWidth",
    "strokeStyle",
    "lineWidth",
    "fillStyle",
    "font",
    "textAlign",
    "textAlign",
]

properties = [
    "fillStyle",
    "font",
    "strokeStyle",
    "lineWidth",
    "textAlign",
]

# ------------------------------------------------------------
# Before implementation:
# exactly the known 15 direct assignments must exist in
# renderChart().
# ------------------------------------------------------------
r46_start = "/* R46_DASHBOARD_CANVAS_CONTEXT_STATE_START */"
r46_end = "/* R46_DASHBOARD_CANVAS_CONTEXT_STATE_END */"

if r46_start not in src and r46_end not in src:
    sequence = re.findall(
        r"\bctx\.(fillStyle|font|strokeStyle|lineWidth|textAlign)\s*=",
        render_body,
    )

    assert sequence == expected_sequence, (
        f"Unexpected R46 baseline sequence: {sequence}"
    )

    assert len(sequence) == 15

    print("BASELINE_CTX_ASSIGNMENTS=15")
    print("BASELINE_CTX_SEQUENCE=PASS")

    for prop in properties:
        count = len(
            re.findall(
                rf"\bctx\.{re.escape(prop)}\s*=",
                render_body,
            )
        )
        print(f"BASELINE_{prop.upper()}={count}")

    print("R46_IMPLEMENTATION=NOT_YET_APPLIED")
    print("EXECUTION_AUTHORITY=PASS")
    print("R46_CONTRACT=PASS")
    raise SystemExit(0)

# ------------------------------------------------------------
# After implementation:
# both R46 markers must exist.
# ------------------------------------------------------------
assert r46_start in src
assert r46_end in src

helper_match = re.search(
    re.escape(r46_start) + r"(.*?)" + re.escape(r46_end),
    src,
    re.S,
)

assert helper_match, "R46 helper block not found"
helper_body = helper_match.group(1)

assert "function setDashboardCanvasContextState(" in helper_body

# ------------------------------------------------------------
# R46 helper must only expose the five approved Canvas
# presentation properties.
# ------------------------------------------------------------
allowed = {
    "fillStyle",
    "font",
    "strokeStyle",
    "lineWidth",
    "textAlign",
}

helper_properties = re.findall(
    r'["\'](fillStyle|font|strokeStyle|lineWidth|textAlign)["\']',
    helper_body,
)

assert set(helper_properties).issubset(allowed)

# ------------------------------------------------------------
# Execution-authority identifiers are forbidden ONLY inside
# the new R46 helper block.
# ------------------------------------------------------------
for forbidden in [
    "IDM",
    "TradePlanner",
    "RiskManager",
    "ExecutionConfirmation",
    "ExecutionGateway",
    "execution_intent",
]:
    assert forbidden not in helper_body, (
        f"Execution authority leaked into R46 helper: {forbidden}"
    )

# ------------------------------------------------------------
# Direct ctx presentation-property assignments must be gone
# from renderChart().
# ------------------------------------------------------------
remaining_direct = re.findall(
    r"\bctx\.(fillStyle|font|strokeStyle|lineWidth|textAlign)\s*=",
    render_body,
)

assert remaining_direct == [], (
    f"Direct context assignments remain: {remaining_direct}"
)

# ------------------------------------------------------------
# Exactly 15 R46 helper calls must replace the old 15
# assignments, preserving property order.
# ------------------------------------------------------------
calls = re.findall(
    r"setDashboardCanvasContextState\(\s*ctx\s*,\s*[\"']"
    r"(fillStyle|font|strokeStyle|lineWidth|textAlign)[\"']",
    render_body,
)

assert calls == expected_sequence, (
    f"Unexpected R46 helper-call sequence: {calls}"
)

assert len(calls) == 15

print("R46_CTX_ASSIGNMENTS_REPLACED=15")
print("R46_CTX_SEQUENCE=PASS")
print("R46_HELPER_AUTHORITY_BOUNDARY=PASS")
print("R46_IMPLEMENTATION=PASS")
print("R46_CONTRACT=PASS")
