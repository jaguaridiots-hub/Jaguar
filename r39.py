#!/usr/bin/env python3

"""
R39
Risk Manager Runner Authority
"""

import ast
from pathlib import Path

TARGET = Path("core/risk_manager_engine.py")

tree = ast.parse(TARGET.read_text(encoding="utf-8"))

classes = [
    n for n in ast.walk(tree)
    if isinstance(n, ast.ClassDef)
]

print("CLASS_COUNT:", len(classes))

runner = next(
    c for c in classes
    if c.name == "RiskManagerEngineRunner"
)

print("RUNNER_CLASS_NAME:", runner.name)
print("RUNNER_CLASS_LINE:", runner.lineno)

methods = [
    n for n in runner.body
    if isinstance(n, ast.FunctionDef)
]

print("METHOD_COUNT:", len(methods))

for m in methods:
    print("METHOD:", m.name, "@", m.lineno)
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
    parameters == ["self", "state", "bus"]
)

print(
    "RUN_SIGNATURE_AUTHORITY:",
    "PASS"
    if signature_authority
    else "FAIL",
)

print(
    "RUN_BODY_STATEMENT_COUNT:",
    len(run_method.body),
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
    if len(run_method.body) > 0 and len(return_nodes) >= 1
    else "FAIL",
)

ret = return_nodes[0]

print(
    "RUN_RETURN_TYPE:",
    type(ret.value).__name__,
)

print(
    "RUN_RETURN_SOURCE:",
    ast.unparse(ret.value),
)

print(
    "RUN_RETURN_CONTRACT_AUTHORITY:",
    "PASS"
    if ret.value is not None
    else "FAIL",
)
