# research/persistence_audit.py
import json
import sqlite3
import os
from .database import DB_PATH

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_latest_run_id():
    conn = get_connection()
    row = conn.execute(
        "SELECT run_id FROM research_runs WHERE end_time IS NOT NULL ORDER BY start_time DESC LIMIT 1"
    ).fetchone()
    conn.close()
    return row["run_id"] if row else None

def compare_and_report(run_id=None, log_file_path=None):
    """Read the runtime audit log and compare with stored database values."""

    print(f"\n{'='*70}")
    print(f"  PERSISTENCE AUDIT")
    print(f"{'='*70}")
    print(f"  Database: {os.path.abspath(DB_PATH)}")

    # Resolve run_id
    if not run_id:
        run_id = get_latest_run_id()
        if not run_id:
            print("❌ No run_id provided and no completed campaigns found.")
            return
        print(f"  Auto-selected latest Run ID: {run_id}")
    else:
        print(f"  Run ID: {run_id}")

    # Verify database contains the score_log table
    conn = get_connection()
    table_check = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='score_log'"
    ).fetchone()
    if not table_check:
        print("❌ Database does not contain score_log table.")
        conn.close()
        return
    conn.close()

    # Load runtime log entries if a path was provided
    runtime_entries = []
    if log_file_path:
        try:
            with open(log_file_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        runtime_entries.append(entry)
                    except json.JSONDecodeError:
                        print(f"  ⚠️  Skipping malformed log line: {line[:50]}...")
        except FileNotFoundError:
            print(f"❌ Audit log file not found: {log_file_path}")
            return
        if not runtime_entries:
            print("No runtime entries found in log file.")
            return

    runtime_map = {e["decision_id"]: e for e in runtime_entries}

    # Fetch stored decisions for this run
    conn = get_connection()
    rows = conn.execute(
        "SELECT decision_id, brain_score, composite_score, contributions_json "
        "FROM score_log WHERE run_id = ?",
        (run_id,)
    ).fetchall()
    conn.close()

    stored_map = {}
    for r in rows:
        stored_map[r["decision_id"]] = {
            "brain_score": r["brain_score"],
            "composite_score": r["composite_score"],
            "contributions": json.loads(r["contributions_json"]) if r["contributions_json"] else []
        }

    print(f"  Runtime decisions: {len(runtime_map)}")
    print(f"  Database decisions: {len(stored_map)}")

    if runtime_entries:
        # Check for missing decisions in either direction
        missing_in_db = set(runtime_map.keys()) - set(stored_map.keys())
        if missing_in_db:
            print(f"  ⚠️  {len(missing_in_db)} decisions in log but missing from database (sample):")
            for did in list(missing_in_db)[:5]:
                print(f"    - {did}")

        missing_in_log = set(stored_map.keys()) - set(runtime_map.keys())
        if missing_in_log:
            print(f"  ⚠️  {len(missing_in_log)} decisions in database but not in log (sample):")
            for did in list(missing_in_log)[:5]:
                print(f"    - {did}")

        # Compare common decisions
        common = set(runtime_map.keys()) & set(stored_map.keys())
        print(f"\n  Comparing {len(common)} common decisions...")

        brain_mismatches = 0
        composite_mismatches = 0
        contrib_mismatches = 0
        tolerance = 1e-9

        for did in sorted(common)[:1000]:  # limit for performance
            rt = runtime_map[did]
            st = stored_map[did]

            if rt["brain_score"] is not None and st["brain_score"] is not None:
                if abs(rt["brain_score"] - st["brain_score"]) > tolerance:
                    brain_mismatches += 1
                    if brain_mismatches <= 5:
                        print(f"    Brain Score mismatch: {did}  runtime={rt['brain_score']}  stored={st['brain_score']}")

            if rt["composite_score"] is not None and st["composite_score"] is not None:
                if abs(rt["composite_score"] - st["composite_score"]) > tolerance:
                    composite_mismatches += 1
                    if composite_mismatches <= 5:
                        print(f"    Composite Score mismatch: {did}  runtime={rt['composite_score']}  stored={st['composite_score']}")

            rt_contribs = rt.get("contributions", [])
            st_contribs = st.get("contributions", [])
            if len(rt_contribs) != len(st_contribs):
                contrib_mismatches += 1
            else:
                for r_eng, s_eng in zip(rt_contribs, st_contribs):
                    if r_eng.get("contribution", 0) != s_eng.get("contribution", 0):
                        contrib_mismatches += 1
                        break

        print(f"  Brain Score mismatches: {brain_mismatches}")
        print(f"  Composite Score mismatches: {composite_mismatches}")
        print(f"  Engine contribution mismatches: {contrib_mismatches}")

        if brain_mismatches == 0 and composite_mismatches == 0 and contrib_mismatches == 0:
            print("\n  ✅ All runtime values match stored values.")
        else:
            print("\n  ❌ Mismatches found – investigate the recorder or database writes.")
    else:
        print("  No runtime log provided; only database count verified.")

    print("=" * 70)
