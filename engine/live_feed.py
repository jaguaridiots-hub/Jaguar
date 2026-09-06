import threading
import time


class LiveFeed:

    def __init__(
        self,
        state,
        plan=None,
        trade_status=None,
        symbol="btcusdt",
    ):
        self.state = state
        self.plan = plan
        self.trade_status = trade_status or {}
        self.symbol = symbol.upper()
        self.running = False
        self.thread = None

    def dashboard(self):

        # ==================================================
        # CANONICAL ENTERPRISE SNAPSHOTS
        # ==================================================

        institutional = getattr(
            self.state,
            "institutional",
            {},
        )

        if not isinstance(
            institutional,
            dict,
        ):
            institutional = {}

        idm = getattr(
            self.state,
            "idm",
            {},
        )

        if not isinstance(
            idm,
            dict,
        ):
            idm = {}

        execution = getattr(
            self.state,
            "execution",
            {},
        )

        if not isinstance(
            execution,
            dict,
        ):
            execution = {}

        # ==================================================
        # CANONICAL ENTERPRISE METRICS
        # ==================================================

        direction = institutional.get(
            "direction",
            "NEUTRAL",
        )

        score = institutional.get(
            "score",
            0,
        )

        grade = institutional.get(
            "grade",
            "F",
        )

        confidence = institutional.get(
            "confidence",
            0,
        )

        decision = idm.get(
            "decision",
            "WAIT",
        )

        priority = idm.get(
            "priority",
            "LOW",
        )

        approved = idm.get(
            "approved",
            False,
        )

        execution_status = execution.get(
            "status",
            "WAIT",
        )

        ready = execution.get(
            "ready",
            False,
        )

        reason = execution.get(
            "reason",
            "",
        )

        # ==================================================
        # JAGUAR LIVE FEED
        # ==================================================

        print(
            "\n"
            + "=" * 60
        )

        print(
            "                 JAGUAR LIVE FEED"
        )

        print(
            "=" * 60
        )

        print(
            f"Symbol       : {self.symbol}"
        )

        print(
            f"Price        : {getattr(self.state, 'price', 0)}"
        )

        print(
            f"Bias         : {direction}"
        )

        print(
            f"Decision     : {decision}"
        )

        print(
            f"Priority     : {priority}"
        )

        print(
            f"Approved     : {approved}"
        )

        print(
            f"Score        : {score}"
        )

        print(
            f"Grade        : {grade}"
        )

        print(
            f"Confidence   : {confidence}"
        )

        print(
            f"Execution    : {execution_status}"
        )

        print(
            f"Ready        : {ready}"
        )

        if reason:

            print(
                f"Reason       : {reason}"
            )

        print(
            "-" * 60
        )

        # ==================================================
        # TRADE PLAN
        # ==================================================

        if self.plan:

            print(
                "TRADE PLAN"
            )

            keys = [
                "Direction",
                "Entry",
                "StopLoss",
                "TP1",
                "TP2",
                "TP3",
                "RiskReward",
            ]

            for key in keys:

                if key in self.plan:

                    print(
                        f"{key:12}: "
                        f"{self.plan[key]}"
                    )

        else:

            print(
                "NO TRADE PLAN"
            )

        print(
            "-" * 60
        )

        # ==================================================
        # TRADE STATUS
        # ==================================================

        print(
            "TRADE STATUS"
        )

        if self.trade_status:

            for key, value in self.trade_status.items():

                print(
                    f"{key:12}: {value}"
                )

        else:

            print(
                "No Active Trade"
            )

        print(
            "=" * 60
        )

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
            daemon=False,
        )

        self.thread.start()

    def stop(self):

        self.running = False

        if self.thread is not None:

            self.thread.join(
                timeout=2
            )

            self.thread = None
