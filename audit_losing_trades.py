# audit_losing_trades.py
import sqlite3
import json
from datetime import datetime

DB_PATH = "research.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def fetch_losing_trades():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT 
            t.uuid,
            t.symbol,
            t.timeframe,
            t.mode,
            t.open_time,
            t.close_time,
            t.entry_price,
            t.exit_price,
            t.pnl,
            t.r_multiple,
            t.win_loss,
            t.snapshot_open,
            t.decision,
            t.composite_score,
            t.brain_score,
            t.probability_score,
            t.confidence
        FROM trades t
        WHERE t.status = 'CLOSED' AND t.win_loss = 0
        ORDER BY t.close_time ASC
    ''')
    rows = cur.fetchall()
    conn.close()
    
    trades = []
    for row in rows:
        # Parse snapshot
        snapshot = json.loads(row[11]) if row[11] else {}
        brain = snapshot.get('brain', {})
        master = snapshot.get('master_decision', {})
        validator = snapshot.get('validator', {})
        regime = snapshot.get('regime', {})
        session = snapshot.get('session', {})
        market = snapshot.get('market', {})
        explain = snapshot.get('brain_explain', {})
        
        # Extract engine contributions
        contributions = explain.get('contributions', [])
        smc_signal = next((c.get('raw_desc') for c in contributions if c.get('label') == 'SMC'), 'UNKNOWN')
        structure_score = next((c.get('base') for c in contributions if c.get('label') == 'Structure'), 0)
        orderflow_score = next((c.get('base') for c in contributions if c.get('label') == 'Order Flow'), 0)
        session_score = next((c.get('base') for c in contributions if c.get('label') == 'Session'), 0)
        regime_score = next((c.get('base') for c in contributions if c.get('label') == 'Regime'), 0)
        
        trade = {
            'uuid': row[0],
            'symbol': row[1],
            'timeframe': row[2],
            'mode': row[3],
            'open_time': row[4],
            'close_time': row[5],
            'entry': row[6],
            'exit': row[7],
            'pnl': row[8],
            'r_multiple': row[9],
            'win_loss': row[10],
            'decision': row[12],
            'master_score': row[13],
            'brain_score': row[14],
            'probability_score': row[15],
            'confidence': row[16],
            'validator_approved': validator.get('approved', False),
            'validator_score': validator.get('validation_score', 0),
            'regime': regime.get('regime', 'UNKNOWN'),
            'session': session.get('session', 'UNKNOWN'),
            'smc_signal': smc_signal,
            'structure_score': structure_score,
            'orderflow_score': orderflow_score,
            'session_score': session_score,
            'regime_score': regime_score,
            'price': market.get('price', 0),
            'volume': market.get('volume', 0),
        }
        trades.append(trade)
    
    return trades

def classify_loss_reason(trade):
    """Classify the primary reason for a losing trade."""
    reasons = []
    
    # Check for trend issues
    if trade['regime'] == 'COMPRESSION':
        reasons.append('COMPRESSION_TRADE')
    
    # Check volume
    if trade['volume'] == 0:
        reasons.append('ZERO_VOLUME')
    
    # Check SMC
    if trade['smc_signal'] == 'NEUTRAL':
        reasons.append('SMC_NEUTRAL')
    
    # Check structure
    if trade['structure_score'] == 0:
        reasons.append('NO_STRUCTURE')
    
    # Check order flow
    if trade['orderflow_score'] == 0:
        reasons.append('WEAK_ORDERFLOW')
    
    # Check validator
    if not trade['validator_approved']:
        reasons.append('VALIDATOR_REJECTED')
    
    # Check confidence
    if trade['confidence'] < 50:
        reasons.append('LOW_CONFIDENCE')
    
    # Check Brain score
    if trade['brain_score'] < 20:
        reasons.append('WEAK_BRAIN')
    
    # Check composite score
    if trade['master_score'] < 70:
        reasons.append('LOW_COMPOSITE')
    
    # If no specific reason, classify as generic
    if not reasons:
        reasons.append('GENERIC_LOSS')
    
    return reasons

def generate_audit_report():
    trades = fetch_losing_trades()
    total_losses = len(trades)
    
    if total_losses == 0:
        print("✅ No losing trades found.")
        return
    
    print("="*80)
    print("JAGUAR QUANT X – LOSING TRADE ATTRIBUTION AUDIT")
    print("="*80)
    print(f"Total Losing Trades: {total_losses}")
    print("="*80)
    
    # Detailed breakdown
    reason_counts = {}
    symbol_counts = {}
    mode_counts = {}
    regime_counts = {}
    
    for i, trade in enumerate(trades, 1):
        print(f"\n📉 Trade #{i} | {trade['symbol']} | {trade['mode']}")
        print(f"   Entry: {trade['open_time']}  Exit: {trade['close_time']}")
        print(f"   Entry Price: {trade['entry']:.2f}  Exit Price: {trade['exit']:.2f}")
        print(f"   PnL: {trade['pnl']:.2f}  R-Multiple: {trade['r_multiple']:.2f}")
        print(f"   Brain Score: {trade['brain_score']:.2f}  Master Score: {trade['master_score']}")
        print(f"   Validator Approved: {trade['validator_approved']} (Score: {trade['validator_score']})")
        print(f"   Regime: {trade['regime']}  Session: {trade['session']}")
        print(f"   SMC Signal: {trade['smc_signal']}  Structure: {trade['structure_score']}")
        print(f"   Order Flow: {trade['orderflow_score']}  Session Score: {trade['session_score']}")
        
        reasons = classify_loss_reason(trade)
        print(f"   Loss Reasons: {', '.join(reasons)}")
        
        # Aggregate statistics
        symbol_counts[trade['symbol']] = symbol_counts.get(trade['symbol'], 0) + 1
        mode_counts[trade['mode']] = mode_counts.get(trade['mode'], 0) + 1
        regime_counts[trade['regime']] = regime_counts.get(trade['regime'], 0) + 1
        for r in reasons:
            reason_counts[r] = reason_counts.get(r, 0) + 1
    
    # Summary statistics
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    
    print("\n📊 Losses by Symbol:")
    for symbol, count in sorted(symbol_counts.items(), key=lambda x: -x[1]):
        print(f"   {symbol}: {count} ({count/total_losses*100:.1f}%)")
    
    print("\n📊 Losses by Mode:")
    for mode, count in sorted(mode_counts.items(), key=lambda x: -x[1]):
        print(f"   {mode}: {count} ({count/total_losses*100:.1f}%)")
    
    print("\n📊 Losses by Regime:")
    for regime, count in sorted(regime_counts.items(), key=lambda x: -x[1]):
        print(f"   {regime}: {count} ({count/total_losses*100:.1f}%)")
    
    print("\n📊 Loss Reasons Frequency:")
    for reason, count in sorted(reason_counts.items(), key=lambda x: -x[1]):
        print(f"   {reason}: {count} ({count/total_losses*100:.1f}%)")
    
    # Engine contribution analysis
    print("\n📊 Average Scores on Losing Trades:")
    avg_brain = sum(t['brain_score'] for t in trades) / total_losses
    avg_master = sum(t['master_score'] for t in trades) / total_losses
    avg_validator = sum(t['validator_score'] for t in trades) / total_losses
    avg_confidence = sum(t['confidence'] for t in trades) / total_losses
    print(f"   Average Brain Score: {avg_brain:.2f}")
    print(f"   Average Master Score: {avg_master:.2f}")
    print(f"   Average Validator Score: {avg_validator:.2f}")
    print(f"   Average Confidence: {avg_confidence:.2f}")
    
    print("\n" + "="*80)
    print("✅ AUDIT COMPLETE")
    print("="*80)

if __name__ == "__main__":
    generate_audit_report()
