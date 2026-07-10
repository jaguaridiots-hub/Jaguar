from datetime import datetime


class MissionControl:

    @staticmethod
    def show(state):

        print("\n")
        print("=" * 70)
        print("             JAGUAR QUANT X - MISSION CONTROL")
        print("=" * 70)

        print(f"Time       : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Symbol     : {getattr(state, 'symbol', '-')}")
        print(f"Interval   : {getattr(state, 'interval', '-')}")
        print(f"Grade      : {getattr(state, 'grade', '-')}")
        print(f"Signal     : {getattr(state, 'signal', '-')}")
        print(f"Confidence : {getattr(state, 'confidence', 0)}")

        print("\nENGINE STATUS")
        print("-" * 70)

        if state.engine_status:
            for name, status in state.engine_status.items():

                t = state.engine_time.get(name, 0)

                print(
                    f"{name:<35}"
                    f"{status:<10}"
                    f"{t:.4f}s"
                )
        else:
            print("No engine data.")

        print("-" * 70)

        if state.error:
            print("\nLAST ERROR")
            print(state.error)

        print("=" * 70)
