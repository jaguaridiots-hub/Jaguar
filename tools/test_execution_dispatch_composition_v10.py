"""Focused D2.8-B3-A execution-dispatch composition tests."""

import os
import importlib


MODE_ENV = "JAGUAR_EXECUTION_MODE"


class FakeLiveRuntime:
    def __init__(self):
        self.submissions = 0

    def submit_live(self, *args, **kwargs):
        self.submissions += 1
        return {"status": "SUBMITTED"}


class FakePaperAdapter:
    constructions = 0

    def __init__(self, mode):
        type(self).constructions += 1
        assert mode == "PAPER"

    def execute(self, execution):
        return {
            "status": "PAPER_EXECUTED",
            "execution": execution,
        }


class FakePaperBrokerForbidden:
    constructions = 0

    def __init__(self, *args, **kwargs):
        type(self).constructions += 1
        raise AssertionError("PaperBrokerAdapter must not be constructed")


def _fresh_module():
    import intelligence.execution_dispatch_composition as module
    return importlib.reload(module)


def main():
    original_mode = os.environ.get(MODE_ENV)

    try:
        import config.config_manager as config_manager
        import intelligence.execution_adapter as adapter_module
        import intelligence.live_execution_composition as live_module

        real_adapter = adapter_module.ExecutionAdapter
        real_live_builder = live_module.build_live_execution_runtime

        # PAPER composition.
        os.environ[MODE_ENV] = "PAPER"
        module = _fresh_module()

        constructed = {"paper": 0, "live": 0}

        class PaperAdapter:
            def __init__(self, mode):
                constructed["paper"] += 1
                assert mode == "PAPER"

            def authorize(self, execution):
                return {"execution": execution}

            def execute(self, execution):
                return {"status": "PAPER_EXECUTED", "execution": execution}

            def rollback(self, execution_result):
                return {
                    "status": "CLOSED",
                    "authorization_id": execution_result.get("authorization_id"),
                    "rolled_back": True,
                }

        def forbidden_live(*, database_module=None):
            constructed["live"] += 1
            raise AssertionError("LIVE runtime must not be built in PAPER mode")

        module.ExecutionAdapter = PaperAdapter
        module.build_live_execution_runtime = forbidden_live

        runtime = module.build_execution_dispatch_runtime()

        assert constructed["paper"] == 1
        assert constructed["live"] == 0
        assert callable(runtime.paper_authorizer)
        assert callable(runtime.paper_rollback)
        result = runtime.dispatch(
            {"mode": "PAPER", "authorization_id": "AUTH-PAPER"},
        )
        assert result["status"] == "PAPER_EXECUTED"
        print("D28B3_PAPER_COMPOSITION: PASS")

        # LIVE composition.
        os.environ[MODE_ENV] = "LIVE"
        module = _fresh_module()

        constructed = {"paper": 0, "live": 0}
        live_runtime = FakeLiveRuntime()

        class ForbiddenPaperAdapter:
            def __init__(self, mode):
                constructed["paper"] += 1
                raise AssertionError(
                    "Paper execution adapter must not be constructed in LIVE mode"
                )

        def live_builder(*, database_module=None):
            constructed["live"] += 1
            return live_runtime

        module.ExecutionAdapter = ForbiddenPaperAdapter
        module.build_live_execution_runtime = live_builder

        runtime = module.build_execution_dispatch_runtime(database_module=object())

        assert constructed["paper"] == 0
        assert constructed["live"] == 1
        assert callable(runtime.paper_authorizer)
        assert callable(runtime.paper_rollback)
        print("D28B3_LIVE_COMPOSITION: PASS")
        print("D28B3_LIVE_HAS_NO_PAPER_BROKER: PASS")

        # LIVE PAPER fallback must fail closed.
        try:
            runtime.dispatch(
                {"mode": "PAPER", "authorization_id": "AUTH-FALLBACK"},
            )
        except Exception as exc:
            assert "PAPER execution unavailable in LIVE mode" in str(exc)
        else:
            raise AssertionError("LIVE composition exposed a PAPER fallback")

        print("D28B3_LIVE_PAPER_FALLBACK_FAIL_CLOSED: PASS")

        for name, callable_ in (
            ("paper_authorizer", runtime.paper_authorizer),
            ("paper_rollback", runtime.paper_rollback),
        ):
            try:
                if name == "paper_authorizer":
                    callable_({"mode": "LIVE"})
                else:
                    callable_({"authorization_id": "AUTH-LIVE"})
            except Exception as exc:
                assert "unavailable in LIVE mode" in str(exc)
            else:
                raise AssertionError(
                    f"LIVE {name} did not fail closed"
                )

        print("D28B3_LIVE_PAPER_CAPABILITIES_FAIL_CLOSED: PASS")

        # LIVE dispatch reaches only the LIVE runtime.
        result = runtime.dispatch(
            {"mode": "LIVE", "authorization_id": "AUTH-LIVE"},
            market_metadata={"live_data_valid": True},
            activation_requested=True,
        )
        assert result["status"] == "SUBMITTED"
        assert live_runtime.submissions == 1
        print("D28B3_LIVE_DISPATCH: PASS")

        # Invalid mode must fail closed.
        os.environ[MODE_ENV] = "INVALID"
        module = _fresh_module()

        try:
            module.build_execution_dispatch_runtime()
        except Exception as exc:
            assert "unable to resolve execution mode" in str(exc) or                    "unsupported execution mode" in str(exc)
        else:
            raise AssertionError("Invalid mode did not fail closed")

        print("D28B3_INVALID_MODE_FAIL_CLOSED: PASS")

    finally:
        # Restore monkeypatched modules for this process.
        try:
            import intelligence.execution_dispatch_composition as module
            module.ExecutionAdapter = real_adapter
            module.build_live_execution_runtime = real_live_builder
        except Exception:
            pass

        if original_mode is None:
            os.environ.pop(MODE_ENV, None)
        else:
            os.environ[MODE_ENV] = original_mode

    print("D28B3_EXECUTION_DISPATCH_COMPOSITION_V10: PASS")


if __name__ == "__main__":
    main()
