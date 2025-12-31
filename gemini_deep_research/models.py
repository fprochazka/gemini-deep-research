"""Data models for research operations."""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


# Interaction State Constants
class InteractionState(str, Enum):
    """State values for research interactions."""

    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


# Custom Exceptions
class DeepResearchError(Exception):
    """Base exception for deep research operations."""


class NoOutputsError(DeepResearchError):
    """Research completed but no outputs available."""


class ResearchNotCompletedError(DeepResearchError):
    """Attempted to fetch results for incomplete research."""


@dataclass
class ResearchRequest:
    """Request to start a research task."""

    query: str
    poll_interval: int = 10


@dataclass
class ResearchStatistics:
    """Statistics about a completed research report."""

    agent: str
    word_count: int
    char_count: int
    line_count: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ResearchStatistics":
        """Create statistics from API response dictionary."""
        return cls(
            agent=data.get("agent", "unknown"),
            word_count=data.get("word_count", 0),
            char_count=data.get("char_count", 0),
            line_count=data.get("line_count", 0),
        )


@dataclass
class ResearchResult:
    """Result of a completed research task."""

    report_path: Path
    statistics: ResearchStatistics | None = None
    duration_mins: float | None = None


@dataclass
class InteractionStatus:
    """Status of a research interaction."""

    interaction_id: str
    state: InteractionState | str  # InteractionState enum or string for compatibility
    statistics: ResearchStatistics | None = None
    error_code: str | None = None
    error_message: str | None = None

    @property
    def is_completed(self) -> bool:
        """Check if the research is completed."""
        return self.state == InteractionState.COMPLETED

    @property
    def is_failed(self) -> bool:
        """Check if the research failed."""
        return self.state == InteractionState.FAILED

    @property
    def is_processing(self) -> bool:
        """Check if the research is still processing."""
        return self.state == InteractionState.PROCESSING
