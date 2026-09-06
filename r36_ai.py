#!/usr/bin/env python3

"""
R36
AI Probability Engine Authority
"""

import ast
from pathlib import Path

TARGET = Path("ai/probability_engine.py")

tree = ast.parse(
    TARGET.read_text(
        encoding="utf-8"
    )
)

classes = [
    node
    for node in ast.walk(tree)
    if isinstance(node, ast.ClassDef)
]

print("CLASS_COUNT:", len(classes))

for cls in classes:
    print(
        "CLASS:",
        cls.name,
        "@ line",
        cls.lineno,
    )
methods = [
    node
    for node in classes[0].body
    if isinstance(node, ast.FunctionDef)
]

print(
    "METHOD_COUNT:",
    len(methods),
)

print("METHOD_NAMES:")

for method in methods:
    print(
        " -",
        method.name,
        "@ line",
        method.lineno,
    )
engine = classes[0]

calculate_methods = [
    node
    for node in engine.body
    if isinstance(node, ast.FunctionDef)
    and node.name == "calculate"
]

print(
    "CALCULATE_METHOD_COUNT:",
    len(calculate_methods),
)

if len(calculate_methods) != 1:
    raise RuntimeError(
        "Expected exactly one calculate() method"
    )

calculate = calculate_methods[0]

print(
    "CALCULATE_METHOD_LINE:",
    calculate.lineno,
)

parameters = [
    arg.arg
    for arg in calculate.args.args
]

print(
    "CALCULATE_PARAMETERS:",
    parameters,
)

print(
    "CALCULATE_PARAMETER_COUNT:",
    len(parameters),
)

signature_authority = (
    len(parameters) == 1
    and parameters[0] == "state"
)


print(
    "CALCULATE_SIGNATURE_AUTHORITY:",
    "PASS"
    if signature_authority
    else "FAIL",
)

body_length = len(calculate.body)

print(
    "CALCULATE_BODY_STATEMENT_COUNT:",
    body_length,
)

return_nodes = [
    node
    for node in ast.walk(calculate)
    if isinstance(node, ast.Return)
]

print(
    "CALCULATE_RETURN_COUNT:",
    len(return_nodes),
)

print(
    "CALCULATE_BODY_AUTHORITY:",
    "PASS"
    if body_length > 0 and len(return_nodes) >= 1
    else "FAIL",
)
# --------------------------------------------------
# Verify calculate() return contract
# --------------------------------------------------

return_node = return_nodes[0]

print(
    "CALCULATE_RETURN_TYPE:",
    type(return_node.value).__name__,
)

print(
    "CALCULATE_RETURN_SOURCE:",
    ast.unparse(return_node.value),
)

print(
    "CALCULATE_RETURN_CONTRACT_AUTHORITY:",
    "PASS"
    if return_node.value is not None
    else "FAIL",
)
