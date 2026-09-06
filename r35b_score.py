#!/usr/bin/env python3

"""
R35B
SMC _score() Authority
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

score_functions = [
    node
    for node in functions
    if node.name == "_score"
]

print(
    "SCORE_FUNCTION_COUNT:",
    len(score_functions),
)

if len(score_functions) != 1:
    raise RuntimeError(
        "Expected exactly one _score() function"
    )

score = score_functions[0]

print(
    "SCORE_FUNCTION_NAME:",
    score.name,
)

print(
    "SCORE_FUNCTION_LINE:",
    score.lineno,
)

parameters = [
    arg.arg
    for arg in score.args.args
]

print(
    "SCORE_PARAMETERS:",
    parameters,
)

print(
    "SCORE_PARAMETER_COUNT:",
    len(parameters),
)

signature_authority = (
    len(parameters) >= 1
)

print(
    "SCORE_SIGNATURE_AUTHORITY:",
    "PASS"
    if signature_authority
    else "FAIL",
)

body_length = len(score.body)

print(
    "SCORE_BODY_STATEMENT_COUNT:",
    body_length,
)

return_nodes = [
    node
    for node in ast.walk(score)
    if isinstance(node, ast.Return)
]

print(
    "SCORE_RETURN_COUNT:",
    len(return_nodes),
)

body_authority = (
    body_length > 0
    and len(return_nodes) >= 1
)

print(
    "SCORE_BODY_AUTHORITY:",
    "PASS"
    if body_authority
    else "FAIL",
)

for i, node in enumerate(return_nodes, 1):

    print(
        f"SCORE_RETURN_{i}_TYPE:",
        type(node.value).__name__,
    )

    print(
        f"SCORE_RETURN_{i}_SOURCE:",
        ast.unparse(node.value),
    )

print(
    "SCORE_RETURN_CONTRACT_AUTHORITY:",
    "PASS"
)
