#!/usr/bin/env python3

"""
R20
ATR Import Resolution Authority
"""

import ast
from pathlib import Path

TARGET = Path("indicators/atr.py")

source = TARGET.read_text(encoding="utf-8")

tree = ast.parse(source)


def find_atr(tree):

    matches = []

    for node in ast.walk(tree):

        if (
            isinstance(node, ast.FunctionDef)
            and node.name == "atr"
        ):
            matches.append(node)

    return matches


functions = find_atr(tree)

print("ATR_FUNCTION_COUNT:", len(functions))

if len(functions) == 1:

    atr_function = functions[0]

    print("ATR_FUNCTION_NAME:", atr_function.name)
    print("ATR_FUNCTION_LINE:", atr_function.lineno)

else:

    raise RuntimeError(
        "Expected exactly one atr() function"
    )

parameters = [
    arg.arg
    for arg in atr_function.args.args
]

print("ATR_PARAMETERS:", parameters)

print(
    "ATR_PARAMETER_COUNT:",
    len(parameters),
)

signature_authority = (
    len(parameters) >= 1
    and parameters[0] == "candles"
)

print(
    "ATR_SIGNATURE_AUTHORITY:",
    "PASS" if signature_authority else "FAIL",
)

body_length = len(atr_function.body)

print(
    "ATR_BODY_STATEMENT_COUNT:",
    body_length,
)

return_nodes = [
    node
    for node in ast.walk(atr_function)
    if isinstance(node, ast.Return)
]

print(
    "ATR_RETURN_COUNT:",
    len(return_nodes),
)

body_authority = (
    body_length > 0
    and len(return_nodes) >= 1
)

print(
    "ATR_BODY_AUTHORITY:",
    "PASS" if body_authority else "FAIL",
)

return_node = return_nodes[0]

print(
    "ATR_RETURN_TYPE:",
    type(return_node.value).__name__,
)

try:
    source = ast.unparse(return_node.value)
except Exception:
    source = None

print(
    "ATR_RETURN_SOURCE:",
    source,
)


if not isinstance(return_node.value, ast.Dict):
    raise RuntimeError(
        "ATR return is not a dictionary"
    )

keys = []

for key in return_node.value.keys:

    if isinstance(key, ast.Constant):
        keys.append(key.value)
    else:
        keys.append(None)

print("ATR_RETURN_KEYS:", keys)

value_key_authority = "value" in keys
volatility_key_authority = "volatility" in keys

print(
    "ATR_VALUE_KEY_AUTHORITY:",
    "PASS" if value_key_authority else "FAIL",
)

print(
    "ATR_VOLATILITY_KEY_AUTHORITY:",
    "PASS" if volatility_key_authority else "FAIL",
)

value_expr = None

for key, value in zip(
    return_node.value.keys,
    return_node.value.values,
):

    if (
        isinstance(key, ast.Constant)
        and key.value == "value"
    ):
        value_expr = value
        break

if value_expr is None:
    raise RuntimeError(
        "value key not found"
    )

print(
    "ATR_VALUE_EXPR_TYPE:",
    type(value_expr).__name__,
)

print(
    "ATR_VALUE_EXPR_SOURCE:",
    ast.unparse(value_expr),
)

value_contract_authority = (
    isinstance(value_expr, ast.Call)
    and isinstance(value_expr.func, ast.Name)
    and value_expr.func.id == "round"
)

print(
    "ATR_VALUE_CONTRACT_AUTHORITY:",
    "PASS" if value_contract_authority else "FAIL",
)

value_assignments = []

for node in ast.walk(atr_function):

    if isinstance(node, ast.Assign):

        for target in node.targets:

            if (
                isinstance(target, ast.Name)
                and target.id == "value"
            ):

                value_assignments.append(node)

print(
    "ATR_VALUE_ASSIGNMENT_COUNT:",
    len(value_assignments),
)

if len(value_assignments) == 1:

    assignment = value_assignments[0]

    print(
        "ATR_VALUE_ASSIGNMENT_TYPE:",
        type(assignment.value).__name__,
    )

    print(
        "ATR_VALUE_ASSIGNMENT_SOURCE:",
        ast.unparse(assignment.value),
    )

else:

    print(
        "ATR_VALUE_ASSIGNMENT_AUTHORITY: FAIL"
    )
