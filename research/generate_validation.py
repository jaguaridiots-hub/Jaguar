# research/generate_validation.py
import os
from .database import DB_PATH, get_connection
from .suite import run_research_campaign

REQUIRED_CAMPAIGNS = [
    ("GC=F", "SWING"),
    ("BTC-USD", "SCALP"),
    ("BTC-USD", "SWING"),
]

MIN_CLOSED_TRADES = 500

def campaign_ready(symbol, mode):
    """Return True if the latest completed campaign has enough closed trades."""
    conn = get_connection()
    row = conn.execute(
        "SELECT executed_trades FROM research_runs WHERE symbols=? AND modes=? AND end_time IS NOT NULL ORDER BY start_time DESC LIMIT 1",
        (symbol, mode)
    ).fetchone()
    conn.close()
    if row and row["executed_trades"] >= MIN_CLOSED_TRADES:
        return True
    return False

def generate_validation_campaigns():
    print("=" * 70)
    print("  VALIDATION CAMPAIGN GENERATOR")
    print("=" * 70)

    missing = []
    for sym, md in REQUIRED_CAMPAIGNS:
        ready = campaign_ready(sym, md)
        status = "READY" if ready else "MISSING"
        print(f"  {sym:10s} {md:6s} : {status}")
        if not ready:
            missing.append((sym, md))

    if not missing:
        print("\n  ✅ All validation campaigns are ready.")
        print("  Run: python3 jaguar.py --staged-brain-v3")
        print("=" * 70)
        return

    print(f"\n  Generating {len(missing)} missing campaign(s)...\n")
    for sym, md in missing:
        print(f"  Starting {sym} {md} ...")
        try:
            run_research_campaign(symbol=sym, mode=md)
        except Exception as e:
            print(f"  ⚠️  Campaign failed: {e}")
            continue
        # After campaign, check readiness again
        if campaign_ready(sym, md):
            print(f"  ✅ {sym} {md} now ready.")
        else:
            print(f"  ⚠️  {sym} {md} completed but may have insufficient trades (need {MIN_CLOSED_TRADES}).")

    print("\n  Generation complete.")
    print("  Run: python3 jaguar.py --staged-brain-v3")
    print("=" * 70)
