# research/replay_sample_verification.py
import json
import os
import tempfile

def verify_trace(symbol="GC=F", mode="SCALP"):
    log_path = os.path.join(tempfile.gettempdir(), f"trace_{symbol}_{mode}.jsonl")
    if not os.path.exists(log_path):
        print(f"No trace log found at {log_path}. Run --replay-trace first.")
        return

    samples = []
    with open(log_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                samples.append(json.loads(line))

    before = [s for s in samples if s['type'] == 'before']
    after = [s for s in samples if s['type'] == 'after']

    print(f"  Log entries: {len(samples)} total ({len(before)} before, {len(after)} after)")

    if not before:
        print("No before samples found.")
        return

    # Extract fields from before and after, aligning by index
    indices = sorted(set(s['index'] for s in before))
    timestamps = sorted(set(s['replay_time'] for s in before))
    prices = [s['price'] for s in before]

    # For RSI/EMA/Brain, we need to look at after samples that correspond to these indices.
    # We'll build a map index -> after
    after_map = {s['index']: s for s in after}

    rsi_vals = []
    ema20_vals = []
    ema50_vals = []
    brain_vals = []

    print("\n  Sampled points:")
    print(f"  {'Index':<8s} {'Timestamp':<25s} {'Close':<10s} {'RSI':<8s} {'EMA20':<10s} {'EMA50':<10s} {'Brain Score':<12s}")
    print(f"  {'-'*8} {'-'*25} {'-'*10} {'-'*8} {'-'*10} {'-'*10} {'-'*12}")

    for b in before:
        idx = b['index']
        ts = b['replay_time']
        close = b['price']
        # Find corresponding after sample
        a = after_map.get(idx, {})
        rsi = a.get('engine_outputs', {}).get('indicators', {}).get('rsi', None) if a.get('engine_outputs') else None
        ema20 = a.get('engine_outputs', {}).get('indicators', {}).get('ema20', None) if a.get('engine_outputs') else None
        ema50 = a.get('engine_outputs', {}).get('indicators', {}).get('ema50', None) if a.get('engine_outputs') else None
        brain = a.get('brain_score', None)

        if rsi is None:
            # try to get from top-level? The after sample has no indicators because we didn't capture them.
            # We'll leave as N/A
            rsi_str = "N/A"
        else:
            rsi_str = f"{rsi:.2f}" if isinstance(rsi, (int, float)) else str(rsi)
            rsi_vals.append(rsi)
        if ema20 is not None:
            ema20_vals.append(ema20)
        if ema50 is not None:
            ema50_vals.append(ema50)
        if brain is not None:
            brain_vals.append(brain)

        print(f"  {idx:<8d} {str(ts):<25s} {close:<10.2f} {rsi_str:<8s} {str(ema20) if ema20 else 'N/A':<10s} {str(ema50) if ema50 else 'N/A':<10s} {str(brain) if brain is not None else 'N/A':<12s}")

    print("\n  Verification Summary:")
    print(f"  Unique replay indices : {len(indices)}")
    print(f"  Unique timestamps     : {len(timestamps)}")
    print(f"  Unique prices         : {len(set(prices))}")
    print(f"  Unique RSI values     : {len(set(rsi_vals))}")
    print(f"  Unique EMA20 values   : {len(set(ema20_vals))}")
    print(f"  Unique Brain Scores   : {len(set(brain_vals))}")
