"""D2.8-A execution-mode configuration contract tests."""

import os

from config.config_manager import ConfigurationManager


ENV_NAME = "JAGUAR_EXECUTION_MODE"


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def clear_mode():
    os.environ.pop(ENV_NAME, None)


def test_unset_defaults_to_paper():
    clear_mode()

    mode = ConfigurationManager().get_execution_mode()

    assert_true(
        mode == "PAPER",
        f"Unset execution mode did not default to PAPER: {mode!r}",
    )

    print("D28_UNSET_DEFAULT_PAPER: PASS")


def test_blank_defaults_to_paper():
    os.environ[ENV_NAME] = "   "

    try:
        mode = ConfigurationManager().get_execution_mode()

        assert_true(
            mode == "PAPER",
            f"Blank execution mode did not default to PAPER: {mode!r}",
        )
    finally:
        clear_mode()

    print("D28_BLANK_DEFAULT_PAPER: PASS")


def test_paper_is_accepted():
    os.environ[ENV_NAME] = "PAPER"

    try:
        mode = ConfigurationManager().get_execution_mode()

        assert_true(
            mode == "PAPER",
            f"PAPER was not accepted: {mode!r}",
        )
    finally:
        clear_mode()

    print("D28_PAPER_ACCEPTED: PASS")


def test_live_is_accepted():
    os.environ[ENV_NAME] = "LIVE"

    try:
        mode = ConfigurationManager().get_execution_mode()

        assert_true(
            mode == "LIVE",
            f"LIVE was not accepted: {mode!r}",
        )
    finally:
        clear_mode()

    print("D28_LIVE_ACCEPTED: PASS")


def test_mode_is_case_and_whitespace_normalized():
    os.environ[ENV_NAME] = "  live  "

    try:
        mode = ConfigurationManager().get_execution_mode()

        assert_true(
            mode == "LIVE",
            f"Explicit mode normalization failed: {mode!r}",
        )
    finally:
        clear_mode()

    print("D28_NORMALIZATION: PASS")


def test_invalid_mode_fails_closed():
    os.environ[ENV_NAME] = "LIVE_NOW"

    try:
        try:
            ConfigurationManager().get_execution_mode()
        except RuntimeError as exc:
            assert_true(
                str(exc).startswith(
                    "FAIL-CLOSED: invalid execution mode:"
                ),
                "Invalid mode raised the wrong failure",
            )
        else:
            raise AssertionError(
                "Invalid execution mode was accepted"
            )
    finally:
        clear_mode()

    print("D28_INVALID_MODE_FAIL_CLOSED: PASS")


def test_empty_string_is_not_explicit_invalid_mode():
    os.environ[ENV_NAME] = ""

    try:
        mode = ConfigurationManager().get_execution_mode()

        assert_true(
            mode == "PAPER",
            f"Empty execution mode did not default to PAPER: {mode!r}",
        )
    finally:
        clear_mode()

    print("D28_EMPTY_DEFAULT_PAPER: PASS")


def run():
    test_unset_defaults_to_paper()
    test_blank_defaults_to_paper()
    test_paper_is_accepted()
    test_live_is_accepted()
    test_mode_is_case_and_whitespace_normalized()
    test_invalid_mode_fails_closed()
    test_empty_string_is_not_explicit_invalid_mode()

    clear_mode()

    print("D28_EXECUTION_MODE_CONFIG: PASS")


if __name__ == "__main__":
    run()
