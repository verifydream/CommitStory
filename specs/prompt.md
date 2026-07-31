# CommitStory AI Coding Prompt — Full Phase 1–3

> Copy-paste this entire message to your AI coding agent (Claude Code, Codex, Aider, Cursor, etc.). Self-contained.  
> **Agent:** Read, plan, execute, commit. No human in the loop until final review.  
> **Language:** English (code/comments may mix English + Indonesian where natural).

---

You are an expert Python CLI engineer. Your task: transform the CommitStory prototype into a production-ready, portfolio-grade pip-installable CLI tool by executing all 3 phases in `specs/plan.md`.

---

## 1. FIRST — Load Context

Before writing any code, read these 3 files. They contain everything you need.

```
specs/PRD.md       — Product assessment, 20+ issues ranked, architecture decisions, risk matrix
specs/plan.md      — 24 tasks, exact code snippets, commands, verification steps, commit messages
specs/task-check.md — Trackable checklist with phase gates
```

**The plan is the source of truth.** Every task has exact file paths, code changes, verification commands, and expected outcomes.

---

## 2. Project Summary

**CommitStory** is a Python CLI (~550 LOC) that reads local git history and generates:
- **Daily dev diary** — narrative from commits via local LLM (llama.cpp / GGUF)
- **Weekly summary** — velocity, refactor frequency, bug density
- **Tech debt detection** — repeated refactors, fix chains, unstable modules
- **Multi-repo dashboard** — aggregate across projects
- **Export** — Markdown or JSON

**Tech stack:** Python 3.10+, GitPython, llama-cpp-python, argparse. Zero web dependencies.

**Current state:** Single-commit prototype (v0.1.0). Clean architecture but zero tests, 3 known bugs, no CI, missing CLI flags.

---

## 3. Execution Order

Execute phases **sequentially**. Do not skip ahead. Each phase gates the next.

| Order | Phase | Tasks | Outcome |
|-------|-------|-------|---------|
| 1 | Critical Fixes | 1.1 → 1.7 | `pytest` all green, `mypy` zero errors, `ruff` zero warnings |
| 2 | Core DX | 2.1 → 2.9 | All CLI flags functional, `--help` complete, shell completion works |
| 3 | Polish | 3.1 → 3.8 | Docker, CI, rich output, caching, metadata |

### Per-Task Workflow

```
1. Read task in specs/plan.md
2. Make the exact code changes described (copy code snippets verbatim)
3. ruff check src/ tests/    (zero new warnings)
4. mypy src/commitstory/     (zero errors)
5. pytest --cov              (all passing, ≥ 80% coverage)
6. git add + git commit      (use the exact commit message from plan.md)
7. Update specs/task-check.md — mark task as ✅
8. Next task
```

Do NOT combine tasks. One commit per task. This is non-negotiable — the user reviews per-task commits.

---

## 4. Phase Gates — Do NOT Skip

After each phase, run the gate check:

| Phase | Gate |
|-------|------|
| 1 | `pytest --cov --cov-fail-under=80` all green, `mypy` zero errors, `ruff check` zero |
| 2 | `commitstory --version` works, `commitstory --help` shows all flags + examples, `commitstory --author "test"` filters |
| 3 | `docker compose up` works, CI workflow valid YAML, `pip install -e .` installs correctly |

**If a gate fails:** fix the issue immediately. Do not proceed to next phase with a failing gate.

---

## 5. Auto-Decision Policy

You are working autonomously. The user is NOT available for questions.

**When you encounter ambiguity:**
1. Pick the most pragmatic, YAGNI-compliant option
2. Document the decision in a running `specs/decisions.md` file — one line per decision
3. Move on

**What counts as "pragmatic":**
- Prefer stdlib over new dependencies
- Prefer simpler implementation with fewer lines
- Prefer the pattern already used in the codebase (dataclasses, argparse, module-level constants)
- If the plan says "X or Y" — pick the first one
- If the plan is silent — match existing codebase conventions

**Do NOT:**
- Add abstractions "for later" (no ABCs, no factories, no interfaces)
- Gold-plate with unnecessary features beyond the plan
- Rewrite working code that the plan didn't target
- Change the tech stack (GitPython stays, llama-cpp-python stays, argparse stays — no click/typer migration)
- Add web frameworks, databases, or async

---

## 6. Key Codebase Conventions to Follow

- **Type hints everywhere** — `mypy --strict` enforced
- **Dataclasses** for structured data (`CommitInfo`, `DebtFlag`, etc.)
- **Module-level constants** for templates (`DAILY_PROMPT`, etc.)
- **Single `main()` entry** with `argparse` — no decorators, no click
- **`try/except ImportError`** for optional deps (llama-cpp-python)
- **Conventional commits** for git messages: `fix:`, `feat:`, `test:`, `refactor:`, `chore:`, `ci:`, `docs:`
- **No `print()` in library code** — use `logging` module
- **Pathlib** over `os.path`
- **`from __future__ import annotations`** for forward references

---

## 7. File Structure (for reference)

```
CommitStory/
├── src/
│   └── commitstory/
│       ├── __init__.py          # __version__ string
│       ├── main.py              # CLI entry point (argparse)
│       ├── config.py            # Config dataclass
│       ├── git_parser.py        # Repo parsing, CommitInfo
│       ├── summarizer.py        # LLM + fallback summarizer
│       ├── analytics.py         # Debt detection, frequency
│       ├── dashboard.py         # Multi-repo dashboard
│       ├── export.py            # Markdown + JSON export
│       └── templates/
│           ├── __init__.py
│           └── prompts.py       # LLM prompt templates
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Shared fixtures
│   ├── test_git_parser.py
│   ├── test_analytics.py
│   ├── test_summarizer.py
│   ├── test_export.py
│   └── test_config.py
├── specs/
│   ├── PRD.md
│   ├── plan.md
│   ├── task-check.md
│   └── prompt.md                # This file
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .gitignore
├── .pre-commit-config.yaml
├── .github/workflows/ci.yml
└── README.md
```

---

## 8. Tracking

At the end of each task, edit `specs/task-check.md` and mark it `✅`. The user will review this file.

At the end of each phase, add a section header in `specs/decisions.md`:

```markdown
## Phase N Decisions

- [task-id]: [decision] — [brief reason]
```

---

## 9. Final Handoff

When ALL 3 phases are complete and all gates pass:

1. Run `pytest --cov --cov-fail-under=80` one final time — all must pass
2. Run `mypy src/commitstory/` — zero errors
3. Run `ruff check src/ tests/` — zero warnings
4. Run `pip install -e .` — successful
5. Verify: `commitstory --help`, `commitstory --version`, `commitstory --no-llm --days 1` all work
6. Push all commits to origin

Create a summary in `specs/decisions.md`:

```markdown
## Final Summary

### Gates
- [x] pytest — all passing, ≥ 80% coverage
- [x] mypy — zero errors
- [x] ruff — zero warnings
- [x] pip install — successful
- [x] docker compose up — works
- [x] CI workflow — valid YAML

### What Changed
[Bulleted list grouped by phase]

### Test Results
- Unit tests: [N] passing
- Coverage: [X]%
```

---

## 10. Reference Commands

```bash
# Install
pip install -e ".[dev]"

# Dev loop
ruff check src/ tests/          # Lint
mypy src/commitstory/           # Type check
pytest --cov=src/commitstory    # Test + coverage
pytest --cov --cov-fail-under=80  # Enforce coverage gate

# Run the tool
commitstory --help
commitstory --version
commitstory --days 7 --no-llm
commitstory --days 1 --detail daily

# Git workflow
git add -A
git commit -m "fix: description"
git push origin master
```

---

**Begin.** Start with Task 1.1. Read `specs/plan.md` section 1.1, make the changes, verify, commit, mark checklist, continue.

**Jangan banyak mikir, gas eksekusi aja.**
