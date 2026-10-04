"""Base class for mission stages."""
from __future__ import annotations

import abc
from typing import Any

from skyscan.mission.context import MissionContext
from skyscan.types import Check
from skyscan.utils.logger import get_logger

log = get_logger("MISSION/STAGE")


class Stage(abc.ABC):
    """Abstract base class for all mission stages."""

    id: str = ""
    title: str = ""
    rulebook: str = ""
    summary: str = ""

    @abc.abstractmethod
    def preconditions(self, ctx: MissionContext) -> list[Check]:
        """Evaluate preconditions before starting the stage.

        Returns a list of Check items. Any failed blocking check results in NO-GO.
        """

    def preview(self, ctx: MissionContext) -> list[Check]:
        """Instant GO / NO-GO evaluation against the current state, for the UI. Must not block or command anything.

        Stages whose ``preconditions`` wait for the vehicle override this with the non-waiting part.
        """
        return self.preconditions(ctx)

    @abc.abstractmethod
    def run(self, ctx: MissionContext) -> bool:
        """Execute the stage logic.

        Must update ctx.report, ctx.phase, criteria and metrics.
        Returns True if successful, False otherwise.
        """

    def describe(self, cfg: Any = None) -> dict[str, Any]:
        """Return stage descriptor for UI consumption."""
        return {
            "id": self.id,
            "title": self.title,
            "rulebook": self.rulebook,
            "summary": self.summary,
            "preconditions": [c.name for c in getattr(self, "precondition_specs", [])],
            "criteria": [c.name for c in getattr(self, "criteria_specs", [])],
            "config": cfg.to_dict() if hasattr(cfg, "to_dict") else (cfg if isinstance(cfg, dict) else {}),
        }
