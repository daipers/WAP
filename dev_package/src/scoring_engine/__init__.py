from typing import TYPE_CHECKING

from .score_runs import ResponseSnapshot, ScoreRun, ScoreRunRepository

if TYPE_CHECKING:
    from scoring_engine.scoring_service import ScoringService


def __getattr__(name: str):
    if name == "ScoringService":
        from .scoring_service import ScoringService

        return ScoringService
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = [
    "ResponseSnapshot",
    "ScoreRun",
    "ScoreRunRepository",
    "ScoringService",
]
