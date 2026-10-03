"""R56-POS-22 PAPER entry lifecycle atomicity gate."""

from pathlib import Path
import ast


ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "intelligence" / "paper_post_fill.py"


def _is_call(node, name):
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == name
    )


def _call_text(node):
    return ast.unparse(node)


def _find_post_fill(tree):
    funcs = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef)
        and n.name == "execute_paper_post_fill"
    ]
    assert len(funcs) == 1
    return funcs[0]


def _find_direction_branch(fn, needle):
    for node in ast.walk(fn):
        if not isinstance(node, ast.If):
            continue

        test = ast.unparse(node.test).strip()

        if test == needle:
            # Return only this branch's body so an elif subtree cannot
            # contaminate the opposite-direction assertions.
            return ast.Module(
                body=list(node.body),
                type_ignores=[],
            )

    raise AssertionError(f"Missing direction branch: {needle}")


def _calls_in(node, name):
    return [
        n for n in ast.walk(node)
        if _is_call(n, name)
    ]


def _attribute_calls_in(node, obj, attr):
    return [
        n
        for n in ast.walk(node)
        if (
            isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)
            and isinstance(n.func.value, ast.Name)
            and n.func.value.id == obj
            and n.func.attr == attr
        )
    ]


def _validate_branch(branch, label):
    journal_calls = _attribute_calls_in(branch, "journal", "save")
    lifecycle_calls = _calls_in(branch, "_persist_paper_durable_lifecycle")
    activate_calls = [
        n for n in ast.walk(branch)
        if (
            isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)
            and isinstance(n.func.value, ast.Name)
            and n.func.value.id == "manager"
            and n.func.attr == "activate"
        )
    ]
    save_calls = _calls_in(branch, "save")

    assert len(journal_calls) == 1, (
        f"{label}: expected exactly one journal.save call"
    )
    assert len(lifecycle_calls) == 1, (
        f"{label}: expected exactly one durable lifecycle call"
    )
    assert len(activate_calls) == 1, (
        f"{label}: expected exactly one manager.activate call"
    )

    # Every save in the entry branch must include the TradeManager.
    assert len(save_calls) == 1, (
        f"{label}: expected exactly one position-state save"
    )

    save_call = save_calls[0]

    assert len(save_call.args) == 3, (
        f"{label}: active save must pass position, SYMBOL, manager"
    )

    assert (
        isinstance(save_call.args[0], ast.Name)
        and save_call.args[0].id == "position"
    ), f"{label}: save target must be position"

    assert (
        isinstance(save_call.args[1], ast.Name)
        and save_call.args[1].id == "SYMBOL"
    ), f"{label}: save symbol must be SYMBOL"

    assert (
        isinstance(save_call.args[2], ast.Name)
        and save_call.args[2].id == "manager"
    ), f"{label}: save must persist manager state"

    assert journal_calls[0].lineno < lifecycle_calls[0].lineno
    assert lifecycle_calls[0].lineno < activate_calls[0].lineno
    assert activate_calls[0].lineno < save_call.lineno

    # Explicitly prohibit the old incomplete persistence boundary.
    for node in save_calls:
        text = _call_text(node)
        assert text != "save(position, SYMBOL)", (
            f"{label}: incomplete active snapshot is forbidden"
        )

    print(f"R56_POS22_{label}_ORDER: PASS")
    print(f"R56_POS22_{label}_MANAGER_STATE: PASS")
    print(f"R56_POS22_{label}_NO_EARLY_SAVE: PASS")


def test_r56_pos22():
    src = HELPER.read_text()
    tree = ast.parse(src)
    fn = _find_post_fill(tree)

    # There must be exactly two state saves in the entire PAPER helper:
    # one LONG and one SHORT, both carrying TradeManager state.
    all_save_calls = _calls_in(fn, "save")
    assert len(all_save_calls) == 2, (
        f"Expected exactly 2 PAPER entry saves, found {len(all_save_calls)}"
    )

    for node in all_save_calls:
        assert len(node.args) == 3
        assert ast.unparse(node.args[0]) == "position"
        assert ast.unparse(node.args[1]) == "SYMBOL"
        assert ast.unparse(node.args[2]) == "manager"

    long_branch = _find_direction_branch(fn, "normalized_direction == 'BUY'")
    short_branch = _find_direction_branch(fn, "normalized_direction == 'SELL'")

    _validate_branch(long_branch, "LONG")
    _validate_branch(short_branch, "SHORT")

    # Authoritative lifecycle ordering across both entry directions.
    required_order = (
        "journal.save",
        "_persist_paper_durable_lifecycle",
        "manager.activate",
        "save(position, SYMBOL, manager)",
    )

    for branch, label in (
        (long_branch, "LONG"),
        (short_branch, "SHORT"),
    ):
        branch_calls = [
            n
            for n in ast.walk(branch)
            if isinstance(n, ast.Call)
        ]

        positions = {}
        for required in required_order:
            matches = [
                n for n in branch_calls
                if ast.unparse(n).startswith(required)
            ]
            assert len(matches) == 1, (
                f"{label}: missing or duplicate {required}"
            )
            positions[required] = matches[0].lineno

        assert (
            positions["journal.save"]
            < positions["_persist_paper_durable_lifecycle"]
            < positions["manager.activate"]
            < positions["save(position, SYMBOL, manager)"]
        )

    print("R56_POS22_NO_INCOMPLETE_ACTIVE_SNAPSHOT: PASS")
    print("R56_POS22_ENTRY_LIFECYCLE_ORDER: PASS")
    print("R56_POS22_ENTRY_ATOMICITY: PASS")


if __name__ == "__main__":
    test_r56_pos22()
