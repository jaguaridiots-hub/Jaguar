import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

DEFAULT_PROVENANCE = ROOT / (
    "backtest/"
    "temporal_structural_deterministic_baseline."
    "provenance.json"
)


def sha256(path):

    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def load_csv(path):

    with path.open(
        newline="",
    ) as handle:

        return list(
            csv.DictReader(handle)
        )


def clean(value):

    if value is None:

        return ""

    return str(value).strip()


def resolve_path(value):

    path = Path(value)

    if path.is_absolute():

        return path

    return ROOT / path


def compare_semantics(
    baseline_path,
    replay_path,
):

    baseline_rows = load_csv(
        baseline_path
    )

    replay_rows = load_csv(
        replay_path
    )

    if not baseline_rows:

        raise RuntimeError(
            "Canonical baseline is empty"
        )

    if not replay_rows:

        raise RuntimeError(
            "Verification replay is empty"
        )

    baseline_fields = list(
        baseline_rows[0].keys()
    )

    replay_fields = list(
        replay_rows[0].keys()
    )

    field_contract_match = (
        baseline_fields
        == replay_fields
    )

    baseline = {
        clean(
            row.get("index")
        ): row
        for row in baseline_rows
    }

    replay = {
        clean(
            row.get("index")
        ): row
        for row in replay_rows
    }

    indices = sorted(
        set(baseline)
        | set(replay),
        key=lambda value: int(value),
    )

    changed_indices = []

    missing_indices = []

    field_changes = Counter()

    if field_contract_match:

        fields = baseline_fields

    else:

        fields = sorted(
            set(baseline_fields)
            | set(replay_fields)
        )

    for index in indices:

        before = baseline.get(
            index
        )

        after = replay.get(
            index
        )

        if (
            before is None
            or after is None
        ):

            missing_indices.append(
                index
            )

            changed_indices.append(
                index
            )

            continue

        row_changed = False

        for field in fields:

            before_value = clean(
                before.get(field)
            )

            after_value = clean(
                after.get(field)
            )

            if (
                before_value
                == after_value
            ):

                continue

            row_changed = True

            field_changes[
                field
            ] += 1

        if row_changed:

            changed_indices.append(
                index
            )

    return {
        "baseline_rows": len(
            baseline_rows
        ),
        "replay_rows": len(
            replay_rows
        ),
        "baseline_fields": baseline_fields,
        "replay_fields": replay_fields,
        "field_contract_match": (
            field_contract_match
        ),
        "changed_indices": changed_indices,
        "missing_indices": missing_indices,
        "field_changes": dict(
            field_changes
        ),
        "semantic_identity": (
            field_contract_match
            and not changed_indices
            and not missing_indices
            and not field_changes
        ),
    }


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Jaguar same-input temporal structural "
            "regression gate"
        )
    )

    parser.add_argument(
        "--provenance",
        default=str(
            DEFAULT_PROVENANCE
        ),
    )

    args = parser.parse_args()

    provenance_path = resolve_path(
        args.provenance
    )

    if not provenance_path.exists():

        raise FileNotFoundError(
            "Provenance file does not exist: "
            f"{provenance_path}"
        )

    provenance = json.loads(
        provenance_path.read_text()
    )

    fixture = resolve_path(
        provenance[
            "fixture"
        ][
            "path"
        ]
    )

    fixture_metadata = resolve_path(
        provenance[
            "fixture"
        ][
            "metadata_path"
        ]
    )

    validator = resolve_path(
        provenance[
            "validator"
        ][
            "path"
        ]
    )

    baseline = resolve_path(
        provenance[
            "baseline"
        ][
            "path"
        ]
    )

    symbol = provenance[
        "symbol"
    ]

    timeframe = provenance[
        "timeframe"
    ]

    warmup = int(
        provenance[
            "warmup"
        ]
    )

    print()
    print("=" * 100)
    print(
        "JAGUAR QUANT X - SAME-INPUT "
        "TEMPORAL STRUCTURAL REGRESSION GATE"
    )
    print("=" * 100)

    print(
        "Provenance :",
        provenance_path,
    )

    print(
        "Fixture    :",
        fixture,
    )

    print(
        "Validator  :",
        validator,
    )

    print(
        "Baseline   :",
        baseline,
    )

    print(
        "Symbol     :",
        symbol,
    )

    print(
        "Timeframe  :",
        timeframe,
    )

    print(
        "Warmup     :",
        warmup,
    )

    print("=" * 100)

    required_paths = [
        fixture,
        fixture_metadata,
        validator,
        baseline,
    ]

    for path in required_paths:

        if not path.exists():

            raise FileNotFoundError(
                "Required regression asset missing: "
                f"{path}"
            )

    print()
    print(
        "===== IMMUTABLE INPUT CONTRACT ====="
    )

    fixture_actual = sha256(
        fixture
    )

    fixture_expected = provenance[
        "fixture"
    ][
        "sha256"
    ]

    metadata_actual = sha256(
        fixture_metadata
    )

    metadata_expected = provenance[
        "fixture"
    ][
        "metadata_sha256"
    ]

    fixture_ok = (
        fixture_actual
        == fixture_expected
    )

    metadata_ok = (
        metadata_actual
        == metadata_expected
    )

    print(
        "Fixture SHA expected:",
        fixture_expected,
    )

    print(
        "Fixture SHA actual  :",
        fixture_actual,
    )

    print(
        "Fixture identity    :",
        "PASS"
        if fixture_ok
        else "FAIL",
    )

    print(
        "Metadata identity   :",
        "PASS"
        if metadata_ok
        else "FAIL",
    )

    if not fixture_ok:

        print(
            "REGRESSION_GATE: INVALID_FIXTURE"
        )

        return 20

    if not metadata_ok:

        print(
            "REGRESSION_GATE: "
            "INVALID_FIXTURE_METADATA"
        )

        return 21

    print()
    print(
        "===== IMPLEMENTATION PROVENANCE ====="
    )

    implementation_changes = {}

    validator_expected = provenance[
        "validator"
    ][
        "sha256"
    ]

    validator_actual = sha256(
        validator
    )

    if (
        validator_actual
        != validator_expected
    ):

        implementation_changes[
            str(
                validator.relative_to(
                    ROOT
                )
            )
        ] = {
            "expected": validator_expected,
            "actual": validator_actual,
        }

    for path_string, expected in provenance[
        "production_fingerprints"
    ].items():

        path = resolve_path(
            path_string
        )

        if not path.exists():

            implementation_changes[
                path_string
            ] = {
                "expected": expected,
                "actual": "MISSING",
            }

            continue

        actual = sha256(
            path
        )

        if actual != expected:

            implementation_changes[
                path_string
            ] = {
                "expected": expected,
                "actual": actual,
            }

    print(
        "Implementation changes:",
        len(
            implementation_changes
        ),
    )

    for path, change in (
        implementation_changes.items()
    ):

        print()
        print(
            "DRIFT:",
            path,
        )

        print(
            "  expected:",
            change[
                "expected"
            ],
        )

        print(
            "  actual  :",
            change[
                "actual"
            ],
        )

    print()
    print(
        "===== CANONICAL BASELINE CONTRACT ====="
    )

    baseline_expected = provenance[
        "baseline"
    ][
        "sha256"
    ]

    baseline_actual = sha256(
        baseline
    )

    baseline_ok = (
        baseline_actual
        == baseline_expected
    )

    print(
        "Baseline SHA expected:",
        baseline_expected,
    )

    print(
        "Baseline SHA actual  :",
        baseline_actual,
    )

    print(
        "Baseline identity    :",
        "PASS"
        if baseline_ok
        else "FAIL",
    )

    if not baseline_ok:

        print(
            "REGRESSION_GATE: "
            "CANONICAL_BASELINE_MUTATED"
        )

        return 22

    print()
    print(
        "===== EXECUTE FROZEN REPLAY ====="
    )

    with tempfile.TemporaryDirectory(
        prefix="jaguar_regression_"
    ) as temp_directory:

        replay = Path(
            temp_directory
        ) / "verification.csv"

        command = [
            sys.executable,
            str(
                validator
            ),
            "--symbol",
            symbol,
            "--timeframe",
            timeframe,
            "--warmup",
            str(
                warmup
            ),
            "--fixture",
            str(
                fixture
            ),
            "--output",
            str(
                replay
            ),
        ]

        environment = os.environ.copy()

        environment[
            "PYTHONPATH"
        ] = str(
            ROOT
        )

        result = subprocess.run(
            command,
            cwd=ROOT,
            env=environment,
            text=True,
            capture_output=True,
        )

        print(
            "Replay exit code:",
            result.returncode,
        )

        if result.returncode != 0:

            print()
            print(
                "===== REPLAY STDOUT ====="
            )

            print(
                result.stdout
            )

            print()
            print(
                "===== REPLAY STDERR ====="
            )

            print(
                result.stderr
            )

            print(
                "REGRESSION_GATE: "
                "REPLAY_EXECUTION_FAILED"
            )

            return 23

        if not replay.exists():

            print(
                "REGRESSION_GATE: "
                "REPLAY_OUTPUT_MISSING"
            )

            return 24

        replay_sha = sha256(
            replay
        )

        byte_identity = (
            replay_sha
            == baseline_actual
        )

        print(
            "Replay SHA:",
            replay_sha,
        )

        print(
            "Byte identity:",
            "YES"
            if byte_identity
            else "NO",
        )

        print()
        print(
            "===== SEMANTIC AUDIT ====="
        )

        semantic = compare_semantics(
            baseline,
            replay,
        )

        print(
            "Baseline rows       :",
            semantic[
                "baseline_rows"
            ],
        )

        print(
            "Replay rows         :",
            semantic[
                "replay_rows"
            ],
        )

        print(
            "Field contract match:",
            semantic[
                "field_contract_match"
            ],
        )

        print(
            "Changed rows        :",
            len(
                semantic[
                    "changed_indices"
                ]
            ),
        )

        print(
            "Changed indices     :",
            semantic[
                "changed_indices"
            ],
        )

        print(
            "Missing indices     :",
            semantic[
                "missing_indices"
            ],
        )

        print(
            "Field changes       :",
            semantic[
                "field_changes"
            ],
        )

        semantic_identity = semantic[
            "semantic_identity"
        ]

    print()
    print(
        "===== REGRESSION CLASSIFICATION ====="
    )

    implementation_changed = bool(
        implementation_changes
    )

    behaviour_changed = not (
        byte_identity
        and semantic_identity
    )

    if (
        not implementation_changed
        and not behaviour_changed
    ):

        classification = (
            "PASS"
        )

        exit_code = 0

    elif (
        implementation_changed
        and not behaviour_changed
    ):

        classification = (
            "IMPLEMENTATION_CHANGED_"
            "BEHAVIOUR_STABLE"
        )

        exit_code = 0

    elif (
        implementation_changed
        and behaviour_changed
    ):

        classification = (
            "BEHAVIOURAL_DRIFT_"
            "REVIEW_REQUIRED"
        )

        exit_code = 30

    else:

        classification = (
            "NONDETERMINISTIC_OR_"
            "ENVIRONMENTAL_DRIFT"
        )

        exit_code = 31

    print(
        "Implementation changed:",
        implementation_changed,
    )

    print(
        "Behaviour changed     :",
        behaviour_changed,
    )

    print(
        "Classification        :",
        classification,
    )

    print()
    print(
        "REGRESSION_GATE:",
        classification,
    )

    print("=" * 100)

    return exit_code


if __name__ == "__main__":

    sys.exit(
        main()
    )
