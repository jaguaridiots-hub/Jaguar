#!/usr/bin/env python3

"""
R35
Smart Money Engine Authority
"""

import ast
from pathlib import Path

TARGET = Path("engine/smc_engine.py")

tree = ast.parse(
    TARGET.read_text(
        encoding="utf-8"
    )
)

# --------------------------------------------------
# Discover all functions
# --------------------------------------------------

functions = [
    node
    for node in ast.walk(tree)
    if isinstance(node, ast.FunctionDef)
]

print(
    "FUNCTION_COUNT:",
    len(functions),
)

print("FUNCTION_NAMES:")

for func in functions:
    print(
        " -",
        func.name,
        "@ line",
        func.lineno,
    )

# --------------------------------------------------
# Locate production entry point
# --------------------------------------------------

smc_functions = [
    node
    for node in functions
    if node.name == "analyze"
]

print(
    "SMC_FUNCTION_COUNT:",
    len(smc_functions),
)

if len(smc_functions) != 1:
    raise RuntimeError(
        "Expected exactly one analyze() function"
    )

smc = smc_functions[0]

print(
    "SMC_FUNCTION_NAME:",
    smc.name,
)

print(
    "SMC_FUNCTION_LINE:",
    smc.lineno,
)

# --------------------------------------------------
# Verify signature
# --------------------------------------------------

parameters = [
    arg.arg
    for arg in smc.args.args
]

print(
    "SMC_PARAMETERS:",
    parameters,
)

print(
    "SMC_PARAMETER_COUNT:",
    len(parameters),
)

signature_authority = (
    len(parameters) >= 1
)

print(
    "SMC_SIGNATURE_AUTHORITY:",
    "PASS"
    if signature_authority
    else "FAIL",
)

# --------------------------------------------------
# Verify body
# --------------------------------------------------

body_length = len(smc.body)

print(
    "SMC_BODY_STATEMENT_COUNT:",
    body_length,
)

return_nodes = [
    node
    for node in ast.walk(smc)
    if isinstance(node, ast.Return)
]

print(
    "SMC_RETURN_COUNT:",
    len(return_nodes),
)

body_authority = (
    body_length > 0
    and len(return_nodes) >= 1
)

print(
    "SMC_BODY_AUTHORITY:",
    "PASS"
    if body_authority
    else "FAIL",
)
# --------------------------------------------------
# Verify return contract
# --------------------------------------------------

return_node = return_nodes[0]

print(
    "SMC_RETURN_TYPE:",
    type(return_node.value).__name__,
)

print(
    "SMC_RETURN_SOURCE:",
    ast.unparse(return_node.value),
)

return_authority = (
    return_node.value is not None
)

print(
    "SMC_RETURN_CONTRACT_AUTHORITY:",
    "PASS"
    if return_authority
    else "FAIL",
)
producer_names = [
    "_signal",
    "_score",
    "_reasons",
]

calls = []

for node in ast.walk(smc):

    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in producer_names
    ):
        calls.append(node)

print(
    "PRODUCER_CALL_COUNT:",
    len(calls),
)

found = sorted({
    node.func.id
    for node in calls
})

print(
    "PRODUCER_CALLS_FOUND:",
    found,
)

authority = (
    found == sorted(producer_names)
)

print(
    "PRODUCER_CALL_AUTHORITY:",
    "PASS"
    if authority
    else "FAIL",
)
