---
name: gemini-deep-research
description: Conducts comprehensive, autonomous deep research on specific topics using Google's Gemini Deep Research API. Initiates long-running background research tasks that synthesize multiple sources into detailed reports. Use when users request deep analysis, comprehensive research, or multi-source synthesis on complex topics. Triggered by phrases like "research", "deep dive", "comprehensive analysis", or when simple fact lookups are insufficient.
---

# Gemini Deep Research

Perform autonomous deep research using the `gemini-deep-research` CLI tool.

## Workflow

1. **Start research** with the user's query:
```bash
gemini-deep-research research "Your detailed research query here"
```

2. **Wait for completion** - This is a long-running operation (typically 3-10+ minutes). The CLI will guide you with printed instructions.

3. **Read and present results** - After completion, the tool prints the path to the generated report. Use the Read tool to access it:
```
/tmp/gemini-deep-research/<timestamp>/research.md
```

4. Present the research findings to the user, summarizing key insights from the comprehensive report.

## Notes

- The CLI is self-guiding and prints all necessary commands with interaction IDs
- All edge cases are handled by the CLI's printed guidance messages
