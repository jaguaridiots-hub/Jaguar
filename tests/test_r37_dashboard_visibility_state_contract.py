from pathlib import Path
import re

JS = Path("dashboard/command_center_v3.py").read_text()

START = "/* R37_DASHBOARD_VISIBILITY_STATE_START */"
END = "/* R37_DASHBOARD_VISIBILITY_STATE_END */"


def fail(message):
    raise AssertionError(message)


def main():
    checks = 0

    # 1-2: boundary markers
    if JS.count(START) != 1:
        fail("R37 start marker must exist exactly once")
    checks += 1

    if JS.count(END) != 1:
        fail("R37 end marker must exist exactly once")
    checks += 1

    start = JS.index(START)
    end = JS.index(END)
    if start >= end:
        fail("R37 visibility boundary ordering invalid")
    checks += 1

    block = JS[start:end]

    # 3: helper definition
    if block.count("function setDashboardHiddenState(") != 1:
        fail("R37 hidden-state helper must be defined exactly once")
    checks += 1

    # 4: helper must assign Boolean(hidden)
    if "element.hidden=Boolean(hidden);" not in block.replace(" ", ""):
        fail("R37 helper must normalize hidden state with Boolean(hidden)")
    checks += 1

    # 5: helper must validate the element
    if 'if(!element||!("hidden"inelement))return;' not in block.replace(" ", ""):
        fail("R37 helper must validate element.hidden")
    checks += 1

    # 6: exactly one direct .hidden assignment, inside R37 boundary
    direct_assignments = re.findall(r'\b[A-Za-z_$][\w$]*\.hidden\s*=', JS)
    if len(direct_assignments) != 1:
        fail(
            f"expected exactly one direct .hidden assignment in dashboard JS, "
            f"found {len(direct_assignments)}"
        )
    checks += 1

    # 7: direct assignment is inside R37 boundary
    assignment_match = re.search(r'\b[A-Za-z_$][\w$]*\.hidden\s*=', JS)
    if not assignment_match or not (start <= assignment_match.start() < end):
        fail("direct .hidden assignment must be inside R37 boundary")
    checks += 1

    # 8: routing must call the helper
    if "setDashboardHiddenState(panel,!active);" not in JS.replace(" ", ""):
        fail("R24 routed panel visibility must use R37 helper")
    checks += 1

    # 9: legacy direct panel mutation must be gone
    if "panel.hidden=!active;" in JS.replace(" ", ""):
        fail("legacy direct panel.hidden mutation remains")
    checks += 1

    # 10: no direct hidden assignment outside R37 boundary
    outside = JS[:start] + JS[end:]
    if re.search(r'\b[A-Za-z_$][\w$]*\.hidden\s*=', outside):
        fail("direct .hidden assignment exists outside R37 boundary")
    checks += 1

    # 11: R37 must stay dashboard-local
    if "fetch(" in block or "XMLHttpRequest" in block:
        fail("R37 boundary must not introduce network access")
    checks += 1

    # 12: no trading authority references
    forbidden = (
        "IDM",
        "TradePlanner",
        "RiskManager",
        "ExecutionGateway",
        "execution_intent",
        "state.decision",
        "state.trade",
        "state.risk",
        "state.execution",
    )
    for token in forbidden:
        if token in block:
            fail(f"R37 boundary contains forbidden authority token: {token}")
    checks += 1

    print(f"R37 contract PASS: {checks}/{checks}")


if __name__ == "__main__":
    main()
