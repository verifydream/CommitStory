# CommitStory

CLI tool that reads git commit history and generates a readable dev diary — what was built, bugs fixed, decisions made, and what's next. Powered by local LLM via llama.cpp.

## Installation

```bash
pip install commitstory
```

Or run from source:

```bash
cd commitstory
pip install -e .
```

## Usage

```bash
# Daily diary (last 24h)
commitstory

# Last 7 days
commitstory --days 7

# Weekly summary
commitstory --days 7 --detail weekly

# Tech debt detection
commitstory --days 30 --detail debt

# JSON output
commitstory --format json

# Use custom GGUF model
commitstory --model ~/models/phi-3.5-mini.Q4_K_M.gguf

# Multi-repo dashboard
commitstory --multi

# Force fallback (stats-only, no LLM)
commitstory --no-llm
```

## Features

- **Daily Dev Diary** — concise narrative from commits
- **Weekly Summary** — velocity, refactor frequency, bug density
- **Tech Debt Detection** — repeated refactors, fix chains, unstable modules
- **Multi-repo Dashboard** — aggregate across projects
- **Export** — Markdown or JSON
- **Fully Offline** — GGUF models, no API needed

## Requirements

- Python 3.10+
- Git repository (local)
- Optional: GGUF model for LLM narrative (falls back to stats-only)

## License

MIT
