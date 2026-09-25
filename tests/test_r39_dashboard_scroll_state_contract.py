from pathlib import Path
import re

JS = Path("dashboard/command_center_v3.py").read_text()

START = "/* R39_DASHBOARD_SCROLL_STATE_START */"
END = "/* R39_DASHBOARD_SCROLL_STATE_END */"


def fail(message):
    raise AssertionError(message)


def main():
    checks = 0

    # 1. Start marker
    if JS.count(START) != 1:
        fail("R39 start marker must exist exactly once")
    checks += 1

    # 2. End marker
    if JS.count(END) != 1:
        fail("R39 end marker must exist exactly once")
    checks += 1

    start = JS.index(START)
    end = JS.index(END)

    # 3. Boundary ordering
    if start >= end:
        fail("R39 scroll boundary ordering invalid")
    checks += 1

    block = JS[start:end]
    normalized = block.replace(" ", "")

    # 4. Helper definition
    if block.count("function setDashboardScrollTop(") != 1:
        fail("R39 scroll helper must be defined exactly once")
    checks += 1

    # 5. Helper validates scrollTop
    if 'if(!element||!("scrollTop"inelement))return;' not in normalized:
        fail("R39 helper must validate element.scrollTop")
    checks += 1

    # 6. Helper performs centralized scrollTop assignment
    if "element.scrollTop=value;" not in normalized:
        fail("R39 helper must assign element.scrollTop from value")
    checks += 1

    # 7. Exactly one direct scrollTop assignment in dashboard
    direct = re.findall(
        r'\b[A-Za-z_$][A-Za-z0-9_$]*\.scrollTop\s*=',
        JS,
    )
    if len(direct) != 1:
        fail(
            f"expected exactly one direct scrollTop assignment "
            f"in dashboard JS, found {len(direct)}"
        )
    checks += 1

    # 8. Direct assignment must be inside R39 boundary
    match = re.search(
        r'\b[A-Za-z_$][A-Za-z0-9_$]*\.scrollTop\s*=',
        JS,
    )
    if not match or not (start <= match.start() < end):
        fail("direct scrollTop assignment must be inside R39 boundary")
    checks += 1

    # 9. Assistant log must use the centralized helper
    if "setDashboardScrollTop(log,log.scrollHeight);" not in JS.replace(" ", ""):
        fail("assistant log must use R39 scroll helper")
    checks += 1

    # 10. Legacy direct mutation must be gone
    if "log.scrollTop=log.scrollHeight;" in JS.replace(" ", ""):
        fail("legacy direct log.scrollTop mutation remains")
    checks += 1

    # 11. No direct scrollLeft mutation introduced
    if re.search(r'\b[A-Za-z_$][A-Za-z0-9_$]*\.scrollLeft\s*=', JS):
        fail("R39 must not introduce scrollLeft mutation")
    checks += 1

    # 12. No scroll API introduced
    if ".scrollTo(" in block or ".scrollBy(" in block:
        fail("R39 boundary must not introduce scroll APIs")
    checks += 1

    # 13. No application-state mutation
    if re.search(r'\bstate\.[A-Za-z_$][A-Za-z0-9_$]*\s*=', block):
        fail("R39 boundary must not mutate dashboard application state")
    checks += 1

    # 14. No filter mutation
    if "dashboardFilters" in block:
        fail("R39 boundary must not mutate dashboard filters")
    checks += 1

    # 15. No storage/network
    if (
        "sessionStorage" in block
        or "localStorage" in block
        or "fetch(" in block
        or "XMLHttpRequest" in block
    ):
        fail("R39 boundary must not introduce storage or network access")
    checks += 1

    # 16. No execution authority references
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
            fail(f"R39 boundary contains forbidden authority token: {token}")
    checks += 1

    print(f"R39 contract PASS: {checks}/{checks}")


if __name__ == "__main__":
    main()
