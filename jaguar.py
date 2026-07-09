from core.orchestrator import JaguarOrchestrator


def main():

    app = JaguarOrchestrator()

    state = app.analyze("BTCUSDT", "15m")

    print("\n========== JAGUAR ==========")

    from report.console_report import print_report

    print_report(state)

    print("\nEvents:")

    for e in app.events():

        print(e)


if __name__ == "__main__":

    main()
