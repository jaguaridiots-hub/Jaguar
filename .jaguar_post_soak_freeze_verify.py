import hashlib
from pathlib import Path
import subprocess
import sys

SEAL = Path(".jaguar_paper_certification_seal_20260917_160343.txt")

PRODUCTION_FILES = [
    "main.py",
    "intelligence/paper_post_fill.py",
    "research/database.py",
    "intelligence/paper_broker_adapter.py",
    "intelligence/execution_adapter.py",
    "intelligence/execution_dispatch_composition.py",
    "intelligence/live_execution_dispatch.py",
    "intelligence/execution_identity.py",
]

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

if not SEAL.exists():
    raise SystemExit(f"ABORT: seal not found: {SEAL}")

seal = SEAL.read_text().splitlines()

sealed = {}
inside_hashes = False

for line in seal:
    if line == "PRODUCTION SHA256":
        inside_hashes = True
        continue
    if inside_hashes and "=" in line:
        path, value = line.split("=", 1)
        if path in PRODUCTION_FILES:
            sealed[path] = value.strip()

missing = [p for p in PRODUCTION_FILES if p not in sealed]
if missing:
    raise SystemExit(
        "ABORT: missing sealed hashes:\n" + "\n".join(missing)
    )

print("=== POST-SOAK FREEZE VERIFICATION ===")

for path in PRODUCTION_FILES:
    actual = sha256(path)
    expected = sealed[path]

    if actual != expected:
        raise SystemExit(
            f"FAIL: {path}\n"
            f"sealed ={expected}\n"
            f"actual ={actual}"
        )

    print(f"{path}: UNCHANGED")

head = subprocess.check_output(
    ["git", "rev-parse", "HEAD"], text=True
).strip()

expected_head = "177c20a6c3030906ef070c5878784cc82bfb04d2"

if head != expected_head:
    raise SystemExit(
        f"FAIL: HEAD changed\nexpected={expected_head}\nactual={head}"
    )

delta = subprocess.check_output(
    [
        "git", "diff", "--name-only",
        "jaguar-v2.0.0-rc1-live-readiness..HEAD",
    ],
    text=True,
).splitlines()

expected_delta = [
    "api.py",
    "dashboard/ui_state.py",
    "intelligence/paper_post_fill.py",
]

if delta != expected_delta:
    raise SystemExit(
        "FAIL: release delta changed:\n" + "\n".join(delta)
    )

print(f"HEAD: {head}")
print("RELEASE DELTA: " + ", ".join(delta))
print("DASHBOARD RELEASE EXCLUSION: PASS")
print("POST-SOAK FREEZE: PASS")
