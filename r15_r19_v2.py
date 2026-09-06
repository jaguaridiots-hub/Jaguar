#!/usr/bin/env python3

"""
R15-R19_v2
ATR Dictionary Producer Authority Diagnostic

Goal:
    Prove that IndicatorEngine.calculate()
    produces the "atr" dictionary entry
    using the imported atr(candles) function.
"""

import ast
from pathlib import Path

TARGET = Path("indicators/indicator_engine.py")

source = TARGET.read_text(encoding="utf-8")

tree = ast.parse(source)

def find_calculate(tree):

    for node in ast.walk(tree):

        if isinstance(node, ast.ClassDef):

            if node.name != "IndicatorEngine":
                continue

            for child in node.body:

                if (
                    isinstance(child, ast.FunctionDef)
                    and child.name == "calculate"
                ):
                    return child

    raise RuntimeError(
        "IndicatorEngine.calculate not found"
    )

calculate = find_calculate(tree)

print("TARGET_FUNCTION:", calculate.name)
print("START_LINE:", calculate.lineno)


def find_return_dict(function):

    for node in ast.walk(function):

        if isinstance(node, ast.Return):

            if isinstance(node.value, ast.Dict):

                return node.value

    raise RuntimeError(
        "Return dictionary not found"
    )


return_dict = find_return_dict(calculate)

print(
    "RETURN_DICT_KEYS:",
    len(return_dict.keys),
)

def find_dict_entry(dictionary, key_name):

    for key, value in zip(
        dictionary.keys,
        dictionary.values,
    ):

        if (
            isinstance(key, ast.Constant)
            and key.value == key_name
        ):
            return key, value

    raise RuntimeError(
        f"{key_name} entry not found"
    )


atr_key, atr_value = find_dict_entry(
    return_dict,
    "atr",
)

print(
    "ATR_KEY:",
    atr_key.value,
)

print(
    "ATR_VALUE_TYPE:",
    type(atr_value).__name__,
)

print(
    "ATR_VALUE_SOURCE:",
    ast.unparse(atr_value),
)

def build_import_table(tree):

    table = {}

    for node in tree.body:

        if isinstance(node, ast.ImportFrom):

            module = node.module

            for alias in node.names:

                local = alias.asname or alias.name

                table[local] = {
                    "module": module,
                    "symbol": alias.name,
                }

    return table


imports = build_import_table(tree)

if isinstance(atr_value.func, ast.Name):
    root = atr_value.func.id
else:
    root = None

print("CALL_ROOT:", root)

print(
    "IMPORT_RECORD:",
    imports.get(root),
)

authority = (
    root == "atr"
    and imports.get(root) == {
        "module": "indicators.atr",
        "symbol": "atr",
    }
)

print()
print("=" * 80)
print("R15-R19_v2 FINAL")
print("=" * 80)

print("R15_R19_V2_TARGET_FUNCTION:", calculate.name)
print("R15_R19_V2_RETURN_KEY:", atr_key.value)
print("R15_R19_V2_CALL:", ast.unparse(atr_value))
print("R15_R19_V2_IMPORT:", imports.get(root))

print(
    "R15_R19_V2_FINAL_AUTHORITY:",
    "PASS" if authority else "FAIL",
)
