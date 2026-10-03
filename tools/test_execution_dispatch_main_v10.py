"""Jaguar Quant X B3-B static execution-dispatch integration gate."""

from pathlib import Path
import ast


ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "main.py"
HELPER = ROOT / "intelligence" / "paper_post_fill.py"


def _call_named(node, name):
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == name
    )


def _attr_call(node, obj, attr):
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == obj
        and node.func.attr == attr
    )


def _const(node, value):
    return isinstance(node, ast.Constant) and node.value == value


def _get_call(node, obj, key):
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == obj
        and node.func.attr == "get"
        and len(node.args) >= 1
        and isinstance(node.args[0], ast.Constant)
        and node.args[0].value == key
    )


def _mode_guard(node, value):
    return (
        isinstance(node, ast.If)
        and isinstance(node.test, ast.Compare)
        and isinstance(node.test.left, ast.Name)
        and node.test.left.id == "execution_mode"
        and len(node.test.ops) == 1
        and isinstance(node.test.ops[0], ast.Eq)
        and len(node.test.comparators) == 1
        and isinstance(node.test.comparators[0], ast.Constant)
        and node.test.comparators[0].value == value
    )


def _not_equal_get(node, obj, key, expected_name=None, expected_value=None):
    if not (
        isinstance(node, ast.Compare)
        and isinstance(node.left, ast.Call)
        and _get_call(node.left, obj, key)
        and len(node.ops) == 1
        and isinstance(node.ops[0], ast.NotEq)
        and len(node.comparators) == 1
    ):
        return False

    rhs = node.comparators[0]

    if expected_name is not None:
        return isinstance(rhs, ast.Name) and rhs.id == expected_name

    return _const(rhs, expected_value)


def test_b3b():
    main_src = MAIN.read_text()
    helper_src = HELPER.read_text()

    main_tree = ast.parse(main_src)
    helper_tree = ast.parse(helper_src)

    # Legacy adapter is completely removed from the production boundary.
    assert "ExecutionAdapter" not in main_src
    assert "execution_adapter" not in main_src

    # Exactly one authoritative mode-aware composition build.
    build_calls = [
        n for n in ast.walk(main_tree)
        if _call_named(n, "build_execution_dispatch_runtime")
    ]
    assert len(build_calls) == 1

    # PAPER lifecycle is delegated to exactly one helper call.
    paper_calls = [
        n for n in ast.walk(main_tree)
        if _call_named(n, "execute_paper_post_fill")
    ]
    assert len(paper_calls) == 1
    paper_call = paper_calls[0]

    # Exactly one LIVE dispatch: activation is explicit.
    dispatch_calls = [
        n for n in ast.walk(main_tree)
        if _attr_call(n, "execution_dispatch_runtime", "dispatch")
    ]

    live_dispatches = []
    paper_dispatches = []

    for n in dispatch_calls:
        kwargs = {kw.arg: kw.value for kw in n.keywords}
        activation = kwargs.get("activation_requested")

        if isinstance(activation, ast.Constant) and activation.value is True:
            live_dispatches.append(n)
        else:
            paper_dispatches.append(n)

    assert len(live_dispatches) == 1
    assert len(paper_dispatches) == 1

    live_dispatch = live_dispatches[0]
    live_kwargs = {kw.arg: kw.value for kw in live_dispatch.keywords}

    # Authoritative market metadata boundary.
    market_metadata = live_kwargs.get("market_metadata")
    assert (
        isinstance(market_metadata, ast.Attribute)
        and isinstance(market_metadata.value, ast.Name)
        and market_metadata.value.id == "state"
        and market_metadata.attr == "market_metadata"
    )

    # The activated LIVE dispatch is inside exactly one LIVE branch.
    live_parents = [
        n for n in ast.walk(main_tree)
        if isinstance(n, ast.If) and live_dispatch in ast.walk(n)
    ]
    live_guards = [n for n in live_parents if _mode_guard(n, "LIVE")]
    assert len(live_guards) >= 1
    live_guard = min(
        live_guards,
        key=lambda n: (n.end_lineno - n.lineno, n.lineno),
    )

    # PAPER helper is structurally excluded from LIVE branch.
    assert paper_call not in ast.walk(live_guard)

    # LIVE status gate.
    status_gates = [
        n for n in ast.walk(live_guard)
        if (
            isinstance(n, ast.If)
            and isinstance(n.test, ast.Compare)
            and isinstance(n.test.left, ast.Call)
            and _get_call(n.test.left, "live_result", "status")
            and len(n.test.ops) == 1
            and isinstance(n.test.ops[0], ast.NotEq)
            and len(n.test.comparators) == 1
            and _const(n.test.comparators[0], "SUBMITTED")
        )
    ]
    assert len(status_gates) == 1

    # LIVE authorization identity gate.
    auth_gates = [
        n for n in ast.walk(live_guard)
        if (
            isinstance(n, ast.If)
            and _not_equal_get(
                n.test,
                "live_result",
                "authorization_id",
                expected_name="authorization_id",
            )
        )
    ]
    assert len(auth_gates) == 1

    # LIVE client-order identity gate.
    client_gates = [
        n for n in ast.walk(live_guard)
        if (
            isinstance(n, ast.If)
            and _not_equal_get(
                n.test,
                "live_result",
                "client_order_id",
                expected_name="client_order_id",
            )
        )
    ]
    assert len(client_gates) == 1

    # LIVE branch must not consume PAPER-only post-fill artifacts.
    live_text = ast.unparse(live_guard)
    for forbidden in (
        "filled_quantity",
        "fill_price",
        "position.open_trade",
        "record_trade_open",
        "journal.save",
        "manager.activate",
    ):
        assert forbidden not in live_text

    # PAPER mode gate must contain the helper.
    paper_guards = [
        n for n in ast.walk(main_tree)
        if _mode_guard(n, "PAPER")
    ]
    assert len(paper_guards) == 1
    assert paper_call in ast.walk(paper_guards[0])

    # Durable SUBMITTED update exists.
    submitted_updates = []
    for n in ast.walk(main_tree):
        if _call_named(n, "update_execution_intent"):
            kwargs = {kw.arg: kw.value for kw in n.keywords}
            if _const(kwargs.get("status"), "SUBMITTED"):
                submitted_updates.append(n)
    assert submitted_updates

    # PAPER helper contains the preserved lifecycle.
    helper_functions = [
        n for n in ast.walk(helper_tree)
        if (
            isinstance(n, ast.FunctionDef)
            and n.name == "execute_paper_post_fill"
        )
    ]
    assert len(helper_functions) == 1

    helper_fn = helper_functions[0]
    helper_calls = [
        ast.unparse(n)
        for n in ast.walk(helper_fn)
        if isinstance(n, ast.Call)
    ]

    for required in (
        "position.open_trade(",
        "record_trade_open(",
        "journal.save(",
        "manager.activate(",
    ):
        assert any(required in text for text in helper_calls)

    for forbidden in (
        "execution_adapter.execute",
        ".submit_entry(",
        ".submit_protection(",
    ):
        assert not any(forbidden in text for text in helper_calls)

    print("B3B_COMPOSITION: PASS")
    print("B3B_NO_LEGACY_EXECUTION_ADAPTER: PASS")
    print("B3B_LIVE_DISPATCH: PASS")
    print("B3B_LIVE_MARKET_METADATA: PASS")
    print("B3B_LIVE_ACTIVATION: PASS")
    print("B3B_LIVE_SUBMITTED_GATE: PASS")
    print("B3B_LIVE_AUTHORIZATION_GATE: PASS")
    print("B3B_LIVE_CLIENT_ORDER_GATE: PASS")
    print("B3B_LIVE_NO_PAPER_LIFECYCLE: PASS")
    print("B3B_PAPER_DISPATCH: PASS")
    print("B3B_PAPER_HELPER_LIFECYCLE: PASS")
    print("B3B_EXECUTION_DISPATCH_MAIN_V10: PASS")


if __name__ == "__main__":
    test_b3b()
