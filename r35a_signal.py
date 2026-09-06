#!/usr/bin/env python3

"""
R35A
SMC _signal() Authority
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

signal_functions = [
    node
    for node in functions
    if node.name == "_signal"
]

print(
    "SIGNAL_FUNCTION_COUNT:",
    len(signal_functions),
)

if len(signal_functions) != 1:
    raise RuntimeError(
        "Expected exactly one _signal() function"
    )

signal = signal_functions[0]

print(
    "SIGNAL_FUNCTION_NAME:",
    signal.name,
)

print(
    "SIGNAL_FUNCTION_LINE:",
    signal.lineno,
)

parameters = [
    arg.arg
    for arg in signal.args.args
]

print(
    "SIGNAL_PARAMETERS:",
    parameters,
)

print(
    "SIGNAL_PARAMETER_COUNT:",
    len(parameters),
)

signature_authority = (
    len(parameters) >= 1
)

print(
    "SIGNAL_SIGNATURE_AUTHORITY:",
    "PASS"
    if signature_authority
    else "FAIL",
)

body_length = len(signal.body)

print(
    "SIGNAL_BODY_STATEMENT_COUNT:",
    body_length,
)

return_nodes = [
    node
    for node in ast.walk(signal)
    if isinstance(node, ast.Return)
]

print(
    "SIGNAL_RETURN_COUNT:",
    len(return_nodes),
)

body_authority = (
    body_length > 0
    and len(return_nodes) >= 1
)

print(
    "SIGNAL_BODY_AUTHORITY:",
    "PASS"
    if body_authority
    else "FAIL",
)

return_node = return_nodes[0]

print(
    "SIGNAL_RETURN_TYPE:",
    type(return_node.value).__name__,
)

print(
    "SIGNAL_RETURN_SOURCE:",
    ast.unparse(return_node.value),
)

print(
    "SIGNAL_RETURN_CONTRACT_AUTHORITY:",
    "PASS"
    if return_node.value is not None
    else "FAIL",
)
