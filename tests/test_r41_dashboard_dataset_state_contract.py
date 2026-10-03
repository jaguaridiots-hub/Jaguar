from pathlib import Path
import re

JS = Path("dashboard/command_center_v3.py").read_text()

START = "/* R41_DASHBOARD_DATASET_STATE_START */"
END = "/* R41_DASHBOARD_DATASET_STATE_END */"


def fail(message):
    raise AssertionError(message)


def main():
    checks = 0

    # 1. Start marker
    if JS.count(START) != 1:
        fail("R41 start marker must exist exactly once")
    checks += 1

    # 2. End marker
    if JS.count(END) != 1:
        fail("R41 end marker must exist exactly once")
    checks += 1

    start = JS.index(START)
    end = JS.index(END)

    # 3. Boundary ordering
    if start >= end:
        fail("R41 dataset boundary ordering invalid")
    checks += 1

    block = JS[start:end]
    normalized = block.replace(" ", "")

    # 4. Helper definition
    if block.count("function setDashboardDatasetValue(") != 1:
        fail("R41 dataset helper must be defined exactly once")
    checks += 1

    # 5. Helper validates target dataset
    if 'if(!element||!element.dataset||typeofname!=="string")return;' not in normalized:
        fail("R41 helper must validate element.dataset and name")
    checks += 1

    # 6. Centralized computed dataset assignment
    if "element.dataset[name]=String(value??\"\");" not in normalized:
        fail("R41 helper must centrally assign dataset value")
    checks += 1

    # 7. Exactly one direct dataset property assignment in dashboard
    direct = re.findall(
        r'\.dataset\.[A-Za-z_$][A-Za-z0-9_$]*\s*=(?!=)',
        JS,
    )
    if len(direct) != 0:
        fail(
            "direct dataset property assignment remains outside R41 "
            f"boundary: {direct}"
        )
    checks += 1

    # 8. Exactly one computed dataset assignment
    computed = re.findall(
        r'\bdataset\[[A-Za-z_$][A-Za-z0-9_$]*\]\s*=(?!=)',
        JS,
    )
    if len(computed) != 1:
        fail(
            f"expected exactly one computed dataset assignment, found {len(computed)}"
        )
    checks += 1

    # 9. Computed assignment must be inside R41
    match = re.search(
        r'\bdataset\[[A-Za-z_$][A-Za-z0-9_$]*\]\s*=(?!=)',
        JS,
    )
    if not match or not (start <= match.start() < end):
        fail("computed dataset assignment must be inside R41 boundary")
    checks += 1

    # 10. R24 routing must use the helper
    if 'setDashboardDatasetValue(el,"r24Route",group.name);' not in JS.replace(" ", ""):
        fail("R24 routing must use R41 dataset helper")
    checks += 1

    # 11. Legacy mutation must be gone
    if "el.dataset.r24Route=group.name;" in JS.replace(" ", ""):
        fail("legacy r24Route dataset mutation remains")
    checks += 1

    # 12. Existing dataset reads must remain
    required_reads = (
        "el.dataset.r24Route!==name",
        "panel.dataset.r24Panel===name",
        "button.dataset.r24Tab||\"overview\"",
        "b.dataset.symbol",
        "btn.dataset.symbol",
        "btn.dataset.indicator",
    )
    for token in required_reads:
        if token not in JS.replace(" ", ""):
            fail(f"required dataset read missing: {token}")
    checks += 1

    # 13. No network access
    if "fetch(" in block or "XMLHttpRequest" in block:
        fail("R41 boundary must not introduce network access")
    checks += 1

    # 14. No state/filter/storage mutation
    if re.search(r'\bstate\.[A-Za-z_$][A-Za-z0-9_$]*\s*=', block):
        fail("R41 boundary must not mutate dashboard application state")
    if "dashboardFilters" in block:
        fail("R41 boundary must not mutate dashboard filters")
    if "sessionStorage" in block or "localStorage" in block:
        fail("R41 boundary must not introduce storage")
    checks += 1

    # 15. No execution authority
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
            fail(f"R41 boundary contains forbidden authority token: {token}")
    checks += 1

    print(f"R41 contract PASS: {checks}/{checks}")


if __name__ == "__main__":
    main()
