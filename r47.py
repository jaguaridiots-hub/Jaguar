#!/usr/bin/env python3

import ast
from pathlib import Path

TARGET = Path("strategy/execution_confirmation_engine.py")

tree = ast.parse(TARGET.read_text(encoding="utf-8"))

engine = next(
    c for c in ast.walk(tree)
    if isinstance(c, ast.ClassDef)
    and c.name == "ExecutionConfirmationEngine"
)

run = next(
    f for f in engine.body
    if isinstance(f, ast.FunctionDef)
    and f.name == "run"
)

print("RUN_METHOD_LINE:", run.lineno)

params = [a.arg for a in run.args.args]

print("RUN_PARAMETERS:", params)
print("RUN_PARAMETER_COUNT:", len(params))

print(
    "RUN_SIGNATURE_AUTHORITY:",
    "PASS" if params == ["self", "state", "bus"] else "FAIL"
)

print("RUN_BODY_STATEMENT_COUNT:", len(run.body))

returns = [
    n for n in ast.walk(run)
    if isinstance(n, ast.Return)
]

print("RUN_RETURN_COUNT:", len(returns))

ret = returns[0]

print("RUN_RETURN_TYPE:", type(ret.value).__name__)
print("RUN_RETURN_SOURCE:", ast.unparse(ret.value))
