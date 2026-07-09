def print_report(state):

    brain = getattr(state, "brain", {}) or {}

    print()
    print("=" * 60)
    print("                JAGUAR QUANT X")
    print("=" * 60)

    print("Signal      :", brain.get("signal"))
    print("Grade       :", brain.get("grade"))
    print("Confidence  :", brain.get("confidence"))
    print("Score       :", brain.get("score"))

    print("\nMarket Structure")
    print(getattr(state, "structure", {}))

    print("\nLiquidity")
    print(getattr(state, "liquidity", {}))

    print("\nFair Value Gap")
    print(getattr(state, "fvg", {}))

    print("\nPremium / Discount")
    print(getattr(state, "premium_discount", {}))

    print("\nWyckoff")
    print(getattr(state, "wyckoff", {}))

    print("\nMarket Structure Shift")
    print(getattr(state, "mss", {}))

    print("\nEqual High / Equal Low")
    print(getattr(state, "equal_levels", {}))

    print("\nVolume Profile")
    print(getattr(state, "volume_profile", {}))

    print("\nSession")
    print(getattr(state, "session", {}))

    print("\nGANN")
    print(getattr(state, "gann", {}))

    print()

    print("Regime")
    print(getattr(state, "regime", {}))

    print()
    print("=" * 60)
    print("TIMEFRAME CONFLUENCE")
    print("=" * 60)
    print(getattr(state, "mtf", {}))

    print()
    print("=" * 60)
    print("TRADE PLANNER")
    print("=" * 60)
    print(getattr(state, "trade_plan", {}))

    print()
    print("=" * 60)
    print("RISK MANAGER")
    print("=" * 60)
    print(getattr(state, "risk", {}))

    print("\nReasons")
    for r in brain.get("reasons", []):
        print("✓", r)

    print()
    print("=" * 60)
    print("ENTERPRISE DASHBOARD")
    print("=" * 60)

    if hasattr(state, "dashboard") and state.dashboard:

        d = state.dashboard

        print("Symbol          :", d.get("symbol"))
        print("Timeframe       :", d.get("interval"))

        print()

        print("AI Signal       :", d.get("signal"))
        print("Score           :", d.get("score"))
        print("Probability     :", d.get("probability"))
        print("Confidence      :", d.get("confidence"))
        print("Grade           :", d.get("institution_grade"))
        print("Quality         :", d.get("trade_quality"))

        print()

        print("Entry           :", d.get("entry"))
        print("Stop Loss       :", d.get("stop"))
        print("Take Profit 1   :", d.get("tp1"))
        print("Take Profit 2   :", d.get("tp2"))

        print()

        print("Risk Status     :", d.get("risk_status"))
        print("Position Size   :", d.get("position_size"))
        print("Exposure        :", d.get("exposure"))

        print()

        print("Session         :", d.get("session"))
        print("MTF Bias        :", d.get("mtf_bias"))

        print("Market Regime   :", d.get("market_regime"))
        print("Regime Score    :", d.get("regime_score"))

        print()

        print("Decision        :", d.get("decision"))
        print("Decision Score  :", d.get("decision_score"))

        print()

        print("Execution       :", d.get("execution_signal"))
        print("Execution Score :", d.get("execution_score"))

        print()

        print("Order Flow      :", d.get("orderflow_signal"))
        print("Delta           :", d.get("orderflow_delta"))

        print()

        print("POC             :", d.get("poc"))
        print("VAH             :", d.get("vah"))
        print("VAL             :", d.get("val"))

        print()

        print("Gann Support    :", d.get("gann_support"))
        print("Gann Resistance :", d.get("gann_resistance"))
        print("Nearest Level   :", d.get("gann_level"))

    print("=" * 60)
