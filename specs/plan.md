# CommitStory — Implementation Plan

> **For AI coding agents:** Execute tasks phase-by-phase, in order. Each phase gates the next.  
> **For subagent-driven workflow:** One task = one `delegate_task` call. Review output before next task.  
> **Commit strategy:** One commit per task. Conventional commits (`feat:`, `fix:`, `refactor:`, `chore:`, `test:`).

---

## Phase 1: Critical Fixes + Test Suite

> **Outcome:** Bug-free foundation, 80%+ test coverage, type-safe.

---

### Task 1.1: Fix `DEBT_PROMPT` `{week_range}` placeholder bug

**Files:** `src/commitstory/templates/prompts.py`, `src/commitstory/summarizer.py`

**Problem:** `WEEKLY_PROMPT` and `DEBT_PROMPT` contain `{week_range}` placeholder. `summarize()` only does `template.replace("{commits}", formatted)` — the `{week_range}` stays as literal text in the LLM prompt.

**Fix:** Remove `{week_range}` from templates or compute it in `summarize()` and do a second `.replace()`.

```python
# summarizer.py — inside summarize(), after template.replace("{commits}", formatted):
from datetime import datetime, timedelta
week_start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
week_end = datetime.now().strftime("%Y-%m-%d")
prompt = prompt.replace("{week_range}", f"{week_start} to {week_end}")
```

**Verification:** Run with `--detail weekly --no-llm` — output should not contain literal `{week_range}`.

**Commit:** `fix: replace {week_range} placeholder in weekly/debt prompts`

---

### Task 1.2: Fix `_fallback_summary()` to respect `detail_level`

**Files:** `src/commitstory/summarizer.py`

**Problem:** `_fallback_summary()` ignores `detail_level` — always produces daily-format header regardless of `weekly`/`debt` mode.

**Fix:** Branch on `detail_level`:

```python
def _fallback_summary(commits: list[CommitInfo], detail_level: str) -> str:
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    total_add = sum(c.total_additions for c in commits)
    total_del = sum(c.total_deletions for c in commits)
    files = set()
    types: dict[str, int] = {}
    authors = set()
    for c in commits:
        files.update(c.files_changed)
        authors.add(c.author)
        if c.conventional_type:
            types[c.conventional_type] = types.get(c.conventional_type, 0) + 1

    type_summary = ", ".join(f"{k}: {v}" for k, v in sorted(types.items())) if types else "no conventional commits"

    if detail_level == "weekly":
        header = f"## Week ending {today} — Dev Diary ({len(commits)} commits)"
        subtitle = "Weekly Summary"
    elif detail_level == "debt":
        header = f"## Tech Debt Report — {today} ({len(commits)} commits analyzed)"
        subtitle = "Debt Analysis"
    else:
        header = f"## {today} — Dev Diary ({len(commits)} commits)"
        subtitle = "Daily Summary"

    lines = [
        header,
        "",
        f"**{subtitle}**",
        f"**Authors:** {', '.join(authors)}",
        f"**Files changed:** {len(files)}",
        f"**Lines:** +{total_add} / -{total_del}",
        f"**Types:** {type_summary}",
        "",
        "### Commits",
    ]
    for c in commits:
        lines.append(f"- {c.short_sha} {c.summary}")
    return "\n".join(lines)
```

**Verification:** `commitstory --detail weekly --no-llm` → shows "Week ending" header.

**Commit:** `fix: _fallback_summary respects detail_level (daily/weekly/debt)`

---

### Task 1.3: Fix `detect_debt()` off-by-one on final fix streak

**Files:** `src/commitstory/analytics.py`

**Problem:** After the `for` loop in `detect_debt()`, the final `fix_streaks` value is never checked. If the last N commits are all `fix:`, the streak is silently lost.

**Fix:** Add post-loop check:

```python
# After the for loop in detect_debt():
    # Check final streak (off-by-one fix)
    if fix_streaks >= 3:
        flags.append(DebtFlag(
            severity="medium",
            module="(general)",
            description=f"Chain of {fix_streaks} consecutive fix commits — possible instability",
            suggestion="Add regression tests before further fixes",
        ))

    return flags
```

**Verification:** Unit test with 4 consecutive `fix:` commits at end of list → should flag.

**Commit:** `fix: detect final fix streak in detect_debt (off-by-one)`

---

### Task 1.4: Add LRU-bounded LLM cache with `functools.lru_cache`

**Files:** `src/commitstory/summarizer.py`

**Problem:** `_LLM_CACHE` dict grows unboundedly. If user runs `commitstory --model path1` then `--model path2` then `--model path3` repeatedly, memory leaks.

**Fix:** Replace dict cache with `functools.lru_cache` + explicit eviction:

```python
import functools

_LLM_CACHE: dict[str, "Llama"] = {}
_MAX_CACHED_MODELS = 2

def _get_llm(model_path: str | None, n_ctx: int = 4096) -> "Llama | None":
    if not _LLAMA_AVAILABLE:
        return None
    key = model_path or "default"
    if key not in _LLM_CACHE:
        path = model_path
        try:
            _LLM_CACHE[key] = Llama(model_path=path, n_ctx=n_ctx, verbose=False)
        except Exception as e:
            logger.error("Failed to load model %s: %s", path, e)
            return None
        # Evict oldest if over limit
        while len(_LLM_CACHE) > _MAX_CACHED_MODELS:
            oldest = next(iter(_LLM_CACHE))
            if oldest != key:
                del _LLM_CACHE[oldest]
    return _LLM_CACHE[key]
```

**Verification:** Test that loading 3 different models keeps only 2 in cache.

**Commit:** `fix: bound LLM cache to prevent memory leak`

---

### Task 1.5: Remove unused `rich` dependency or make it actually used

**Files:** `pyproject.toml`, `src/commitstory/main.py`

**Problem:** `rich>=13.0` listed in `pyproject.toml` but never imported anywhere.

**Decision (ADR-6):** Remove `rich` for now. CLI is simple argparse + print. Add back when implementing progress spinners (Phase 3).

**Fix:**

```toml
# pyproject.toml — remove rich from dependencies
dependencies = [
    "gitpython>=3.1",
    "llama-cpp-python>=0.3.0",
]
```

**Verification:** `pip install -e .` — no `rich` pulled. `commitstory --help` still works.

**Commit:** `chore: remove unused rich dependency`

---

### Task 1.6: Add pytest test suite with ≥ 80% coverage

**Files:** 
- `tests/__init__.py` (new)
- `tests/test_git_parser.py` (new)
- `tests/test_analytics.py` (new)
- `tests/test_summarizer.py` (new)
- `tests/test_export.py` (new)
- `tests/test_config.py` (new)
- `tests/conftest.py` (new)
- `pyproject.toml` (add pytest config)

**conftest.py — reusable fixtures:**

```python
import pytest
from datetime import datetime, timedelta
from commitstory.git_parser import CommitInfo, FileStats

@pytest.fixture
def sample_commits():
    """Generate 10 synthetic commits across feat/fix/refactor types."""
    base = datetime(2026, 8, 1, 10, 0, 0)
    commits = []
    types = ["feat", "fix", "feat", "refactor", "fix", "fix", "docs", "feat", "fix", "chore"]
    for i, (t, offset_hours) in enumerate(zip(types, range(0, 30, 3))):
        commits.append(CommitInfo(
            sha=f"abc{i:04d}",
            short_sha=f"abc{i:04d}"[:8],
            message=f"{t}: change number {i}",
            summary=f"{t}: change number {i}",
            author="test-dev",
            date=base + timedelta(hours=offset_hours),
            files_changed=[f"src/module_{i%3}.py"],
            file_stats=[FileStats(path=f"src/module_{i%3}.py", additions=i*5, deletions=i*2)],
            total_additions=i*5,
            total_deletions=i*2,
            is_merge=False,
            conventional_type=t,
        ))
    return commits

@pytest.fixture
def fix_streak_commits():
    """4 consecutive fix commits at the end — should trigger debt flag."""
    base = datetime(2026, 8, 1, 10, 0, 0)
    return [
        CommitInfo(sha="abc0001", short_sha="abc0001", message="feat: initial",
                   summary="feat: initial", author="dev", date=base, files_changed=[],
                   file_stats=[], total_additions=0, total_deletions=0,
                   is_merge=False, conventional_type="feat"),
        CommitInfo(sha="abc0002", short_sha="abc0002", message="fix: bug1",
                   summary="fix: bug1", author="dev", date=base + timedelta(hours=1),
                   files_changed=[], file_stats=[], total_additions=0, total_deletions=0,
                   is_merge=False, conventional_type="fix"),
        CommitInfo(sha="abc0003", short_sha="abc0003", message="fix: bug2",
                   summary="fix: bug2", author="dev", date=base + timedelta(hours=2),
                   files_changed=[], file_stats=[], total_additions=0, total_deletions=0,
                   is_merge=False, conventional_type="fix"),
        CommitInfo(sha="abc0004", short_sha="abc0004", message="fix: bug3",
                   summary="fix: bug3", author="dev", date=base + timedelta(hours=3),
                   files_changed=[], file_stats=[], total_additions=0, total_deletions=0,
                   is_merge=False, conventional_type="fix"),
        CommitInfo(sha="abc0005", short_sha="abc0005", message="fix: bug4",
                   summary="fix: bug4", author="dev", date=base + timedelta(hours=4),
                   files_changed=[], file_stats=[], total_additions=0, total_deletions=0,
                   is_merge=False, conventional_type="fix"),
    ]
```

**test_analytics.py examples:**

```python
from commitstory.analytics import detect_debt, analyze_frequency

def test_detect_debt_flags_repeated_refactors(sample_commits):
    flags = detect_debt(sample_commits)
    # sample_commits has 1 refactor on module_1.py — not enough
    refactor_flags = [f for f in flags if "refactor" in f.description.lower()]
    assert len(refactor_flags) == 0  # only 1 refactor, not 3+

def test_detect_debt_off_by_one_fix_streak(fix_streak_commits):
    flags = detect_debt(fix_streak_commits)
    fix_flags = [f for f in flags if "consecutive fix" in f.description.lower()]
    assert len(fix_flags) == 1
    assert "4 consecutive" in fix_flags[0].description

def test_analyze_frequency_returns_report(sample_commits):
    freq = analyze_frequency(sample_commits)
    assert freq.velocity > 0
    assert freq.peak_day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
```

**test_summarizer.py:**

```python
from commitstory.summarizer import _fallback_summary, _format_commits

def test_fallback_summary_daily(sample_commits):
    result = _fallback_summary(sample_commits, "daily")
    assert "Dev Diary" in result
    assert "## " in result

def test_fallback_summary_weekly(sample_commits):
    result = _fallback_summary(sample_commits, "weekly")
    assert "Week ending" in result or "Weekly" in result

def test_fallback_summary_debt(sample_commits):
    result = _fallback_summary(sample_commits, "debt")
    assert "Debt" in result or "debt" in result.lower()

def test_format_commits(sample_commits):
    result = _format_commits(sample_commits)
    assert "feat:" in result
    assert "fix:" in result
```

**test_git_parser.py:**

```python
from commitstory.git_parser import parse_conventional_commit

def test_parse_feat():
    assert parse_conventional_commit("feat: add login") == "feat"
    assert parse_conventional_commit("feat(api): add endpoint") == "feat"

def test_parse_fix():
    assert parse_conventional_commit("fix: crash on null") == "fix"

def test_parse_non_conventional():
    assert parse_conventional_commit("updated stuff") is None
    assert parse_conventional_commit("FEAT: wrong case") is None

def test_parse_multiline():
    assert parse_conventional_commit("fix: header\n\nbody text") == "fix"
```

**test_export.py:**

```python
from commitstory.export import to_markdown, to_json, write_to_file
import json

def test_to_json(sample_commits):
    result = to_json(sample_commits)
    data = json.loads(result)
    assert data["total_commits"] == len(sample_commits)
    assert len(data["commits"]) == len(sample_commits)

def test_to_markdown(sample_commits):
    result = to_markdown(sample_commits)
    assert "CommitStory" in result
    assert "## Commit Log" in result

def test_write_to_file(tmp_path):
    p = tmp_path / "output.md"
    result = write_to_file("hello", p)
    assert result == p
    assert p.read_text() == "hello"
```

**pyproject.toml additions:**

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "pytest-mock>=3.12",
    "mypy>=1.8",
    "ruff>=0.4",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]

[tool.coverage.run]
source = ["src/commitstory"]
omit = ["src/commitstory/templates/*"]

[tool.coverage.report]
fail_under = 80
```

**Verification:** `pip install -e ".[dev]" && python -m pytest --cov=src/commitstory --cov-report=term` → ≥ 80% coverage, all green.

**Commit:** `test: add pytest suite with 80%+ coverage`

---

### Task 1.7: Add `mypy --strict` + `py.typed` marker

**Files:**
- `pyproject.toml` (add `[tool.mypy]`)
- `src/commitstory/py.typed` (new, empty file)

**pyproject.toml:**

```toml
[tool.mypy]
strict = true
python_version = "3.10"
packages = ["src/commitstory"]
exclude = ["tests/"]
ignore_missing_imports = true  # gitpython, llama_cpp have no stubs
```

**Fix any mypy violations:** `git_parser.py` has `_commit_to_info(commit)` without type annotation → add `from git import Commit; def _commit_to_info(commit: Commit) -> CommitInfo:`.

**Verification:** `mypy src/commitstory/` — zero errors.

**Commit:** `chore: add mypy strict mode + py.typed marker`

---

## Phase 2: Core DX Improvements

> **Outcome:** Polished CLI experience. Shell completions, filtering, config dedup.

---

### Task 2.1: Add `--version` flag

**Files:** `src/commitstory/main.py`, `src/commitstory/__init__.py`

**Changes:**

```python
# __init__.py
__version__ = "0.1.0"

# main.py — add import:
from . import __version__
# In parser:
parser.add_argument("--version", action="version", version=f"commitstory v{__version__}")
```

**Verification:** `commitstory --version` → `commitstory v0.1.0`

**Commit:** `feat: add --version flag`

---

### Task 2.2: Add `--config` flag

**Files:** `src/commitstory/main.py`, `src/commitstory/config.py`

**Changes:**

```python
# main.py
parser.add_argument("--config", type=str, default="~/.commitstory.json", help="Config file path")

# After args parsing:
config = Config.from_file(args.config)
# Use config values as defaults for CLI args when not explicitly passed
```

**Verification:** `commitstory --config /tmp/test.json` → creates/reads from that path.

**Commit:** `feat: add --config flag for custom config path`

---

### Task 2.3: Configure logging at CLI entry point

**Files:** `src/commitstory/main.py`

**Changes:**

```python
# At top of main(), before any other imports:
import logging
logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

# Add --verbose flag:
parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")
# After parse:
if args.verbose:
    logging.getLogger().setLevel(logging.DEBUG)
```

**Commit:** `feat: configure logging with --verbose flag`

---

### Task 2.4: Deduplicate config parsing — use `Config.from_file()` in dashboard

**Files:** `src/commitstory/dashboard.py`

**Problem:** `scan_config_repos()` duplicates JSON parsing from `Config.from_file()`.

**Fix:**

```python
def scan_config_repos(config_path: str | Path = "~/.commitstory.json") -> list[str]:
    from .config import Config
    cfg = Config.from_file(config_path)
    return cfg.repos
```

**Commit:** `refactor: deduplicate config parsing in dashboard`

---

### Task 2.5: Add `--author` and `--branch` filter flags

**Files:** `src/commitstory/main.py`, `src/commitstory/git_parser.py`

**Changes in main.py:**

```python
parser.add_argument("--author", "-a", type=str, help="Filter by author name (substring match)")
parser.add_argument("--branch", "-b", type=str, help="Git branch to analyze (default: active branch)")
```

**Changes in git_parser.py — `get_commits()`:**

```python
def get_commits(
    repo: Repo,
    days: int = 1,
    branch: str | None = None,
    author: str | None = None,
    limit: int = 200,
) -> list[CommitInfo]:
    # ... existing code ...
    result = []
    for c in commits:
        ci = _commit_to_info(c)
        if author and author.lower() not in ci.author.lower():
            continue
        result.append(ci)
    return list(reversed(result))
```

**Verification:** `commitstory --author "Boss Ver" --branch develop` → only commits matching both filters.

**Commit:** `feat: add --author and --branch filter flags`

---

### Task 2.6: Validate repo path before opening

**Files:** `src/commitstory/git_parser.py`

**Changes:**

```python
def get_repo(repo_path: str | Path) -> Repo:
    p = Path(repo_path).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"Path does not exist: {p}")
    if not (p / ".git").exists():
        raise ValueError(f"Not a git repository (no .git directory): {p}")
    return Repo(str(p), search_parent_directories=True)
```

**Commit:** `fix: validate repo path exists and has .git before opening`

---

### Task 2.7: Fix `get_multi_repo_stats()` hardcoded `days=7` — use param

**Files:** `src/commitstory/git_parser.py`, `src/commitstory/main.py`

**Changes in git_parser.py:**

```python
def get_multi_repo_stats(repo_paths: list[str | Path], days: int = 7) -> dict[str, list[CommitInfo]]:
    result = {}
    for p in repo_paths:
        try:
            repo = get_repo(p)
            name = Path(p).name
            result[name] = get_commits(repo, days=days)
        except Exception:
            continue
    return result
```

**In main.py:** pass `args.days` to `get_multi_repo_stats(repos, days=args.days)`.

**Commit:** `fix: pass days param to get_multi_repo_stats (was hardcoded 7)`

---

### Task 2.8: Move template imports to module level

**Files:** `src/commitstory/summarizer.py`

**Problem:** Template imports inside `summarize()` function — prevents static analysis.

**Fix:** Move to top of file:

```python
from .templates.prompts import DAILY_PROMPT, WEEKLY_PROMPT, DEBT_PROMPT
```

Then in `summarize()`:

```python
prompt_map = {
    "daily": DAILY_PROMPT,
    "weekly": WEEKLY_PROMPT,
    "debt": DEBT_PROMPT,
}
```

**Commit:** `refactor: move template imports to module level`

---

### Task 2.9: Add shell completion

**Files:** `pyproject.toml`

Use argparse's built-in completion support or add a `[project.scripts]` entry for completion generation.

**Simplest approach — document in README how to enable:**

```bash
# bash
eval "$(register-python-argcomplete commitstory)"
# Requires: pip install argcomplete
```

Add `argcomplete` as optional dev dependency. Add to `main.py`:

```python
# At top of main(), before parser.parse_args():
try:
    import argcomplete
    argcomplete.autocomplete(parser)
except ImportError:
    pass
```

**Commit:** `feat: add argcomplete shell completion support`

---

## Phase 3: Polish + Production Readiness

> **Outcome:** Docker, CI, rich output, caching, metadata. Portfolio-grade.

---

### Task 3.1: Add Dockerfile + docker-compose (demo)

**Files:** `Dockerfile` (new), `docker-compose.yml` (new), `.dockerignore` (new)

**Dockerfile:**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml ./
COPY src/ ./src/
RUN pip install --no-cache-dir -e .
ENTRYPOINT ["commitstory"]
```

**docker-compose.yml:**

```yaml
version: "3.8"
services:
  commitstory:
    build: .
    volumes:
      - ${REPO_PATH:-.}:/repo:ro
      - ${CONFIG_PATH:-~/.commitstory.json}:/root/.commitstory.json:ro
    command: --repo /repo --days 7
```

**Commit:** `feat: add Dockerfile and docker-compose`

---

### Task 3.2: Add GitHub Actions CI

**Files:** `.github/workflows/ci.yml` (new)

```yaml
name: CI
on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -e ".[dev]"
      - run: ruff check src/ tests/

  typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -e ".[dev]"
      - run: mypy src/commitstory/

  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e ".[dev]"
      - run: pytest --cov=src/commitstory --cov-report=term --cov-fail-under=80
```

**Commit:** `ci: add GitHub Actions workflow (lint, typecheck, test)`

---

### Task 3.3: Rich progress spinner during LLM inference

**Files:** `pyproject.toml`, `src/commitstory/summarizer.py`

**Changes:** Re-add `rich>=13.0` to dependencies. Add progress indicator:

```python
def summarize(commits, detail_level="daily", model_path=None, n_ctx=4096):
    # ... existing code ...
    
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn
    
    console = Console()
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        task = progress.add_task("Generating narrative with local LLM...", total=None)
        try:
            resp = llm(prompt, max_tokens=1024, temperature=0.3, stop=["<|end|>", "###"])
            progress.remove_task(task)
            return resp["choices"][0]["text"].strip()
        except Exception as e:
            progress.remove_task(task)
            logger.error("LLM inference failed: %s", e)
            return _fallback_summary(commits, detail_level)
```

**Commit:** `feat: add rich progress spinner during LLM inference`

---

### Task 3.4: Add `[project.urls]` and classifiers to `pyproject.toml`

**Files:** `pyproject.toml`

```toml
[project.urls]
Homepage = "https://github.com/verifydream/CommitStory"
Issues = "https://github.com/verifydream/CommitStory/issues"

classifiers = [
    "Development Status :: 3 - Alpha",
    "Environment :: Console",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Software Development :: Version Control :: Git",
]
```

**Commit:** `chore: add project URLs and classifiers`

---

### Task 3.5: Add pre-commit hooks config

**Files:** `.pre-commit-config.yaml` (new)

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        args: [--strict]
        additional_dependencies: [gitpython]
```

**Commit:** `chore: add pre-commit hooks config`

---

### Task 3.6: Add `--template` flag for custom output

**Files:** `src/commitstory/main.py`, `src/commitstory/export.py`

**Changes:**

```python
# main.py
parser.add_argument("--template", "-t", type=str, help="Custom output template file")

# export.py
def to_markdown_template(commits, template_path: str, narrative="", analytics=None) -> str:
    """Apply a custom template file."""
    from pathlib import Path
    tmpl = Path(template_path).read_text()
    # Simple variable substitution
    today = datetime.now().strftime("%Y-%m-%d")
    tmpl = tmpl.replace("{{date}}", today)
    tmpl = tmpl.replace("{{count}}", str(len(commits)))
    tmpl = tmpl.replace("{{narrative}}", narrative)
    # etc.
    return tmpl
```

**Commit:** `feat: add --template flag for custom output templates`

---

### Task 3.7: Add repository-level caching (SHA hash check)

**Files:** `src/commitstory/git_parser.py`, `src/commitstory/main.py`

**Changes:**

```python
# Add to git_parser.py
import hashlib
import json
from pathlib import Path

def get_cache_key(repo: Repo, days: int, branch: str | None) -> str:
    """Generate cache key from latest commit SHA + params."""
    head_sha = repo.head.commit.hexsha
    raw = f"{head_sha}:{days}:{branch or ''}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]

def get_cached(cache_dir: Path, key: str) -> list[CommitInfo] | None:
    """Read cached commit list from disk."""
    cache_file = cache_dir / f"{key}.json"
    if cache_file.exists():
        # TODO: deserialize CommitInfo from JSON cache
    return None
```

Skip deep implementation for now — mark as `ponytail:` future optimization. Store cache in `~/.cache/commitstory/`.

**Commit:** `feat: add basic cache key generation (deserialization deferred)`

---

### Task 3.8: Add `--help` examples

**Files:** `src/commitstory/main.py`

**Changes:** Add `epilog` to argparse:

```python
parser = argparse.ArgumentParser(
    description="CommitStory — git history to readable dev diary",
    epilog="""Examples:
  commitstory                         # Today's commits, daily diary
  commitstory --days 7 --detail weekly # Weekly summary
  commitstory --days 30 --detail debt  # Tech debt analysis
  commitstory --multi                  # All repos from config
  commitstory --format json --output report.json  # JSON export
  commitstory --author "Boss Ver" --branch develop  # Filtered""",
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
```

**Commit:** `docs: add usage examples to --help`

---

## Final Verification

Run after all phases:

```bash
pip install -e ".[dev]"
ruff check src/ tests/          # zero warnings
mypy src/commitstory/           # zero errors
pytest --cov=src/commitstory --cov-report=term --cov-fail-under=80
commitstory --version           # v0.1.0
commitstory --help              # shows examples
```
