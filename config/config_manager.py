"""
=========================================
Jaguar QuantX Configuration Manager
=========================================
"""

import os
import config.settings as settings
import config.institutional_config as institutional
import config.decision_config as decision


class ConfigurationManager:

    def __init__(self):
        self.settings = settings
        self.institutional = institutional
        self.decision = decision

    def get_setting(self, name, default=None):
        return getattr(self.settings, name, default)

    def get_institutional(self, name, default=None):
        return getattr(self.institutional, name, default)

    def get_decision(self, name, default=None):
        return getattr(self.decision, name, default)



    def get_execution_mode(self):
        """
        Resolve the authoritative PAPER/LIVE transport mode.

        Unset or blank configuration defaults to PAPER.
        Explicit PAPER and LIVE are accepted.
        Any other explicit value fails closed.
        """

        raw = os.getenv(
            settings.EXECUTION_MODE_ENV
        )

        if raw is None or not raw.strip():
            return settings.DEFAULT_EXECUTION_MODE

        mode = raw.strip().upper()

        if mode not in settings.ALLOWED_EXECUTION_MODES:
            raise RuntimeError(
                "FAIL-CLOSED: invalid execution mode: "
                f"{mode}"
            )

        return mode

    def validate(self):
        return True


config = ConfigurationManager()
