"""
=========================================
Jaguar QuantX Configuration Manager
=========================================
"""

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

    def validate(self):
        return True


config = ConfigurationManager()
