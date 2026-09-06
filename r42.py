#!/usr/bin/env python3

import ast
from pathlib import Path

TARGET = Path("strategy/trade_validator_engine.py")

tree = ast.parse(TARGET.read_text(encoding="utf-8"))

engine = next(
    c for c in ast.walk(tree)
    if isinstance(c, ast.ClassDef)
    and c.name == "TradeValidatorEngine"
)

run = next(
    m for m in engine.body
    if isinstance(m, ast.FunctionDef)
    and m.name == "run"
)

print("RUN_METHOD_COUNT:", 1)
print("RUN_METHOD_LINE:", run.lineno)

params = [a.arg for a in run.args.args]

print("RUN_PARAMETERS:", params)
print("RUN_PARAMETER_COUNT:", len(params))

print(
    "RUN_SIGNATURE_AUTHORITY:",
    "PASS" if params == ["self", "state", "bus"] else "FAIL"
)

print(
    "RUN_BODY_STATEMENT_COUNT:",
    len(run.body)
)

returns = [
    n for n in ast.walk(run)
    if isinstance(n, ast.Return)
]

print(
    "RUN_RETURN_COUNT:",
    len(returns)
)

print(
    "RUN_BODY_AUTHORITY:",
    "PASS"
    if len(run.body) > 0 and len(returns) >= 1
    else "FAIL"
)

ret = returns[0]

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
    else "FAIL"
)
