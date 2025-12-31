# gemini-deep-research

CLI tool for conducting autonomous deep research using Google's Gemini Deep Research Agent via the new beta Interactions API.

## Features

- **Autonomous Research**: Leverages Google's Deep Research Pro agent to conduct comprehensive research on any topic
- **Analyst-Grade Reports**: Generates detailed, well-structured, and cited research reports suitable for professional use
- **New Beta Interactions API**: Built on Google's latest Interactions API (Preview) designed for robust agentic workflows
- **Background Processing**: Long-running research tasks execute in the background with polling for status updates
- **Markdown Output**: Research reports are automatically saved as formatted markdown files
- **Rich CLI Interface**: Beautiful terminal UI with progress indicators and status updates
- **Environment Configuration**: Simple API key management via environment variables or `.env` file
- **Verbose Mode**: Optional detailed logging for monitoring research progress

## How It Works

The tool uses Google's new **beta Interactions API** to access the [Gemini Deep Research Agent](https://ai.google.dev/gemini-api/docs/deep-research) (`deep-research-pro-preview-12-2025`). This new API architecture specifically supports long-running, autonomous agentic workflows.

The process involves:

1. Submitting a research query to the Deep Research agent via the Interactions API
2. Monitoring the research task as it runs in the background (server-side execution)
3. Retrieving the completed research report
4. Saving the report to a timestamped markdown file

The Deep Research Agent autonomously searches for information, synthesizes findings, and produces comprehensive research reports.

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd gemini-deep-research

# Install globally with pipx in editable mode
pipx install -e .
```

After installation, the `gemini-deep-research` command will be available globally.

## Claude Code Skill (Optional)

For users of Claude Code, a skill is available that teaches Claude how to efficiently use the `gemini-deep-research` CLI tool. The skill includes:

- Typical workflow for conducting deep research
- Important notes about long-running operations (3-10+ minutes)
- Command documentation with examples
- How to read and present research results

### Installing the Skill

**For Claude Code (CLI)** - Global installation (available in all projects):

```bash
# Copy the skill directory to your global Claude Code skills directory
cp -r usage/claude-code-skill/gemini-deep-research ~/.claude/skills/
```

**For Claude Code (CLI)** - Project-specific installation (available only in this project):

```bash
# Copy the skill directory to your project's .claude/skills directory
mkdir -p .claude/skills
cp -r usage/claude-code-skill/gemini-deep-research .claude/skills/
```

**For Claude.ai or Claude Desktop** - Use the packaged skill file:

The `usage/claude-code-skill/gemini-deep-research.skill` file can be uploaded through Settings > Capabilities > Skills.

After installation, Claude will automatically use the skill when conducting deep research.

## Configuration

### API Key Setup

You need a Google Gemini API key to use this tool. Get one from the [Google AI Studio](https://aistudio.google.com/apikey).

**Option 1: Environment Variable**

```bash
export GEMINI_API_KEY="your-api-key-here"
```

**Option 2: .env File**

Create a `.env` file in your project directory or home directory:

```bash
GEMINI_API_KEY=your-api-key-here
```

The tool will automatically load the API key from the `.env` file.

## Usage

### Conduct Research

Start a new research task. The command will print an interaction ID that you can use to check status or cancel the task.

```bash
# Basic research query
gemini-deep-research research "What are the latest developments in quantum computing?"

# With custom poll interval (default: 10 seconds)
gemini-deep-research research "Impact of AI on software development" --poll-interval 15

# With verbose output for detailed status updates
gemini-deep-research research "Future of renewable energy" --verbose
```

When you start a research task, the tool will print the interaction ID:

```
Interaction ID: v1_abc123...
Use 'gemini-deep-research status <ID>' to check progress
```

**Note:** If research takes longer than 9 minutes, the tool will display a helpful message with options to check status or fetch results later. You can press Ctrl+C to stop polling while the research continues in the background, then use the `fetch-results` command to retrieve the completed report.

### Check Research Status

Check the status of a running or completed research task using its interaction ID:

```bash
gemini-deep-research status v1_abc123...
```

This will show:
- Current state (PROCESSING, COMPLETED, FAILED, or CANCELLED)
- Statistics (for completed tasks)
- Error details (for failed tasks)

### Fetch Completed Results

Retrieve and save completed research results to a markdown file:

```bash
gemini-deep-research fetch-results v1_abc123...
```

This is useful when:
- You cancelled the polling with Ctrl+C but the research completed in the background
- The research command was interrupted
- You want to retrieve results from a previous research session

### Output

Research reports are saved to timestamped directories:

```
/tmp/gemini-deep-research/2025-12-29T14-30-45/
  research.md
```

The tool displays the output path when research completes:

```
Research Completed:
Report saved to: /tmp/gemini-deep-research/2025-12-29T14-30-45/research.md
```

## CLI Commands

### research

Conduct autonomous deep research on a specific topic.

**Usage:**
```bash
gemini-deep-research research [OPTIONS] QUERY
```

**Arguments:**
- `QUERY` - The research topic or question (required)

**Options:**
- `--poll-interval`, `-i` - Interval in seconds between status checks (default: 10)
- `--verbose`, `-v` - Show detailed status updates (default: false)

### status

Check the status of a research interaction.

**Usage:**
```bash
gemini-deep-research status INTERACTION_ID
```

**Arguments:**
- `INTERACTION_ID` - The interaction ID from a research task (required)

### fetch-results

Retrieve and save completed research results to a markdown file.

**Usage:**
```bash
gemini-deep-research fetch-results INTERACTION_ID
```

**Arguments:**
- `INTERACTION_ID` - The interaction ID to fetch results for (required)

## Examples

### Quick Research

```bash
gemini-deep-research research "What is the state of fusion energy research in 2025?"
```

### Interactive Workflow

Start a research task and interact with it while it runs:

```bash
# Start research (prints interaction ID)
gemini-deep-research research "Latest developments in quantum computing"

# Output:
# Interaction ID: v1_abc123...
# Use 'gemini-deep-research status <ID>' to check progress

# Press Ctrl+C to stop polling (task continues in background)
# Then check status from another terminal
gemini-deep-research status v1_abc123...

# Fetch results when completed
gemini-deep-research fetch-results v1_abc123...
```

### Detailed Research with Monitoring

```bash
gemini-deep-research research \
  "Compare different approaches to implementing distributed tracing in microservices" \
  --verbose \
  --poll-interval 5
```

### Research from Script

```bash
#!/bin/bash
TOPIC="Emerging trends in cloud-native security"
INTERACTION_ID=$(gemini-deep-research research "$TOPIC" --verbose 2>&1 | grep -oP 'v1_[a-zA-Z0-9_-]+' | head -1)
echo "Started research with ID: $INTERACTION_ID"

# Later, check status
gemini-deep-research status "$INTERACTION_ID"
```

## Development

### Setup

```bash
# Install Poetry (if not already installed)
# Recommended: use pipx
pipx install poetry

# Alternative: use official installer
# curl -sSL https://install.python-poetry.org | python3 -

# Create virtual environment and install dependencies
# Poetry will automatically create .venv in the project directory
poetry install

# Activate the virtual environment
# After this, poetry commands will work inside the venv
source .venv/bin/activate

# Verify setup
poetry --version
pytest --version
```

### Testing

```bash
source .venv/bin/activate && pytest
```

### Linting and Formatting

```bash
source .venv/bin/activate && ruff check --fix . && ruff format .
```

### Code Style

This project follows these coding standards:

- **Style Guide**: PEP 8
- **Linter/Formatter**: Ruff
- **Line Length**: 120 characters
- **Quote Style**: Double quotes
- **Target Python Version**: 3.10+

### Project Structure

```
gemini-deep-research/
├── gemini_deep_research/     - Main package directory
│   ├── main.py              - CLI application entry point
│   ├── api.py               - Gemini Interactions API client
├── usage/                   - Usage examples and integrations
│   └── claude-code-skill/   - Claude Code skill for this tool
├── pyproject.toml           - Poetry configuration and dependencies
└── .env.example             - Example environment configuration
```

## API Details

This tool uses the Google GenAI Python SDK (`google-genai` package, version 1.56.0+) to interact with the **Gemini Interactions API (Public Beta)**:

- `client.interactions.create()` - Start a new research interaction with the Deep Research agent
- `client.interactions.get()` - Poll for interaction status and retrieve results

The **Gemini Deep Research Agent** (`deep-research-pro-preview-12-2025`) is the first specialized agent available through this new Interactions API, designed for autonomous, comprehensive research tasks that require multi-step reasoning and tool use.

The SDK provides a cleaner, more Pythonic interface compared to raw HTTP requests, with automatic authentication, type safety, and better error handling for these new beta endpoints.

## Limitations

- Research tasks can take several minutes to complete depending on query complexity
- API key must have access to the Gemini Interactions API
- Requires active internet connection for API calls
- Research quality depends on the Deep Research Pro model's capabilities and available information

## Requirements

- Python 3.10+
- Poetry for dependency management
- Valid Gemini API key with Interactions API access

## Troubleshooting

**Error: GEMINI_API_KEY environment variable not set**
- Ensure you've set the API key via environment variable or `.env` file
- Verify the `.env` file is in the current directory or home directory

**Research task fails**
- Check your API key has proper permissions for the Interactions API
- Verify your internet connection is active
- Try simplifying your research query

**Timeout or slow responses**
- Deep research tasks can take time; use `--verbose` to monitor progress
- Adjust `--poll-interval` to reduce API calls if needed

## License

MIT License - see LICENSE file for details
