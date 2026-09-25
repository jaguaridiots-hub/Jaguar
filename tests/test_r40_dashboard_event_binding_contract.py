from pathlib import Path
import re

JS = Path("dashboard/command_center_v3.py").read_text()

START = "/* R40_DASHBOARD_EVENT_BINDING_START */"
END = "/* R40_DASHBOARD_EVENT_BINDING_END */"


def fail(message):
    raise AssertionError(message)


def main():
    checks = 0

    # 1. Start marker
    if JS.count(START) != 1:
        fail("R40 start marker must exist exactly once")
    checks += 1

    # 2. End marker
    if JS.count(END) != 1:
        fail("R40 end marker must exist exactly once")
    checks += 1

    start = JS.index(START)
    end = JS.index(END)

    # 3. Boundary ordering
    if start >= end:
        fail("R40 event-binding boundary ordering invalid")
    checks += 1

    block = JS[start:end]
    normalized = block.replace(" ", "")

    # 4. Helper definition
    if block.count("function setDashboardEventHandler(") != 1:
        fail("R40 event-binding helper must be defined exactly once")
    checks += 1

    # 5. Helper validates the element
    if "!element" not in normalized:
        fail("R40 helper must validate the target element")
    checks += 1

    # 6. Helper performs centralized computed event-property assignment
    if "element[eventName]=handler;" not in normalized:
        fail("R40 helper must centrally assign element[eventName]")
    checks += 1

    # 7. Exactly zero direct .event assignments outside R40
    direct_pattern = (
        r'\.(onclick|onchange|oninput|onsubmit|onkeydown|'
        r'onkeyup|onfocus|onblur)\s*='
    )
    direct = re.findall(direct_pattern, JS)
    if direct:
        fail(
            f"direct event-handler assignments remain in dashboard JS: "
            f"{len(direct)}"
        )
    checks += 1

    # 8. R40 helper contains exactly one computed event-property assignment
    computed_inside = re.findall(
        r'\b[A-Za-z_$][A-Za-z0-9_$]*\[[A-Za-z_$][A-Za-z0-9_$]*\]\s*=',
        block,
    )
    if computed_inside != ["element[eventName]="]:
        fail(
            "R40 boundary must contain exactly one computed event-property "
            f"assignment to element[eventName], found {computed_inside}"
        )
    checks += 1

    # 9. No computed event-property assignment outside R40
    outside = JS[:start] + JS[end:]
    if "element[eventName]=" in outside:
        fail("R40 computed event assignment exists outside R40 boundary")
    checks += 1

    # 10. Preserve event counts
    onclick_calls = len(re.findall(
        r'setDashboardEventHandler\([^;]*"onclick"',
        JS,
    ))
    onchange_calls = len(re.findall(
        r'setDashboardEventHandler\([^;]*"onchange"',
        JS,
    ))
    onkeydown_calls = len(re.findall(
        r'setDashboardEventHandler\([^;]*"onkeydown"',
        JS,
    ))

    if onclick_calls != 11:
        fail(f"expected 11 onclick bindings, found {onclick_calls}")
    checks += 1

    if onchange_calls != 2:
        fail(f"expected 2 onchange bindings, found {onchange_calls}")
    checks += 1

    if onkeydown_calls != 1:
        fail(f"expected 1 onkeydown binding, found {onkeydown_calls}")
    checks += 1

    # 11. No event-listener semantic substitution
    if ".addEventListener(" in block:
        fail("R40 helper must not introduce addEventListener semantics")
    checks += 1

    # 12. No application-state mutation in R40 helper boundary
    if re.search(r'\bstate\.[A-Za-z_$][A-Za-z0-9_$]*\s*=', block):
        fail("R40 boundary must not mutate dashboard application state")
    checks += 1

    # 13. No filter mutation
    if "dashboardFilters" in block:
        fail("R40 boundary must not mutate dashboard filters")
    checks += 1

    # 14. No persistence mutation
    if "sessionStorage" in block or "localStorage" in block:
        fail("R40 boundary must not introduce storage access")
    checks += 1

    # 15. No network
    if "fetch(" in block or "XMLHttpRequest" in block:
        fail("R40 boundary must not introduce network access")
    checks += 1

    # 16. No execution authority
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
            fail(f"R40 boundary contains forbidden authority token: {token}")
    checks += 1

    print(f"R40 contract PASS: {checks}/{checks}")


if __name__ == "__main__":
    main()
