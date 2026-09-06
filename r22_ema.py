#!/usr/bin/env python3

"""
R22
EMA Producer Authority
"""

import ast
from pathlib import Path

TARGET = Path("indicators/ema.py")

tree = ast.parse(
    TARGET.read_text(
        encoding="utf-8"
    )
)


def find_ema(tree):

    matches = []

    for node in ast.walk(tree):

        if (
            isinstance(node, ast.FunctionDef)
            and node.name == "ema"
        ):
            matches.append(node)

    return matches


functions = find_ema(tree)

print(
    "EMA_FUNCTION_COUNT:",
    len(functions),
)

if len(functions) != 1:
    raise RuntimeError(
        "Expected exactly one ema() function"
    )

ema_function = functions[0]

print(
    "EMA_FUNCTION_NAME:",
    ema_function.name,
)

print(
    "EMA_FUNCTION_LINE:",
    ema_function.lineno,
)

parameters = [
    arg.arg
    for arg in ema_function.args.args
]

print(
    "EMA_PARAMETERS:",
    parameters,
)

print(
    "EMA_PARAMETER_COUNT:",
    len(parameters),
)

signature_authority = (
    len(parameters) >= 1
    and parameters[0] == "candles"
)

print(
    "EMA_SIGNATURE_AUTHORITY:",
    "PASS"
    if signature_authority
    else "FAIL",
)
body_length = len(ema_function.body)

print(
    "EMA_BODY_STATEMENT_COUNT:",
    body_length,
)

return_nodes = [
    node
    for node in ast.walk(ema_function)
    if isinstance(node, ast.Return)
]

print(
    "EMA_RETURN_COUNT:",
    len(return_nodes),
)

body_authority = (
    body_length > 0
    and len(return_nodes) >= 1
)

print(
    "EMA_BODY_AUTHORITY:",
    "PASS" if body_authority else "FAIL",
)
return_node = return_nodes[0]

print(
    "EMA_RETURN_TYPE:",
    type(return_node.value).__name__,
)

print(
    "EMA_RETURN_SOURCE:",
    ast.unparse(return_node.value),
)

contract_authority = (
    return_node.value is not None
)

print(
    "EMA_RETURN_CONTRACT_AUTHORITY:",
    "PASS" if contract_authority else "FAIL",
)
if not isinstance(return_node.value, ast.Dict):
    raise RuntimeError(
        "EMA return is not a dictionary"
    )

keys = []

for key in return_node.value.keys:

    if isinstance(key, ast.Constant):
        keys.append(key.value)
    else:
        keys.append(None)

print(
    "EMA_RETURN_KEYS:",
    keys,
)

expected = {
    "ema20",
    "ema50",
    "ema100",
    "ema200",
    "trend",
}

contract_authority = (
    set(keys) == expected
)

print(
    "EMA_DICTIONARY_CONTRACT_AUTHORITY:",
    "PASS"
    if contract_authority
    else "FAIL",
)
