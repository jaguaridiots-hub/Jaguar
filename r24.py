#!/usr/bin/env python3

"""
R24
RSI Import Authority
"""

import ast
from pathlib import Path

TARGET = Path("indicators/indicator_engine.py")

tree = ast.parse(
    TARGET.read_text(
        encoding="utf-8"
    )
)


def find_calculate(tree):

    for node in ast.walk(tree):

        if (
            isinstance(node, ast.ClassDef)
            and node.name == "IndicatorEngine"
        ):

            for child in node.body:

                if (
                    isinstance(child, ast.FunctionDef)
                    and child.name == "calculate"
                ):
                    return child

    raise RuntimeError(
        "IndicatorEngine.calculate not found"
    )


calculate = find_calculate(tree)

print(
    "TARGET_FUNCTION:",
    calculate.name,
)

print(
    "START_LINE:",
    calculate.lineno,
)
def find_return_dict(function):

    for node in ast.walk(function):

        if (
            isinstance(node, ast.Return)
            and isinstance(node.value, ast.Dict)
        ):
            return node.value

    raise RuntimeError(
        "Return dictionary not found"
    )


return_dict = find_return_dict(calculate)

print(
    "RETURN_DICT_KEYS:",
    len(return_dict.keys),
)


def find_dict_entry(dictionary, key_name):

    for key, value in zip(
        dictionary.keys,
        dictionary.values,
    ):

        if (
            isinstance(key, ast.Constant)
            and key.value == key_name
        ):
            return key, value

    raise RuntimeError(
        f"{key_name} entry not found"
    )


rsi_key, rsi_value = find_dict_entry(
    return_dict,
    "rsi",
)

print(
    "RSI_KEY:",
    rsi_key.value,
)

print(
    "RSI_VALUE_TYPE:",
    type(rsi_value).__name__,
)

print(
    "RSI_VALUE_SOURCE:",
    ast.unparse(rsi_value),
)
def build_import_table(tree):

    table = {}

    for node in tree.body:

        if isinstance(node, ast.ImportFrom):

            module = node.module

            for alias in node.names:

                local = alias.asname or alias.name

                table[local] = {
                    "module": module,
                    "symbol": alias.name,
                }

    return table


imports = build_import_table(tree)

if isinstance(rsi_value.func, ast.Name):
    root = rsi_value.func.id
else:
    root = None

print(
    "RSI_CALL_ROOT:",
    root,
)

print(
    "RSI_IMPORT_RECORD:",
    imports.get(root),
)

rsi_import_authority = (
    imports.get(root) == {
        "module": "indicators.rsi",
        "symbol": "rsi",
    }
)

print(
    "RSI_IMPORT_AUTHORITY:",
    "PASS"
    if rsi_import_authority
    else "FAIL",
)
#!/usr/bin/env python3

"""
R24
RSI Producer Authority
"""

import ast
from pathlib import Path

TARGET = Path("indicators/rsi.py")

tree = ast.parse(
    TARGET.read_text(
        encoding="utf-8"
    )
)

functions = []

for node in ast.walk(tree):

    if (
        isinstance(node, ast.FunctionDef)
        and node.name == "rsi"
    ):
        functions.append(node)

print(
    "RSI_FUNCTION_COUNT:",
    len(functions),
)

if len(functions) != 1:
    raise RuntimeError(
        "Expected exactly one rsi() function"
    )

rsi_function = functions[0]

print(
    "RSI_FUNCTION_NAME:",
    rsi_function.name,
)

print(
    "RSI_FUNCTION_LINE:",
    rsi_function.lineno,
)

parameters = [
    arg.arg
    for arg in rsi_function.args.args
]

print(
    "RSI_PARAMETERS:",
    parameters,
)

print(
    "RSI_PARAMETER_COUNT:",
    len(parameters),
)

signature_authority = (
    len(parameters) >= 1
    and parameters[0] == "candles"
)

print(
    "RSI_SIGNATURE_AUTHORITY:",
    "PASS"
    if signature_authority
    else "FAIL",
)
body_length = len(rsi_function.body)

print(
    "RSI_BODY_STATEMENT_COUNT:",
    body_length,
)

return_nodes = [
    node
    for node in ast.walk(rsi_function)
    if isinstance(node, ast.Return)
]

print(
    "RSI_RETURN_COUNT:",
    len(return_nodes),
)

body_authority = (
    body_length > 0
    and len(return_nodes) >= 1
)

print(
    "RSI_BODY_AUTHORITY:",
    "PASS"
    if body_authority
    else "FAIL",
)
return_node = return_nodes[0]

print(
    "RSI_RETURN_TYPE:",
    type(return_node.value).__name__,
)

print(
    "RSI_RETURN_SOURCE:",
    ast.unparse(return_node.value),
)

return_contract_authority = (
    return_node.value is not None
)

print(
    "RSI_RETURN_CONTRACT_AUTHORITY:",
    "PASS"
    if return_contract_authority
    else "FAIL",
)
producer_names = [
    "value",
    "signal",
]

producer_assignments = {}

for name in producer_names:

    matches = []

    for node in ast.walk(rsi_function):

        if not isinstance(node, ast.Assign):
            continue

        for target in node.targets:

            if (
                isinstance(target, ast.Name)
                and target.id == name
            ):
                matches.append(node)

    producer_assignments[name] = matches

for name in producer_names:

    matches = producer_assignments[name]

    print(
        f"{name.upper()}_ASSIGNMENT_COUNT:",
        len(matches),
    )

    if len(matches) >= 1:

        print(
            f"{name.upper()}_ASSIGNMENT_AUTHORITY:",
            "PASS",
        )

        for i, assignment in enumerate(matches, 1):

            print(
                f"{name.upper()}_{i}_TYPE:",
                type(assignment.value).__name__,
            )

            print(
                f"{name.upper()}_{i}_SOURCE:",
                ast.unparse(assignment.value),
            )

    else:

        print(
            f"{name.upper()}_ASSIGNMENT_AUTHORITY:",
            "FAIL",
        )
rs_assignments = []

for node in ast.walk(rsi_function):

    if isinstance(node, ast.Assign):

        for target in node.targets:

            if (
                isinstance(target, ast.Name)
                and target.id == "rs"
            ):
                rs_assignments.append(node)

print(
    "RS_ASSIGNMENT_COUNT:",
    len(rs_assignments),
)

if len(rs_assignments) >= 1:

    print(
        "RS_ASSIGNMENT_AUTHORITY:",
        "PASS",
    )

    for i, assignment in enumerate(rs_assignments, 1):

        print(
            f"RS_{i}_TYPE:",
            type(assignment.value).__name__,
        )

        print(
            f"RS_{i}_SOURCE:",
            ast.unparse(assignment.value),
        )

else:

    print(
        "RS_ASSIGNMENT_AUTHORITY:",
        "FAIL",
    )
