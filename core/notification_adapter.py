from __future__ import annotations

import shutil
import subprocess
from typing import Protocol

from core.alert_models import Alert


class NotificationAdapter(Protocol):
    def notify(self, alert: Alert) -> bool:
        ...


class TermuxNotificationAdapter:
    """Best-effort Android notification adapter."""

    def __init__(self, command: str = "termux-notification", timeout: float = 3.0):
        self.command = command
        self.timeout = timeout

    def notify(self, alert: Alert) -> bool:
        if shutil.which(self.command) is None:
            return False

        try:
            result = subprocess.run(
                [
                    self.command,
                    "--id",
                    alert.alert_id,
                    "--title",
                    f"Jaguar {alert.severity}: {alert.alert_type}",
                    "--content",
                    alert.message,
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
        except (OSError, subprocess.SubprocessError):
            return False

        return result.returncode == 0
