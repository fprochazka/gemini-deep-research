"""Main CLI application for Deep Research."""

import logging
import os
import time
from typing import Annotated

import typer
from dotenv import load_dotenv
from rich import print as rprint
from rich.console import Console

from . import service
from .api import DeepResearchAPI
from .models import (
    InteractionState,
    InteractionStatus,
    ResearchNotCompletedError,
    ResearchRequest,
    ResearchResult,
    ResearchStatistics,
)

# Load environment variables from .env if it exists
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

app = typer.Typer(
    rich_markup_mode=None,
    pretty_exceptions_enable=False,
)

console = Console()

# Constants
LONG_RUNNING_THRESHOLD_SECONDS = 540  # 9 minutes


def get_api_key() -> str:
    """Get the Gemini API key from environment variables."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        rprint("[red]Error: GEMINI_API_KEY environment variable not set.[/red]")
        rprint("Please add it to your environment or a .env file.")
        raise typer.Exit(code=1)
    return api_key


def get_api() -> DeepResearchAPI:
    """Get initialized DeepResearchAPI client."""
    api_key = get_api_key()
    return DeepResearchAPI(api_key)


def display_statistics(statistics: ResearchStatistics, duration_mins: float | None = None) -> None:
    """Display research statistics."""
    rprint("\n[bold]Statistics:[/bold]")
    rprint(f"  Agent: [blue]{statistics.agent}[/blue]")
    if duration_mins is not None:
        rprint(f"  Duration: [yellow]{duration_mins:.2f} minutes[/yellow]")
    rprint(
        f"  Report: [green]{statistics.word_count:,} words[/green], "
        f"[green]{statistics.char_count:,} characters[/green], "
        f"[green]{statistics.line_count:,} lines[/green]"
    )


def display_result(result: ResearchResult) -> None:
    """Display research result with statistics."""
    rprint("\n[bold green]Research Completed:[/bold green]")
    rprint(f"Report saved to: [cyan]{result.report_path}[/cyan]")

    if result.statistics:
        display_statistics(result.statistics, result.duration_mins)


def display_status(status: InteractionStatus) -> None:
    """Display interaction status information."""
    rprint(f"\n[bold]Interaction ID:[/bold] [cyan]{status.interaction_id}[/cyan]")
    rprint(f"[bold]Status:[/bold] {status.state}")

    if status.is_completed:
        if status.statistics:
            display_statistics(status.statistics)
        rprint("\n[green]Research is complete![/green]")
        rprint(f"[bold]Fetch results:[/bold] [cyan]gemini-deep-research fetch-results {status.interaction_id}[/cyan]")

    elif status.is_failed:
        rprint(f"\n[red]Error {status.error_code}: {status.error_message}[/red]")

    elif status.is_processing:
        rprint("\n[yellow]Research is still in progress...[/yellow]")


@app.command()
def research(
    query: Annotated[str, typer.Argument(help="The research topic or question.")],
    poll_interval: Annotated[
        int, typer.Option("--poll-interval", "-i", help="Interval in seconds between polling for results.")
    ] = 10,
):
    """
    Conduct autonomous deep research on a specific topic and save the report to a file.
    """
    api = get_api()

    request = ResearchRequest(query=query, poll_interval=poll_interval)
    report_path = service.create_output_path()

    try:
        # Start research
        with console.status(f"[bold green]Initiating research on: {query}...", spinner="dots"):
            interaction_id = service.start_research(api, request)

        # Display interaction ID prominently
        rprint(f"\n[bold blue]Interaction ID:[/bold blue] [cyan]{interaction_id}[/cyan]")
        rprint("[dim]Use 'gemini-deep-research status <ID>' to check progress[/dim]\n")

        # Track timing for long-running message
        start_time = time.time()
        shown_long_running_msg = False

        # Poll until complete
        with console.status("[bold green]Researching...", spinner="earth") as status:

            def on_status_update(state: str, elapsed: float):
                nonlocal shown_long_running_msg

                # Show long-running message after threshold is reached
                if elapsed > LONG_RUNNING_THRESHOLD_SECONDS and not shown_long_running_msg:
                    status.stop()
                    rprint("\n[yellow]Research is taking longer than expected (9+ minutes).[/yellow]")
                    rprint("\n[bold]You can:[/bold]")
                    rprint(f"  • Check status: [cyan]gemini-deep-research status {interaction_id}[/cyan]")
                    rprint(
                        f"  • Fetch results when done: [cyan]gemini-deep-research fetch-results {interaction_id}[/cyan]"
                    )
                    rprint("\n[dim]Press Ctrl+C to stop polling (research continues in background)[/dim]")
                    rprint("[dim]Continuing to wait...[/dim]\n")
                    shown_long_running_msg = True
                    status.start()

                # Update status message
                status.update(f"[bold green]Status: {state}... (checking again in {poll_interval}s)")

            response = service.poll_research_until_complete(api, interaction_id, poll_interval, on_status_update)

        # Handle completion
        if response.get("state") == InteractionState.COMPLETED:
            duration_mins = (time.time() - start_time) / 60
            result = service.save_research_result(report_path, response, duration_mins)
            display_result(result)
        elif response.get("state") == InteractionState.FAILED:
            error = response.get("error", {})
            rprint("\n[red]Research task failed.[/red]")
            rprint(f"[red]Error {error.get('code')}: {error.get('message')}[/red]")
            raise typer.Exit(code=1)

    except Exception as e:
        rprint(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(code=1) from None


@app.command()
def status(
    interaction_id: Annotated[str, typer.Argument(help="The interaction ID to check status for.")],
):
    """
    Check the status of a research interaction.
    """
    api = get_api()

    try:
        status_result = service.get_interaction_status(api, interaction_id)
        display_status(status_result)
    except Exception as e:
        rprint(f"[red]Error checking status:[/red] {str(e)}")
        raise typer.Exit(code=1) from None


@app.command(name="fetch-results")
def fetch_results(
    interaction_id: Annotated[str, typer.Argument(help="The interaction ID to fetch results for.")],
):
    """
    Fetch completed research results and save to a markdown file.
    """
    api = get_api()

    try:
        with console.status(f"[bold green]Fetching results for {interaction_id}...", spinner="dots"):
            result = service.fetch_completed_results(api, interaction_id)

        rprint("\n[bold green]Research Results Retrieved:[/bold green]")
        rprint(f"Report saved to: [cyan]{result.report_path}[/cyan]")

        if result.statistics:
            display_statistics(result.statistics)

    except ResearchNotCompletedError as e:
        rprint(f"[yellow]{str(e)}[/yellow]")
        rprint("[dim]Use 'gemini-deep-research status <ID>' to check progress[/dim]")
        raise typer.Exit(code=0) from None
    except Exception as e:
        rprint(f"[red]Error fetching results:[/red] {str(e)}")
        raise typer.Exit(code=1) from None


@app.callback(invoke_without_command=True)
def callback(
    ctx: typer.Context,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose debug logging")] = False,
):
    """
    Deep Research CLI - Powered by Gemini Deep Research Pro
    """
    # Configure logging level based on verbose flag
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Store verbose flag in context for commands to access if needed
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose

    if ctx.invoked_subcommand is None:
        rprint(ctx.get_help())


if __name__ == "__main__":
    app()
