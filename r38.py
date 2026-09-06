#!/usr/bin/env python3

"""
R38
Trade Planner Engine Runner Authority
"""

import ast
from pathlib import Path

TARGET = Path("core/trade_planner_engine.py")

tree = ast.parse(
    TARGET.read_text(encoding="utf-8")
)

classes = [
    node
    for node in ast.walk(tree)
    if isinstance(node, ast.ClassDef)
]

print("CLASS_COUNT:", len(classes))

runner_classes = [
    node
    for node in classes
    if node.name == "TradePlannerEngineRunner"
]

print(
    "RUNNER_CLASS_COUNT:",
    len(runner_classes),
)

if len(runner_classes) != 1:
    raise RuntimeError(
        "Expected exactly one TradePlannerEngineRunner"
    )

runner = runner_classes[0]

print(
    "RUNNER_CLASS_NAME:",
    runner.name,
)

print(
    "RUNNER_CLASS_LINE:",
    runner.lineno,
)

methods = [
    node
    for node in runner.body
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
run_methods = [
    node
    for node in methods
    if node.name == "run"
]

print(
    "RUN_METHOD_COUNT:",
    len(run_methods),
)

if len(run_methods) != 1:
    raise RuntimeError(
        "Expected exactly one run() method"
    )

run_method = run_methods[0]

print(
    "RUN_METHOD_LINE:",
    run_method.lineno,
)

parameters = [
    arg.arg
    for arg in run_method.args.args
]

print(
    "RUN_PARAMETERS:",
    parameters,
)

print(
    "RUN_PARAMETER_COUNT:",
    len(parameters),
)

signature_authority = (
    len(parameters) == 3
    and parameters == ["self", "state", "bus"]
)

print(
    "RUN_SIGNATURE_AUTHORITY:",
    "PASS"
    if signature_authority
    else "FAIL",
)

body_length = len(run_method.body)

print(
    "RUN_BODY_STATEMENT_COUNT:",
    body_length,
)

return_nodes = [
    node
    for node in ast.walk(run_method)
    if isinstance(node, ast.Return)
]

print(
    "RUN_RETURN_COUNT:",
    len(return_nodes),
)

print(
    "RUN_BODY_AUTHORITY:",
    "PASS"
    if body_length > 0 and len(return_nodes) >= 1
    else "FAIL",
)

return_node = return_nodes[0]

print(
    "RUN_RETURN_TYPE:",
    type(return_node.value).__name__,
)

print(
    "RUN_RETURN_SOURCE:",
    ast.unparse(return_node.value),
)

print(
    "RUN_RETURN_CONTRACT_AUTHORITY:",
    "PASS"
    if return_node.value is not None
    else "FAIL",
)
