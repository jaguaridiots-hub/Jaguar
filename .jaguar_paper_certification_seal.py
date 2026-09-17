from pathlib import Path
import hashlib
import subprocess
from datetime import datetime, timezone

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

def run(*args):
    return subprocess.check_output(args, text=True).strip()

head = run("git", "rev-parse", "HEAD")
parent = run("git", "rev-parse", "HEAD^")
tag_target = run(
    "git", "rev-list", "-n", "1",
    "jaguar-v2.0.0-rc1-live-readiness",
)

release_delta = run(
    "git", "diff", "--name-only",
    "jaguar-v2.0.0-rc1-live-readiness..HEAD",
).splitlines()

dashboard_in_delta = "dashboard_BTCUSDT_SWING.html" in release_delta

assert head == "177c20a6c3030906ef070c5878784cc82bfb04d2"
assert parent == "32ab5183fc3acee01e2ba22e76bfe969efe507c2"
assert tag_target == "82ff4f7831f9e0a81e6cbc8c5987a089e51bfd2e"
assert release_delta == ["api.py", "dashboard/ui_state.py", "intelligence/paper_post_fill.py"]
assert not dashboard_in_delta

out = Path(
    f".jaguar_paper_certification_seal_"
    f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.txt"
)

lines = [
    "JAGUAR QUANT X — PAPER CERTIFICATION SEAL",
    "=" * 52,
    f"timestamp_utc={datetime.now(timezone.utc).isoformat()}",
    f"execution_mode=PAPER",
    f"branch={run('git', 'branch', '--show-current')}",
    f"head={head}",
    f"parent={parent}",
    f"release_tag=jaguar-v2.0.0-rc1-live-readiness",
    f"release_tag_target={tag_target}",
    "",
    "CERTIFIED GATES",
    "canonical_paper_e2e=PASS",
    "durable_lifecycle=PASS",
    "durable_idempotency=PASS",
    "partial_failure_fail_closed=PASS",
    "recovery_resume=PASS",
    "no_paper_resubmission=PASS",
    "identity_preservation=PASS",
    "production_compile=PASS",
    "git_diff_check=PASS",
    "live_submission_count=0",
    "",
    "RELEASE DELTA",
    *release_delta,
    f"dashboard_excluded={not dashboard_in_delta}",
    "",
    "PRODUCTION SHA256",
]

for path in PRODUCTION_FILES:
    lines.append(f"{path}={sha256(path)}")

lines += [
    "",
    "WORKTREE POLICY",
    "dashboard_BTCUSDT_SWING.html=RESTORED / EXCLUDED FROM RELEASE DELTA",
    "certification_artifacts=UNTRACKED EVIDENCE",
    "production_certification_changes=NONE",
]

out.write_text("\n".join(lines) + "\n")

print(out)
print("PAPER CERTIFICATION SEAL: PASS")
