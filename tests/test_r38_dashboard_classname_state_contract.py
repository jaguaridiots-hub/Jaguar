from pathlib import Path
import re

JS = Path("dashboard/command_center_v3.py").read_text()

START = "/* R38_DASHBOARD_CLASSNAME_STATE_START */"
END = "/* R38_DASHBOARD_CLASSNAME_STATE_END */"


def fail(message):
    raise AssertionError(message)


def main():
    checks = 0

    # 1. Start marker
    if JS.count(START) != 1:
        fail("R38 start marker must exist exactly once")
    checks += 1

    # 2. End marker
    if JS.count(END) != 1:
        fail("R38 end marker must exist exactly once")
    checks += 1

    start = JS.index(START)
    end = JS.index(END)

    # 3. Boundary ordering
    if start >= end:
        fail("R38 classname boundary ordering invalid")
    checks += 1

    block = JS[start:end]

    # 4. Helper definition
    if block.count("function setDashboardClassName(") != 1:
        fail("R38 classname helper must be defined exactly once")
    checks += 1

    # 5. Helper must validate className
    normalized = block.replace(" ", "")
    if 'if(!element||!("className"inelement))return;' not in normalized:
        fail("R38 helper must validate element.className")
    checks += 1

    # 6. Helper must normalize assigned value
    if "element.className=String(value??\"\");" not in normalized:
        fail("R38 helper must normalize value with String(value??\"\")")
    checks += 1

    # 7. Exactly one direct className assignment in the dashboard
    direct = re.findall(
        r'\b[A-Za-z_$][A-Za-z0-9_$]*\.className\s*=',
        JS,
    )
    if len(direct) != 1:
        fail(
            f"expected exactly one direct className assignment "
            f"in dashboard JS, found {len(direct)}"
        )
    checks += 1

    # 8. The direct assignment must be inside R38
    match = re.search(
        r'\b[A-Za-z_$][A-Za-z0-9_$]*\.className\s*=',
        JS,
    )
    if not match or not (start <= match.start() < end):
        fail("direct className assignment must be inside R38 boundary")
    checks += 1

    # 9. R38 must expose the centralized helper at the UI call sites
    call_count = JS.count("setDashboardClassName(")
    if call_count < 10:
        fail(
            f"expected helper definition plus 9 call sites, found {call_count}"
        )
    checks += 1

    # 10. Legacy direct assignments must be gone
    legacy_patterns = (
        'modeBadge").className=',
        'healthBadge").className=',
        'freshBadge").className=',
        'dataQualityBadge").className=',
        'decisionEl.className=',
        'decisionContext.className=',
    )
    for token in legacy_patterns:
        if token in JS:
            fail(f"legacy direct className mutation remains: {token}")
    checks += 1

    # 11. Network isolation
    if "fetch(" in block or "XMLHttpRequest" in block:
        fail("R38 boundary must not introduce network access")
    checks += 1

    # 12. State mutation isolation
    if re.search(r'\bstate\.[A-Za-z_$][A-Za-z0-9_$]*\s*=', block):
        fail("R38 boundary must not mutate dashboard application state")
    checks += 1

    # 13. Filter isolation
    if "dashboardFilters" in block:
        fail("R38 boundary must not mutate dashboard filters")
    checks += 1

    # 14. Storage isolation
    if "sessionStorage" in block or "localStorage" in block:
        fail("R38 boundary must not introduce storage mutation")
    checks += 1

    # 15. Execution authority isolation
    forbidden = (
        "IDM",
        "TradePlanner",
        "RiskManager",
        "ExecutionConfirmation",
        "ExecutionGateway",
        "execution_intent",
        "state.decision",
        "state.trade",
        "state.risk",
        "state.execution",
        "place_order",
        "submit_order",
        "broker",
    )
    for token in forbidden:
        if token in block:
            fail(f"R38 boundary contains forbidden authority token: {token}")
    checks += 1

    print(f"R38 contract PASS: {checks}/{checks}")


if __name__ == "__main__":
    main()
