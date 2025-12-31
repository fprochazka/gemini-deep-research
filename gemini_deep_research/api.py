"""Client for the Gemini Interactions API using google-genai SDK.

This module provides a high-level interface to the Google Gemini Interactions API,
specifically designed for working with the Deep Research Pro agent. It handles
interaction creation, status polling, and result extraction.

The Deep Research Pro agent performs autonomous research on complex topics,
synthesizing information from multiple sources into comprehensive reports.
Research tasks typically take 3-10+ minutes to complete.

Classes:
    DeepResearchAPI: Main client for interacting with the Gemini Deep Research agent.
"""

import logging
import warnings
from typing import Any

from google import genai

from .models import InteractionState

# Suppress experimental warnings from google-genai SDK
# The Interactions API is in beta, so these warnings are expected
warnings.filterwarnings("ignore", message="Interactions usage is experimental")

logger = logging.getLogger(__name__)


class DeepResearchAPI:
    """Client for the Gemini Interactions API with Deep Research Pro agent.

    This class wraps the google-genai SDK to provide a simplified interface for
    conducting deep research using the Deep Research Pro agent. It manages the
    lifecycle of research interactions including creation, polling, and result
    extraction.

    The Deep Research Pro agent:
    - Performs autonomous web research on complex topics
    - Synthesizes information from multiple sources
    - Generates comprehensive, well-cited reports in markdown format
    - Runs in background mode with polling for completion

    Attributes:
        AGENT_NAME: Identifier for the Deep Research Pro agent (constant).
        api_key: Google Gemini API key for authentication.
        client: Initialized google-genai Client instance.

    Example:
        >>> api = DeepResearchAPI(api_key="your-key")
        >>> interaction_id = api.start_interaction("Research quantum computing")
        >>> # Poll for completion
        >>> while True:
        ...     status = api.get_interaction_status(interaction_id)
        ...     if status["state"] == "COMPLETED":
        ...         report = status["outputs"][-1]["text"]
        ...         break
    """

    AGENT_NAME = "deep-research-pro-preview-12-2025"

    def __init__(self, api_key: str):
        """Initialize the Deep Research API client.

        Args:
            api_key: Google Gemini API key. Get one from https://aistudio.google.com/apikey

        Note:
            The client is initialized immediately upon instantiation. Ensure the
            API key is valid before creating the client to avoid authentication errors.
        """
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)

    def start_interaction(self, query: str) -> str:
        """Start a new research interaction with the Deep Research Pro agent.

        Creates a background research task that runs asynchronously. The agent will
        autonomously research the topic, synthesize findings, and generate a report.

        Args:
            query: The research topic or question. Be specific for best results.
                  Examples:
                  - "What are the latest developments in quantum computing in 2025?"
                  - "Compare different approaches to implementing distributed tracing"

        Returns:
            str: Unique interaction ID for polling status and retrieving results.
                Format: "v1_<base64_encoded_identifier>"

        Raises:
            Exception: If the API request fails (network error, invalid API key, etc.)

        Note:
            Research tasks typically take 3-10+ minutes depending on query complexity.
            Use get_interaction_status() to poll for completion.
        """
        logger.debug(f"Starting research interaction with agent {self.AGENT_NAME}")
        logger.debug(f"Query: {query}")

        interaction = self.client.interactions.create(
            input=query,
            agent=self.AGENT_NAME,
            background=True,
        )

        logger.debug(f"Interaction created with ID: {interaction.id}")
        return interaction.id

    def get_interaction_status(self, interaction_id: str) -> dict[str, Any]:
        """Get the current status of a research interaction.

        Polls the Gemini API to check the status of a research task and retrieve
        results when complete. This method should be called repeatedly (with delays)
        until the state is "COMPLETED", "FAILED", or "CANCELLED".

        Args:
            interaction_id: The ID returned from start_interaction().

        Returns:
            dict: Interaction status with the following structure:
                {
                    "id": str,              # Interaction identifier
                    "state": str,           # One of: PROCESSING, COMPLETED, FAILED, CANCELLED
                    "status": str,          # Raw status from SDK (in_progress, completed, etc.)
                    "outputs": [            # Present only when state is COMPLETED
                        {"text": str}       # The research report in markdown
                    ],
                    "error": {              # Present only when state is FAILED
                        "code": str,        # Error code
                        "message": str      # Error description
                    },
                    "statistics": {         # Present only when state is COMPLETED
                        "agent": str,       # Agent name used
                        "word_count": int,  # Number of words in report
                        "char_count": int,  # Number of characters in report
                        "line_count": int   # Number of lines in report
                    }
                }

        Raises:
            Exception: If the API request fails or interaction_id is invalid.

        Note:
            - Poll this method every 10-30 seconds to check for completion
            - The Deep Research agent does not report token usage (usage field is None)
            - Statistics are calculated from the generated report text
        """
        logger.debug(f"Polling status for interaction: {interaction_id}")
        interaction = self.client.interactions.get(interaction_id)

        # Convert SDK response to dict format expected by main.py
        # Map SDK status to InteractionState enum for type safety
        status = interaction.status.lower()
        if status == "in_progress":
            state = InteractionState.PROCESSING
        elif status == "completed":
            state = InteractionState.COMPLETED
        elif status == "failed":
            state = InteractionState.FAILED
        elif status == "cancelled":
            state = InteractionState.CANCELLED
        else:
            # For unknown states, convert to uppercase string and wrap in enum
            state = InteractionState(status.upper())

        logger.debug(f"Interaction status: {status} -> state: {state}")

        result = {
            "id": interaction.id,
            "state": state,
            "status": interaction.status,
        }

        # Add outputs if available
        if hasattr(interaction, "outputs") and interaction.outputs:
            result["outputs"] = [{"text": output.text} for output in interaction.outputs]

            # Calculate statistics from the generated report
            # Note: The Deep Research agent doesn't report token usage,
            # so we calculate basic text statistics instead
            output_text = interaction.outputs[-1].text
            result["statistics"] = {
                "agent": getattr(interaction, "agent", self.AGENT_NAME),
                "word_count": len(output_text.split()),
                "char_count": len(output_text),
                "line_count": len(output_text.split("\n")),
            }

        # Add error if present
        if hasattr(interaction, "error") and interaction.error:
            result["error"] = {
                "code": getattr(interaction.error, "code", "UNKNOWN"),
                "message": getattr(interaction.error, "message", str(interaction.error)),
            }

        return result
