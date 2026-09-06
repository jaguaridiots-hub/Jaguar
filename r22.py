#!/usr/bin/env python3

"""
R22
EMA Import Authority Diagnostic
"""

import ast
from pathlib import Path

TARGET = Path("indicators/indicator_engine.py")

tree = ast.parse(
    TARGET.read_text(encoding="utf-8")
)


def find_calculate(tree):

    for node in ast.walk(tree):

        if (
            isinstance(node, ast.ClassDef)
            and node.name == "IndicatorEngine"
        ):

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

        if (
            isinstance(node, ast.Return)
            and isinstance(node.value, ast.Dict)
        ):
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


ema_key, ema_value = find_dict_entry(
    return_dict,
    "ema",
)

print(
    "EMA_KEY:",
    ema_key.value,
)

print(
    "EMA_VALUE_TYPE:",
    type(ema_value).__name__,
)

print(
    "EMA_VALUE_SOURCE:",
    ast.unparse(ema_value),
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

if isinstance(ema_value.func, ast.Name):
    root = ema_value.func.id
else:
    root = None

print(
    "EMA_CALL_ROOT:",
    root,
)

print(
    "EMA_IMPORT_RECORD:",
    imports.get(root),
)

ema_import_authority = (
    imports.get(root) == {
        "module": "indicators.ema",
        "symbol": "ema",
    }
)

print(
    "EMA_IMPORT_AUTHORITY:",
    "PASS" if ema_import_authority else "FAIL",
)


