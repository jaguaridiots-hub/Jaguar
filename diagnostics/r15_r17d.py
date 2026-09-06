import ast
import hashlib
import subprocess
from pathlib import Path

PHASE = (
    "PHASE 7.5E73B-R10-R4-R8-R15-R17D "
    "ATR DATA EXACT RHS EXPRESSION AND RECURSIVE LOCAL "
    "PRODUCER LINEAGE AUTHORITY DIAGNOSTIC"
)

EXPECTED_HEAD = "db017a77d82a8a8e5664d98108b7c3652c7c8479"
EXPECTED_PARENT = "dc8d54c6630e594b00286de9c0e74310eeb27122"

EXPECTED_HASHES = {
    "indicators/indicator_engine.py":
        "11964b156a6290ef6a5adca15781d79ace76f3477f8c6f907ded42fb10207d57",
    "backtest/temporal_structural_validator.py":
        "72d4c25a027da43d836af4d5098642372771b6ff5ad6752bfd2f396424b91df8",
    "engine/institutional_master.py":
        "dee3465dcc079cba50e41f3285bbda2801b2296a150eac5cdb75bf656e02efee",
    "engine/ai_brain.py":
        "e08baff5f2c5b22ae0057cdeb6f5d29536f5b3adac1ab2ad48e337427cb6062e",
    "trade_state.json":
        "909369d54d6fc6484add34c3f37a60727f6cd1799a824bc00740f2b21c4a435e",
    "indicators/atr.py":
        "6248b652f52567bd445a83e4a843164d176ccd6fbb04c6dc3f2bf64b503db7e1",
}

TARGET_PATH = Path("indicators/indicator_engine.py")

PRESERVE = [
    Path(path)
    for path in EXPECTED_HASHES
]


def git(*args):
    return subprocess.run(
        ["git", *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def text(data):
    return data.decode(
        "utf-8",
        errors="replace",
    )


def sha(data):
    return hashlib.sha256(data).hexdigest()


def section(name):
    print()
    print("=" * 100)
    print(name)
    print("=" * 100)


def source_of(node):
    if node is None:
        return None

    try:
        return ast.unparse(node)
    except Exception:
        return None


def assignment_targets(node):
    if isinstance(node, ast.Assign):
        return node.targets

    if isinstance(node, ast.AnnAssign):
        return [node.target]

    if isinstance(node, ast.NamedExpr):
        return [node.target]

    return []


def assignment_value(node):
    if isinstance(
        node,
        (
            ast.Assign,
            ast.AnnAssign,
            ast.NamedExpr,
        ),
    ):
        return node.value

    return None


def assigned_names(node):
    result = []

    for target in assignment_targets(node):
        for child in ast.walk(target):
            if isinstance(child, ast.Name):
                result.append(child.id)

    return result


def dotted_name(node):
    if isinstance(node, ast.Name):
        return node.id

    if isinstance(node, ast.Attribute):
        prefix = dotted_name(node.value)

        if prefix is None:
            return None

        return f"{prefix}.{node.attr}"

    return None


def call_name(node):
    if not isinstance(node, ast.Call):
        return None

    return dotted_name(node.func)


def expression_name_loads(node):
    return sorted(
        [
            {
                "name": child.id,
                "line": child.lineno,
                "column": child.col_offset,
                "source": source_of(child),
            }
            for child in ast.walk(node)
            if (
                isinstance(child, ast.Name)
                and isinstance(child.ctx, ast.Load)
            )
        ],
        key=lambda record: (
            record["line"],
            record["column"],
            record["name"],
        ),
    )


def build_parent_map(root):
    result = {}

    for parent in ast.walk(root):
        for child in ast.iter_child_nodes(parent):
            result[child] = parent

    return result


def enclosing_statement(node, parent_map):
    current = node

    while current in parent_map:
        current = parent_map[current]

        if isinstance(current, ast.stmt):
            return current

    return None


def build_import_records(tree):
    records = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                records.append(
                    {
                        "kind": "IMPORT_FROM",
                        "module": node.module,
                        "symbol": alias.name,
                        "local_name": (
                            alias.asname
                            if alias.asname
                            else alias.name
                        ),
                        "line": node.lineno,
                        "source": source_of(node),
                    }
                )

        elif isinstance(node, ast.Import):
            for alias in node.names:
                records.append(
                    {
                        "kind": "IMPORT",
                        "module": alias.name,
                        "symbol": None,
                        "local_name": (
                            alias.asname
                            if alias.asname
                            else alias.name.split(".")[0]
                        ),
                        "line": node.lineno,
                        "source": source_of(node),
                    }
                )

    return records


def assignment_records_for_name(
    owner,
    name,
    before_line,
):
    records = []

    for node in ast.walk(owner):
        if not isinstance(
            node,
            (
                ast.Assign,
                ast.AnnAssign,
                ast.NamedExpr,
            ),
        ):
            continue

        if node.lineno >= before_line:
            continue

        if name not in assigned_names(node):
            continue

        value = assignment_value(node)

        records.append(
            {
                "name": name,
                "line": node.lineno,
                "column": node.col_offset,
                "rhs_type": (
                    type(value).__name__
                    if value is not None
                    else None
                ),
                "rhs_source": source_of(value),
                "rhs_name_loads":
                    expression_name_loads(value)
                    if value is not None
                    else [],
                "rhs_call_records": [
                    {
                        "line": child.lineno,
                        "column": child.col_offset,
                        "call_name": call_name(child),
                        "call_source": source_of(child),
                    }
                    for child in sorted(
                        [
                            child
                            for child in ast.walk(value)
                            if isinstance(child, ast.Call)
                        ],
                        key=lambda child: (
                            child.lineno,
                            child.col_offset,
                        ),
                    )
                ]
                if value is not None
                else [],
                "statement_source": source_of(node),
            }
        )

    return sorted(
        records,
        key=lambda record: (
            record["line"],
            record["column"],
        ),
    )


def parameter_names(definition):
    result = []

    result.extend(
        argument.arg
        for argument in definition.args.posonlyargs
    )

    result.extend(
        argument.arg
        for argument in definition.args.args
    )

    if definition.args.vararg is not None:
        result.append(definition.args.vararg.arg)

    result.extend(
        argument.arg
        for argument in definition.args.kwonlyargs
    )

    if definition.args.kwarg is not None:
        result.append(definition.args.kwarg.arg)

    return result


print("=" * 100)
print(PHASE)
print("=" * 100)

head_before = text(
    git("rev-parse", "HEAD").stdout
).strip()

parent_before = text(
    git("rev-parse", "HEAD^").stdout
).strip()

status_before = text(
    git("status", "--porcelain=v1").stdout
)

cached_before = text(
    git("diff", "--cached", "--name-only").stdout
)

before = {
    str(path): (
        path.read_bytes()
        if path.exists()
        else None
    )
    for path in PRESERVE
}

section("PRE-DIAGNOSTIC AUTHORITY")

print("EXPECTED_HEAD:", EXPECTED_HEAD)
print("HEAD_BEFORE:", head_before)
print("EXPECTED_PARENT:", EXPECTED_PARENT)
print("PARENT_BEFORE:", parent_before)

hash_authority = True

for path_string, expected_hash in EXPECTED_HASHES.items():
    path = Path(path_string)

    data = (
        path.read_bytes()
        if path.exists()
        else None
    )

    actual_hash = (
        sha(data)
        if data is not None
        else None
    )

    record = {
        "path": str(path),
        "exists": path.exists(),
        "expected_sha256": expected_hash,
        "actual_sha256": actual_hash,
        "sha256_authority": (
            "PASS"
            if actual_hash == expected_hash
            else "FAIL"
        ),
    }

    if actual_hash != expected_hash:
        hash_authority = False

    print(
        "PRE_DIAGNOSTIC_TARGET_RECORD:",
        record,
    )

pre_authority = (
    head_before == EXPECTED_HEAD
    and parent_before == EXPECTED_PARENT
    and hash_authority
    and cached_before.strip() == ""
)

print(
    "R15_R17D_PRE_DIAGNOSTIC_AUTHORITY:",
    "PASS"
    if pre_authority
    else "FAIL",
)

if not pre_authority:
    print(
        "R15_R17D_ABORT_REASON: "
        "PRE_DIAGNOSTIC_AUTHORITY_FAIL"
    )
    raise SystemExit(2)

source = TARGET_PATH.read_text(
    encoding="utf-8"
)

tree = ast.parse(source)

parent_map = build_parent_map(tree)

definitions = [
    node
    for node in ast.walk(tree)
    if (
        isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        )
        and node.name == "update_market_state"
    )
]

if len(definitions) != 1:
    print(
        "R15_R17D_ABORT_REASON: "
        "UPDATE_OWNER_AUTHORITY_FAIL"
    )
    raise SystemExit(3)

definition = definitions[0]

parameters = set(
    parameter_names(definition)
)

import_records = build_import_records(tree)

section("ATR DATA EXACT RHS EXPRESSION AUTHORITY")

atr_data_assignments = []

for node in ast.walk(definition):
    if not isinstance(
        node,
        (
            ast.Assign,
            ast.AnnAssign,
            ast.NamedExpr,
        ),
    ):
        continue

    if "atr_data" not in assigned_names(node):
        continue

    value = assignment_value(node)

    statement = enclosing_statement(
        node,
        parent_map,
    )

    record = {
        "line": node.lineno,
        "column": node.col_offset,
        "rhs_type": (
            type(value).__name__
            if value is not None
            else None
        ),
        "rhs_source": source_of(value),
        "rhs_name_load_records":
            expression_name_loads(value)
            if value is not None
            else [],
        "rhs_call_count": (
            sum(
                1
                for child in ast.walk(value)
                if isinstance(child, ast.Call)
            )
            if value is not None
            else 0
        ),
        "statement_line": (
            statement.lineno
            if statement is not None
            else None
        ),
        "statement_source": source_of(statement),
    }

    atr_data_assignments.append(record)

    print(
        "ATR_DATA_EXACT_RHS_RECORD:",
        record,
    )

print(
    "ATR_DATA_EXACT_ASSIGNMENT_COUNT:",
    len(atr_data_assignments),
)

section("ATR DATA RHS ROOT SYMBOL AUTHORITY")

rhs_root_records = []

for assignment in atr_data_assignments:
    for load_record in assignment[
        "rhs_name_load_records"
    ]:
        name = load_record["name"]

        local_assignments = assignment_records_for_name(
            definition,
            name,
            assignment["line"],
        )

        matching_imports = [
            record
            for record in import_records
            if record["local_name"] == name
        ]

        record = {
            "atr_data_assignment_line":
                assignment["line"],
            "atr_data_rhs":
                assignment["rhs_source"],
            "root_name":
                name,
            "root_load_line":
                load_record["line"],
            "is_update_parameter":
                name in parameters,
            "local_assignment_count":
                len(local_assignments),
            "local_assignment_records":
                local_assignments,
            "import_binding_count":
                len(matching_imports),
            "import_bindings":
                matching_imports,
        }

        rhs_root_records.append(record)

        print(
            "ATR_DATA_RHS_ROOT_RECORD:",
            record,
        )

print(
    "ATR_DATA_RHS_ROOT_RECORD_COUNT:",
    len(rhs_root_records),
)

section("ATR DATA RECURSIVE LOCAL PRODUCER LINEAGE AUTHORITY")

lineage_records = []

terminal_records = []

visited = set()


def trace_local_name(
    name,
    before_line,
    depth,
    path,
):
    key = (
        name,
        before_line,
    )

    if key in visited:
        terminal = {
            "terminal_kind": "CYCLE_OR_REVISIT",
            "name": name,
            "before_line": before_line,
            "depth": depth,
            "path": path,
        }

        terminal_records.append(terminal)

        print(
            "ATR_DATA_LINEAGE_TERMINAL_RECORD:",
            terminal,
        )

        return

    visited.add(key)

    local_assignments = assignment_records_for_name(
        definition,
        name,
        before_line,
    )

    matching_imports = [
        record
        for record in import_records
        if record["local_name"] == name
    ]

    if local_assignments:
        selected = local_assignments[-1]

        record = {
            "depth": depth,
            "name": name,
            "before_line": before_line,
            "path": path,
            "classification":
                "LOCAL_ASSIGNMENT",
            "selected_assignment":
                selected,
        }

        lineage_records.append(record)

        print(
            "ATR_DATA_LINEAGE_RECORD:",
            record,
        )

        child_names = [
            load["name"]
            for load in selected[
                "rhs_name_loads"
            ]
        ]

        if not child_names:
            terminal = {
                "terminal_kind":
                    "LOCAL_ASSIGNMENT_WITHOUT_NAME_LOAD",
                "name": name,
                "before_line": before_line,
                "depth": depth,
                "path": path,
                "selected_assignment":
                    selected,
            }

            terminal_records.append(terminal)

            print(
                "ATR_DATA_LINEAGE_TERMINAL_RECORD:",
                terminal,
            )

        for child_name in child_names:
            trace_local_name(
                child_name,
                selected["line"],
                depth + 1,
                path + [
                    {
                        "name": name,
                        "assignment_line":
                            selected["line"],
                        "rhs":
                            selected["rhs_source"],
                    }
                ],
            )

        return

    if name in parameters:
        terminal = {
            "terminal_kind": "UPDATE_PARAMETER",
            "name": name,
            "before_line": before_line,
            "depth": depth,
            "path": path,
        }

        terminal_records.append(terminal)

        print(
            "ATR_DATA_LINEAGE_TERMINAL_RECORD:",
            terminal,
        )

        return

    if matching_imports:
        terminal = {
            "terminal_kind": "IMPORT_BINDING",
            "name": name,
            "before_line": before_line,
            "depth": depth,
            "path": path,
            "import_bindings":
                matching_imports,
        }

        terminal_records.append(terminal)

        print(
            "ATR_DATA_LINEAGE_TERMINAL_RECORD:",
            terminal,
        )

        return

    terminal = {
        "terminal_kind": "UNRESOLVED_NAME",
        "name": name,
        "before_line": before_line,
        "depth": depth,
        "path": path,
    }

    terminal_records.append(terminal)

    print(
        "ATR_DATA_LINEAGE_TERMINAL_RECORD:",
        terminal,
    )


for assignment in atr_data_assignments:
    for load_record in assignment[
        "rhs_name_load_records"
    ]:
        trace_local_name(
            load_record["name"],
            assignment["line"],
            0,
            [
                {
                    "name": "atr_data",
                    "assignment_line":
                        assignment["line"],
                    "rhs":
                        assignment["rhs_source"],
                }
            ],
        )

print(
    "ATR_DATA_RECURSIVE_LINEAGE_RECORD_COUNT:",
    len(lineage_records),
)

print(
    "ATR_DATA_RECURSIVE_TERMINAL_RECORD_COUNT:",
    len(terminal_records),
)

section("ATR DATA CALL-BEARING LOCAL PRODUCER AUTHORITY")

call_bearing_lineage_records = []

for lineage_record in lineage_records:
    assignment = lineage_record[
        "selected_assignment"
    ]

    for call_record in assignment[
        "rhs_call_records"
    ]:
        dotted = call_record["call_name"]

        root = (
            dotted.split(".")[0]
            if dotted
            else None
        )

        matching_imports = [
            record
            for record in import_records
            if record["local_name"] == root
        ]

        record = {
            "lineage_depth":
                lineage_record["depth"],
            "local_name":
                lineage_record["name"],
            "assignment_line":
                assignment["line"],
            "assignment_rhs":
                assignment["rhs_source"],
            "call_name":
                dotted,
            "call_source":
                call_record["call_source"],
            "root_name":
                root,
            "matching_import_records":
                matching_imports,
        }

        call_bearing_lineage_records.append(
            record
        )

        print(
            "ATR_DATA_CALL_BEARING_LINEAGE_RECORD:",
            record,
        )

exact_atr_import_call_records = [
    record
    for record in call_bearing_lineage_records
    if any(
        (
            binding["kind"] == "IMPORT_FROM"
            and binding["module"] == "indicators.atr"
            and binding["symbol"] == "atr"
        )
        for binding in record[
            "matching_import_records"
        ]
    )
]

for record in exact_atr_import_call_records:
    print(
        "ATR_DATA_EXACT_ATR_IMPORT_CALL_LINEAGE_RECORD:",
        record,
    )

print(
    "ATR_DATA_CALL_BEARING_LINEAGE_RECORD_COUNT:",
    len(call_bearing_lineage_records),
)

print(
    "ATR_DATA_EXACT_ATR_IMPORT_CALL_LINEAGE_RECORD_COUNT:",
    len(exact_atr_import_call_records),
)

section("ATR DATA NON-CALL PRODUCER CAUSAL CLASSIFICATION")

single_assignment_authority = (
    len(atr_data_assignments) == 1
)

rhs_non_call_authority = (
    single_assignment_authority
    and atr_data_assignments[0][
        "rhs_call_count"
    ] == 0
)

exact_atr_lineage_authority = (
    len(exact_atr_import_call_records) == 1
)

parameter_terminal_records = [
    record
    for record in terminal_records
    if record["terminal_kind"] == "UPDATE_PARAMETER"
]

import_terminal_records = [
    record
    for record in terminal_records
    if record["terminal_kind"] == "IMPORT_BINDING"
]

unresolved_terminal_records = [
    record
    for record in terminal_records
    if record["terminal_kind"] == "UNRESOLVED_NAME"
]

if (
    single_assignment_authority
    and rhs_non_call_authority
    and exact_atr_lineage_authority
):
    classification = (
        "ATR_DATA_NON_CALL_RHS_TRANSITIVELY_PROJECTS_"
        "IMPORTED_INDICATORS_ATR_ATR_CALL_RESULT"
    )

    next_owner = (
        "ATR_INVALID_MINIMUM_DOMAIN_NATIVE_DICT_"
        "FALLBACK_CONTRACT_OWNER"
    )

    causal_authority = True

elif (
    single_assignment_authority
    and rhs_non_call_authority
    and len(parameter_terminal_records) >= 1
):
    classification = (
        "ATR_DATA_NON_CALL_RHS_TRANSITIVELY_REACHES_"
        "UPDATE_PARAMETER_LINEAGE"
    )

    next_owner = (
        "ATR_DATA_PARAMETER_TO_LOCAL_PRODUCER_OWNER"
    )

    causal_authority = True

elif (
    single_assignment_authority
    and rhs_non_call_authority
    and len(import_terminal_records) >= 1
):
    classification = (
        "ATR_DATA_NON_CALL_RHS_TRANSITIVELY_REACHES_"
        "IMPORT_BINDING_WITHOUT_EXACT_ATR_CALL_PROOF"
    )

    next_owner = (
        "ATR_DATA_IMPORT_BOUND_PRODUCER_SEMANTIC_OWNER"
    )

    causal_authority = True

else:
    classification = (
        "ATR_DATA_NON_CALL_RHS_RECURSIVE_LOCAL_"
        "PRODUCER_LINEAGE_UNRESOLVED"
    )

    next_owner = (
        "ATR_DATA_EXACT_RHS_EXPRESSION_SEMANTIC_OWNER"
    )

    causal_authority = False

print(
    "SINGLE_ATR_DATA_ASSIGNMENT_AUTHORITY:",
    "PASS"
    if single_assignment_authority
    else "FAIL",
)

print(
    "ATR_DATA_EXACT_RHS_NON_CALL_AUTHORITY:",
    "PASS"
    if rhs_non_call_authority
    else "FAIL",
)

print(
    "ATR_DATA_EXACT_ATR_IMPORT_CALL_LINEAGE_AUTHORITY:",
    "PASS"
    if exact_atr_lineage_authority
    else "FAIL",
)

print(
    "ATR_DATA_PARAMETER_TERMINAL_RECORD_COUNT:",
    len(parameter_terminal_records),
)

print(
    "ATR_DATA_IMPORT_TERMINAL_RECORD_COUNT:",
    len(import_terminal_records),
)

print(
    "ATR_DATA_UNRESOLVED_TERMINAL_RECORD_COUNT:",
    len(unresolved_terminal_records),
)

print(
    "R15_R17D_CLASSIFICATION:",
    classification,
)

print(
    "R15_R17D_NEXT_OWNER_CLASSIFICATION:",
    next_owner,
)

print(
    "R15_ATR_DATA_NON_CALL_PRODUCER_CAUSAL_AUTHORITY:",
    "PASS"
    if causal_authority
    else "FAIL",
)

print("SOURCE_REPAIR_AUTHORIZED: NO")
print("SOURCE_REPAIR_APPLIED: NO")

section("POST-DIAGNOSTIC REPOSITORY AUTHORITY")

head_after = text(
    git("rev-parse", "HEAD").stdout
).strip()

parent_after = text(
    git("rev-parse", "HEAD^").stdout
).strip()

status_after = text(
    git("status", "--porcelain=v1").stdout
)

cached_after = text(
    git("diff", "--cached", "--name-only").stdout
)

bytes_preserved = True

for relative, original in before.items():
    path = Path(relative)

    current = (
        path.read_bytes()
        if path.exists()
        else None
    )

    preserved = current == original

    if not preserved:
        bytes_preserved = False

    print(
        "TARGET_RECORD_AFTER:",
        {
            "path": relative,
            "exists": path.exists(),
            "sha256": (
                sha(current)
                if current is not None
                else None
            ),
            "bytes_preserved": (
                "PASS"
                if preserved
                else "FAIL"
            ),
        },
    )

repository_authority = (
    head_after == head_before
    and parent_after == parent_before
    and bytes_preserved
    and status_after == status_before
    and cached_after.strip() == ""
)

print("HEAD_AFTER:", head_after)

print(
    "HEAD_PRESERVED:",
    "PASS"
    if head_after == head_before
    else "FAIL",
)

print(
    "PARENT_PRESERVED:",
    "PASS"
    if parent_after == parent_before
    else "FAIL",
)

print(
    "TARGET_BYTES_PRESERVED:",
    "PASS"
    if bytes_preserved
    else "FAIL",
)

print(
    "PORCELAIN_PRESERVED:",
    "PASS"
    if status_after == status_before
    else "FAIL",
)

print(
    "INDEX_EMPTY_AFTER_DIAGNOSTIC:",
    "PASS"
    if cached_after.strip() == ""
    else "FAIL",
)

print(
    "R15_POST_DIAGNOSTIC_REPOSITORY_AUTHORITY:",
    "PASS"
    if repository_authority
    else "FAIL",
)

section("R15-R17D FINAL")

final_authority = (
    causal_authority
    and repository_authority
)

print(
    "R15_R17D_TARGET_OWNER:",
    "indicators/indicator_engine.py::update_market_state",
)

print(
    "R15_R17D_TARGET_LOCAL_SYMBOL:",
    "atr_data",
)

print(
    "R15_R17D_ATR_DATA_EXACT_ASSIGNMENT_COUNT:",
    len(atr_data_assignments),
)

print(
    "R15_R17D_ATR_DATA_EXACT_RHS_TYPE:",
    (
        atr_data_assignments[0]["rhs_type"]
        if len(atr_data_assignments) == 1
        else None
    ),
)

print(
    "R15_R17D_ATR_DATA_EXACT_RHS_SOURCE:",
    (
        atr_data_assignments[0]["rhs_source"]
        if len(atr_data_assignments) == 1
        else None
    ),
)

print(
    "R15_R17D_ATR_DATA_EXACT_RHS_CALL_COUNT:",
    (
        atr_data_assignments[0]["rhs_call_count"]
        if len(atr_data_assignments) == 1
        else None
    ),
)

print(
    "R15_R17D_ATR_DATA_RHS_ROOT_RECORD_COUNT:",
    len(rhs_root_records),
)

print(
    "R15_R17D_ATR_DATA_RECURSIVE_LINEAGE_RECORD_COUNT:",
    len(lineage_records),
)

print(
    "R15_R17D_ATR_DATA_RECURSIVE_TERMINAL_RECORD_COUNT:",
    len(terminal_records),
)

print(
    "R15_R17D_ATR_DATA_CALL_BEARING_LINEAGE_RECORD_COUNT:",
    len(call_bearing_lineage_records),
)

print(
    "R15_R17D_ATR_DATA_EXACT_ATR_IMPORT_CALL_LINEAGE_RECORD_COUNT:",
    len(exact_atr_import_call_records),
)

print(
    "R15_R17D_ATR_DATA_PARAMETER_TERMINAL_RECORD_COUNT:",
    len(parameter_terminal_records),
)

print(
    "R15_R17D_ATR_DATA_IMPORT_TERMINAL_RECORD_COUNT:",
    len(import_terminal_records),
)

print(
    "R15_R17D_ATR_DATA_UNRESOLVED_TERMINAL_RECORD_COUNT:",
    len(unresolved_terminal_records),
)

print(
    "R15_R17D_CLASSIFICATION:",
    classification,
)

print(
    "R15_R17D_NEXT_OWNER_CLASSIFICATION:",
    next_owner,
)

print(
    "R15_ATR_DATA_NON_CALL_PRODUCER_CAUSAL_AUTHORITY:",
    "PASS"
    if causal_authority
    else "FAIL",
)

print(
    "R15_POST_DIAGNOSTIC_REPOSITORY_AUTHORITY:",
    "PASS"
    if repository_authority
    else "FAIL",
)

print(
    "R15_R17D_FINAL_AUTHORITY:",
    "PASS"
    if final_authority
    else "FAIL",
)

print("SOURCE_REPAIR_AUTHORIZED: NO")
print("SOURCE_REPAIR_APPLIED: NO")
print("STAGING_AUTHORIZED: NO")
print("COMMIT_AUTHORIZED: NO")
print("COMMIT_APPLIED: NO")
print("CLEANUP_AUTHORIZED: NO")

print(
    "NEXT_ACTION:",
    (
        "REPORT_OUTPUT_ONLY_FOR_ATR_DATA_NON_CALL_PRODUCER_LINEAGE_REVIEW"
        if final_authority
        else "STOP_AND_REPORT_R15_R17D_AUTHORITY_FAILURE"
    ),
)

