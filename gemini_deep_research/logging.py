"""Logging configuration for the CLI."""

import logging

from rich.console import Console
from rich.logging import RichHandler

error_console = Console(stderr=True)


def setup_logging(verbose: bool = False) -> None:
    """Configure logging based on verbose flag."""
    level = logging.DEBUG if verbose else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                console=error_console,
                rich_tracebacks=True,
                show_time=verbose,
                show_path=verbose,
            )
        ],
        force=True,
    )

    if not verbose:
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("google.auth").setLevel(logging.WARNING)
        logging.getLogger("google_auth_httplib2").setLevel(logging.WARNING)
