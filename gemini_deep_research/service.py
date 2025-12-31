"""Business logic for research operations."""

import logging
import tempfile
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from .api import DeepResearchAPI
from .models import (
    InteractionState,
    InteractionStatus,
    NoOutputsError,
    ResearchNotCompletedError,
    ResearchRequest,
    ResearchResult,
    ResearchStatistics,
)

logger = logging.getLogger(__name__)


def create_output_path() -> Path:
    """Create a timestamped output directory and return the report path."""
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    output_dir = Path(tempfile.gettempdir()) / "gemini-deep-research" / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "research.md"
    logger.debug(f"Created output path: {report_path}")
    return report_path


def _parse_statistics(response: dict[str, Any]) -> ResearchStatistics | None:
    """Parse statistics from API response dictionary.

    Args:
        response: API response containing optional statistics.

    Returns:
        ResearchStatistics if statistics are present, None otherwise.
    """
    stats_dict = response.get("statistics")
    return ResearchStatistics.from_dict(stats_dict) if stats_dict else None


def start_research(api: DeepResearchAPI, request: ResearchRequest) -> str:
    """Start a new research task.

    Args:
        api: Initialized DeepResearchAPI client.
        request: Research request containing query.

    Returns:
        Interaction ID for the started research task.
    """
    return api.start_interaction(request.query)


def poll_research_until_complete(
    api: DeepResearchAPI,
    interaction_id: str,
    poll_interval: int,
    on_status_update: Callable[[str, float], None] | None = None,
    max_attempts: int | None = None,
) -> dict[str, Any]:
    """Poll research status until completion or failure.

    Args:
        api: Initialized DeepResearchAPI client.
        interaction_id: The interaction ID to poll.
        poll_interval: Interval in seconds between status checks.
        on_status_update: Optional callback(state: str, elapsed_seconds: float) called on each poll.
        max_attempts: Maximum number of poll attempts before giving up. None for unlimited.

    Returns:
        Final API response dictionary when completed or failed.

    Raises:
        TimeoutError: If max_attempts is reached without completion.
    """
    logger.debug(f"Starting to poll interaction {interaction_id} (interval: {poll_interval}s)")
    start_time = time.time()
    attempts = 0

    while True:
        response = api.get_interaction_status(interaction_id)
        state = response.get("state")

        attempts += 1
        elapsed = time.time() - start_time
        logger.debug(f"Poll attempt {attempts}: state={state}, elapsed={elapsed:.1f}s")

        if on_status_update:
            on_status_update(state, elapsed)

        if state in (InteractionState.COMPLETED, InteractionState.FAILED):
            logger.debug(f"Research completed with state: {state} after {attempts} attempts ({elapsed:.1f}s)")
            return response

        if max_attempts is not None and attempts >= max_attempts:
            raise TimeoutError(
                f"Research polling timed out after {attempts} attempts "
                f"({attempts * poll_interval} seconds). Current state: {state}"
            )

        time.sleep(poll_interval)


def save_research_result(
    report_path: Path, api_response: dict[str, Any], duration_mins: float | None = None
) -> ResearchResult:
    """Save research results to file and create result object.

    Args:
        report_path: Path where the report should be saved.
        api_response: API response containing outputs and statistics.
        duration_mins: Optional duration in minutes.

    Returns:
        ResearchResult with report path and statistics.

    Raises:
        Exception: If outputs are not available.
    """
    outputs = api_response.get("outputs", [])
    if not outputs:
        raise NoOutputsError("No outputs available")

    text = outputs[-1].get("text", "No text output found.")
    logger.debug(f"Saving research report to {report_path} ({len(text)} chars)")
    report_path.write_text(text)

    statistics = _parse_statistics(api_response)
    if statistics:
        logger.debug(f"Report statistics: {statistics.word_count} words, {statistics.line_count} lines")

    return ResearchResult(
        report_path=report_path,
        statistics=statistics,
        duration_mins=duration_mins,
    )


def get_interaction_status(api: DeepResearchAPI, interaction_id: str) -> InteractionStatus:
    """Get the status of a research interaction.

    Args:
        api: Initialized DeepResearchAPI client.
        interaction_id: The interaction ID to check.

    Returns:
        InteractionStatus with current state and optional statistics/error.
    """
    response = api.get_interaction_status(interaction_id)

    statistics = _parse_statistics(response)

    error_dict = response.get("error", {})
    error_code = error_dict.get("code") if error_dict else None
    error_message = error_dict.get("message") if error_dict else None

    return InteractionStatus(
        interaction_id=interaction_id,
        state=response.get("state"),
        statistics=statistics,
        error_code=error_code,
        error_message=error_message,
    )


def fetch_completed_results(api: DeepResearchAPI, interaction_id: str) -> ResearchResult:
    """Fetch completed research results.

    Args:
        api: Initialized DeepResearchAPI client.
        interaction_id: The interaction ID to fetch results for.

    Returns:
        ResearchResult with report path and statistics.

    Raises:
        ResearchNotCompletedError: If research is not completed.
        NoOutputsError: If no outputs are available.
    """
    # Make a single API call to get the response
    response = api.get_interaction_status(interaction_id)
    state = response.get("state")

    if state != InteractionState.COMPLETED:
        raise ResearchNotCompletedError(f"Research is not yet completed. Current status: {state}")

    report_path = create_output_path()
    return save_research_result(report_path, response)
