#!/usr/bin/env python3

"""
R34
IndicatorEngine Authority
"""

import ast
from pathlib import Path

TARGET = Path("indicators/indicator_engine.py")

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

print(
    "CLASS_COUNT:",
    len(classes),
)

engine_classes = [
    node
    for node in classes
    if node.name == "IndicatorEngine"
]

print(
    "INDICATORENGINE_CLASS_COUNT:",
    len(engine_classes),
)

if len(engine_classes) != 1:
    raise RuntimeError(
        "Expected exactly one IndicatorEngine class"
    )

engine = engine_classes[0]

print(
    "INDICATORENGINE_CLASS_NAME:",
    engine.name,
)

print(
    "INDICATORENGINE_START_LINE:",
    engine.lineno,
)
methods = [
    node
    for node in engine.body
    if isinstance(node, ast.FunctionDef)
]

print(
    "METHOD_COUNT:",
    len(methods),
)

calculate_methods = [
    node
    for node in methods
    if node.name == "calculate"
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
    "CALCULATE_METHOD_NAME:",
    calculate.name,
)

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
    and parameters[0] == "candles"
)

print(
    "CALCULATE_SIGNATURE_AUTHORITY:",
    "PASS"
    if signature_authority
    else "FAIL",
)
producer_names = [
    "atr",
    "ema",
    "rsi",
    "macd",
    "adx",
    "supertrend",
    "vwap",
    "bollinger",
    "fibonacci",
    "volume",
]

calls = []

for node in ast.walk(calculate):

    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in producer_names
    ):
        calls.append(node)

print(
    "INDICATOR_CALL_COUNT:",
    len(calls),
)

found = sorted({
    node.func.id
    for node in calls
})

print(
    "INDICATOR_CALLS_FOUND:",
    found,
)

authority = (
    len(found) == len(producer_names)
    and found == sorted(producer_names)
)

print(
    "INDICATOR_CALL_AUTHORITY:",
    "PASS"
    if authority
    else "FAIL",
)
return_nodes = [
    node
    for node in ast.walk(calculate)
    if isinstance(node, ast.Return)
]

print(
    "RETURN_COUNT:",
    len(return_nodes),
)

if len(return_nodes) != 1:
    raise RuntimeError(
        "Expected exactly one return statement"
    )

return_node = return_nodes[0]

print(
    "RETURN_TYPE:",
    type(return_node.value).__name__,
)

print(
    "RETURN_SOURCE:",
    ast.unparse(return_node.value),
)

return_authority = (
    isinstance(return_node.value, ast.Dict)
)

print(
    "RETURN_CONTRACT_AUTHORITY:",
    "PASS"
    if return_authority
    else "FAIL",
)
