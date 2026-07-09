def print_report(state):

    brain = state.brain

    print()
    print("=" * 60)
    print("               JAGUAR QUANT X")
    print("=" * 60)

    print("Signal      :", brain["signal"])
    print("Grade       :", brain["grade"])
    print("Confidence  :", brain["confidence"], "%")
    print("Score       :", brain["score"])

    print("\nMarket Structure")

    print(state.structure)

    print("\nLiquidity")

    print(state.liquidity)

    print("\nFair Value Gap")
    print(state.fvg)

    print()
    print("Premium / Discount")
    print(state.premium_discount)

    print()
    print("Wyckoff")
    print(state.wyckoff)

    print()
    print("Market Structure Shift")
    print(state.mss)

    print()
    print("Equal High / Equal Low")
    print(state.equal_levels)

    print("\nReasons")

    for r in brain["reasons"]:
        print("✓", r)

    print("=" * 60)
