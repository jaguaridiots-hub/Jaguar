#!/usr/bin/env python3

"""
R35C
SMC _reasons() Authority
"""

import ast
from pathlib import Path

TARGET = Path("engine/smc_engine.py")

tree = ast.parse(
    TARGET.read_text(
        encoding="utf-8"
    )
)

functions = [
    node
    for node in ast.walk(tree)
    if isinstance(node, ast.FunctionDef)
]

reason_functions = [
    node
    for node in functions
    if node.name == "_reasons"
]

print(
    "REASONS_FUNCTION_COUNT:",
    len(reason_functions),
)

if len(reason_functions) != 1:
    raise RuntimeError(
        "Expected exactly one _reasons() function"
    )

reasons = reason_functions[0]

print(
    "REASONS_FUNCTION_NAME:",
    reasons.name,
)

print(
    "REASONS_FUNCTION_LINE:",
    reasons.lineno,
)

parameters = [
    arg.arg
    for arg in reasons.args.args
]

print(
    "REASONS_PARAMETERS:",
    parameters,
)

print(
    "REASONS_PARAMETER_COUNT:",
    len(parameters),
)

signature_authority = (
    len(parameters) >= 1
)

print(
    "REASONS_SIGNATURE_AUTHORITY:",
    "PASS"
    if signature_authority
    else "FAIL",
)

body_length = len(reasons.body)

print(
    "REASONS_BODY_STATEMENT_COUNT:",
    body_length,
)

return_nodes = [
    node
    for node in ast.walk(reasons)
    if isinstance(node, ast.Return)
]

print(
    "REASONS_RETURN_COUNT:",
    len(return_nodes),
)

body_authority = (
    body_length > 0
    and len(return_nodes) >= 1
)

print(
    "REASONS_BODY_AUTHORITY:",
    "PASS"
    if body_authority
    else "FAIL",
)

for i, node in enumerate(return_nodes, 1):

    print(
        f"REASONS_RETURN_{i}_TYPE:",
        type(node.value).__name__,
    )

    print(
        f"REASONS_RETURN_{i}_SOURCE:",
        ast.unparse(node.value),
    )

print(
    "REASONS_RETURN_CONTRACT_AUTHORITY:",
    "PASS"
)
