import threading
import time


class LiveFeed:

    def __init__(self, state, plan=None, trade_status=None, symbol="btcusdt"):
        self.state = state
        self.plan = plan
        self.trade_status = trade_status or {}
        self.symbol = symbol.upper()
        self.running = False
        self.thread = None

    def dashboard(self):
        print("\n" + "=" * 60)
        print("                 JAGUAR LIVE FEED")
        print("=" * 60)

        print(f"Symbol      : {self.symbol}")
        print(f"Price       : {self.state.price}")
        print(f"Decision    : {self.state.decision}")
        print(f"Confidence  : {self.state.confidence}")
        print(f"Probability : {self.state.probability}%")
        print(f"AI Score    : {self.state.ai_score}")

        print("-" * 60)

        if self.plan:
            print("TRADE PLAN")

            keys = [
                "Direction",
                "Entry",
                "StopLoss",
                "TP1",
                "TP2",
                "TP3",
                "RiskReward"
            ]

            for key in keys:
                if key in self.plan:
                    print(f"{key:12}: {self.plan[key]}")

        else:
            print("NO TRADE PLAN")

        print("-" * 60)

        print("TRADE STATUS")

        if self.trade_status:
            for k, v in self.trade_status.items():
                print(f"{k:12}: {v}")
        else:
            print("No Active Trade")

        print("=" * 60)

    def loop(self):
        while self.running:
            self.dashboard()
            time.sleep(5)

    def start(self):
        if self.running:
            return

        self.running = True

        self.thread = threading.Thread(
            target=self.loop,
            daemon=False
        )

        self.thread.start()

    def stop(self):
        self.running = False

        if self.thread is not None:
            self.thread.join(timeout=2)
