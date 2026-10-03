# report/console_report.py
from pprint import pprint

def print_report(state):
    d = getattr(state, "dashboard", {}) or {}

    print()
    print("=" * 60)
    print("                    JAGUAR QUANT X")
    print("=" * 60)

    print("\n1. MARKET SUMMARY")
    print("-" * 60)
    print(f"Symbol          : {d.get('symbol', 'N/A')}")
    print(f"Timeframe       : {d.get('timeframe', 'N/A')}")
    print(f"Price           : {d.get('price', 0):.2f}")
    print(f"Session         : {d.get('session', 'UNKNOWN')}")
    print(f"Market Regime   : {d.get('market_regime', 'UNKNOWN')}")

    print("\n2. AI ANALYSIS")
    print("-" * 60)
    print(f"Brain Signal    : {d.get('brain_signal', 'NONE')}")
    print(f"Brain Score     : {d.get('brain_score', 0)}")
    print(f"Probability     : {d.get('probability', 0)}")
    print(f"Probability Conf: {d.get('probability_confidence', 'LOW')}")

    print("\n3. INSTITUTIONAL DECISION")
    print("-" * 60)
    print(f"Decision        : {d.get('decision', 'WAIT')}")
    print(f"Score           : {d.get('decision_score', 0)}")
    print(f"Grade           : {d.get('decision_grade', 'F')}")
    print(f"Confidence      : {d.get('decision_confidence', 0)}%")
    print(f"Trade Approved  : {d.get('trade_approved', False)}")
    reasons = d.get('decision_reasons', [])
    if reasons:
        print("Reasons         :")
        for r in reasons:
            print(f"  ✓ {r}")
    else:
        print("Reasons         : None")

    print("\n4. TRADE PLAN")
    print("-" * 60)
    print(f"Entry           : {d.get('entry', 'N/A')}")
    print(f"Stop            : {d.get('stop', 'N/A')}")
    print(f"TP1             : {d.get('tp1', 'N/A')}")
    print(f"TP2             : {d.get('tp2', 'N/A')}")
    print(f"Risk Reward     : {d.get('risk_reward', 0)}")

    print("\n5. RISK")
    print("-" * 60)
    print(f"Risk Status     : {d.get('risk_status', 'NO TRADE')}")
    print(f"Position Size   : {d.get('position_size', 0):.4f}")
    print(f"Exposure        : {d.get('exposure', 0):.2f}")

    print("\n6. EXECUTION PIPELINE")
    print("-" * 60)
    print(f"Trigger         : {d.get('execution_trigger', False)}")
    print(f"Confirmation    : {d.get('execution_confirmation', False)}")
    print(f"Status          : {d.get('execution_status', 'IDLE')}")
    print(f"Reason          : {d.get('execution_reason', '')}")

    print("\n7. VALIDATION")
    print("-" * 60)
    print(f"Approved        : {d.get('validator_approved', False)}")
    print(f"Score           : {d.get('validator_score', 0)}")
    blockers = d.get('validator_blockers', [])
    if blockers:
        print("Blockers        :")
        for b in blockers:
            print(f"  ✓ {b}")
    else:
        print("Blockers        : None")

    print("\n8. MARKET DIAGNOSTICS")
    print("-" * 60)
    print("MTF             :", pprint(d.get('mtf', {})))
    print("Order Flow      :", pprint(d.get('orderflow', {})))
    print("Volume Profile  :", pprint(d.get('volume_profile', {})))
    print("Gann            :", pprint(d.get('gann', {})))
    print("SMC             :", pprint(d.get('smc', {})))
    print("Structure       :", pprint(d.get('structure', {})))
    print("Liquidity       :", pprint(d.get('liquidity', {})))
    print("FVG             :", pprint(d.get('fvg', {})))
    print("Premium Discount:", pprint(d.get('premium_discount', {})))
    print("Wyckoff         :", pprint(d.get('wyckoff', {})))
    print("Equal High/Low  :", pprint(d.get('equal_levels', {})))

    print("=" * 60)
