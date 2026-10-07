import ast
from pathlib import Path


def test_analyze_response_removes_authorization_id_from_execution():
    source = Path("api.py").read_text()
    tree = ast.parse(source)

    analyze = next(
        node
        for node in tree.body
        if isinstance(node, ast.AsyncFunctionDef)
        and node.name == "analyze"
    )

    pop_found = False
    execution_return_found = False

    for node in ast.walk(analyze):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "pop"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "execution"
            and len(node.args) == 2
            and isinstance(node.args[0], ast.Constant)
            and node.args[0].value == "authorization_id"
            and isinstance(node.args[1], ast.Constant)
            and node.args[1].value is None
        ):
            pop_found = True

        if (
            isinstance(node, ast.Return)
            and isinstance(node.value, ast.Dict)
        ):
            for key, value in zip(node.value.keys, node.value.values):
                if (
                    isinstance(key, ast.Constant)
                    and key.value == "execution"
                    and isinstance(value, ast.Name)
                    and value.id == "execution"
                ):
                    execution_return_found = True

    assert pop_found, "analyze() must remove authorization_id from execution"
    assert execution_return_found, "analyze() must return the sanitized execution object"
