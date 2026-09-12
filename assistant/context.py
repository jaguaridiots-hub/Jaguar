"""Trusted, read-only Assistant context builder."""

from __future__ import annotations

from typing import Any

from dashboard.ui_state import build_ui_state


def _mapping(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def build_assistant_context(state: Any, report: dict) -> dict:
    """Build an allow-listed, read-only context from canonical Jaguar state."""
    if not isinstance(report, dict):
        raise ValueError("Canonical Jaguar report must be a dictionary")

    ui = build_ui_state(state, report=report)

    system = dict(_mapping(ui.get("system")))
    execution = dict(_mapping(ui.get("execution")))

    # build_ui_state() already resolves PAPER/LIVE from the authoritative
    # execution configuration. Do not reinterpret state.mode here because
    # that field represents the analysis profile (SCALP/SWING/CLASSIC).

    # Never expose execution authorization identity to the LLM.
    execution.pop("authorization_id", None)

    safe_ui = dict(ui)
    safe_ui["system"] = system
    safe_ui["execution"] = execution

    return {
        "source": "JAGUAR_CANONICAL_ENTERPRISE_STATE",
        "read_only": True,
        "ui_state": safe_ui,
    }
