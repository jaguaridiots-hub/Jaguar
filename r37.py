#!/usr/bin/env python3

"""
R37
Jaguar Brain V4 Authority
"""

import ast
from pathlib import Path

TARGET = Path("ai/jaguar_brain_v4.py")

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

brain = None

for cls in classes:
    print(
        "CLASS:",
        cls.name,
        "@ line",
        cls.lineno,
    )

    if cls.name == "JaguarBrainV4":
        brain = cls

if brain is None:
    raise RuntimeError(
        "JaguarBrainV4 class not found"
    )

methods = [
    node
    for node in brain.body
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
analyze_methods = [
    node
    for node in methods
    if node.name == "analyze"
]

print(
    "ANALYZE_METHOD_COUNT:",
    len(analyze_methods),
)

if len(analyze_methods) != 1:
    raise RuntimeError(
        "Expected exactly one analyze() method"
    )

analyze = analyze_methods[0]

print(
    "ANALYZE_METHOD_LINE:",
    analyze.lineno,
)

parameters = [
    arg.arg
    for arg in analyze.args.args
]

print(
    "ANALYZE_PARAMETERS:",
    parameters,
)

print(
    "ANALYZE_PARAMETER_COUNT:",
    len(parameters),
)

signature_authority = (
    len(parameters) == 1
    and parameters[0] == "state"
)

print(
    "ANALYZE_SIGNATURE_AUTHORITY:",
    "PASS"
    if signature_authority
    else "FAIL",
)

body_length = len(analyze.body)

print(
    "ANALYZE_BODY_STATEMENT_COUNT:",
    body_length,
)

return_nodes = [
    node
    for node in ast.walk(analyze)
    if isinstance(node, ast.Return)
]

print(
    "ANALYZE_RETURN_COUNT:",
    len(return_nodes),
)

print(
    "ANALYZE_BODY_AUTHORITY:",
    "PASS"
    if body_length > 0 and len(return_nodes) >= 1
    else "FAIL",
)

# --------------------------------------------------
# Verify analyze() return contract
# --------------------------------------------------

return_node = return_nodes[0]

print(
    "ANALYZE_RETURN_TYPE:",
    type(return_node.value).__name__,
)

print(
    "ANALYZE_RETURN_SOURCE:",
    ast.unparse(return_node.value),
)

print(
    "ANALYZE_RETURN_CONTRACT_AUTHORITY:",
    "PASS"
    if return_node.value is not None
    else "FAIL",
)
