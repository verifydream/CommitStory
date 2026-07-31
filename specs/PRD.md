# CommitStory — Product Requirements Document

> **Status:** Prototype Review → MVP → Production-Ready  
> **Target:** Portfolio-grade self-hosted CLI dev diary generator  
> **Author:** Hermes Agent (review of `verifydream/CommitStory` commit `4be1a35`)  
> **Date:** 2026-08-01

---

## 1. Executive Summary

CommitStory is a Python CLI tool that reads local git commit history and generates a readable dev diary — what was built, bugs fixed, decisions made, tech debt detected. Powered by local LLM via llama.cpp (GGUF), with a stats-only fallback when no model is available. The current prototype (v0.1.0) has a clean architecture (~550 LOC, 10 source files, dataclass-driven) but is a single-commit prototype with zero tests, no CI, and several correctness bugs.

**Goal:** Transform into a polished, pip-installable, well-tested CLI tool suitable for portfolio showcase and real-world daily use.

---

## 2. Current State Assessment

### 2.1 What Works Well (Keep)

| Area | Assessment |
|------|-----------|
| Architecture | Clean separation: `git_parser` → `summarizer` → `analytics` → `export` — single-responsibility modules |
| Data model | Dataclasses (`CommitInfo`, `FileStats`, `DebtFlag`, `FrequencyReport`, `AnalyticsReport`) — typed, composable |
| Conventional commits | Parses `feat:`, `fix:`, `refactor:`, etc. correctly |
| LLM integration | Optional llama.cpp with fallback — no hard dependency |
| Export | Both markdown and JSON output with file write |
| Dependency count | Only 3 runtime deps (`gitpython`, `rich`, `llama-cpp-python`) — lean |
| Multi-repo | Dashboard mode aggregates across projects |
| Tech debt detection | Heuristic-based: repeated refactors, fix chains |
| Config persistence | JSON config file at `~/.commitstory.json` |

### 2.2 Critical Issues (Must Fix Before MVP)

| # | Issue | Impact | Effort |
|---|-------|--------|--------|
| C1 | `DEBT_PROMPT` template has `{week_range}` placeholder that `summarize()` never fills — LLM gets literal `{week_range}` text in prompt | **Correctness** | XS |
| C2 | `_fallback_summary()` ignores `detail_level` — always produces daily-format output even for `weekly`/`debt` | **Correctness** | S |
| C3 | `detect_debt()` final fix_streak not appended if last commits form a streak — off-by-one | **Correctness** | XS |
| C4 | Global `_LLM_CACHE` dict leaks memory — no LRU eviction, no max size | **Resource** | S |
| C5 | `rich` listed as dependency but never imported anywhere — dead weight | **DX** | XS |
| C6 | Zero tests — no pytest, no coverage, nothing | **Quality** | M |
| C7 | No type checker enforcement — `mypy` not in dev deps, no `py.typed` marker | **Quality** | S |

### 2.3 High-Priority Gaps (Should Fix for MVP)

| # | Issue | Impact |
|---|-------|--------|
| H1 | No `--version` flag — can't verify installed version |
| H2 | No `--config` flag — hardcoded `~/.commitstory.json` path |
| H3 | No logging configuration — `logger.error` calls go nowhere unless user configures logging |
| H4 | `scan_config_repos()` duplicates JSON-parsing logic from `Config.from_file()` |
| H5 | `write_to_file()` doesn't specify encoding — platform-dependent behavior |
| H6 | `get_repo()` accepts non-git directories silently (GitPython will throw confusing error) |
| H7 | `summarize()` imports templates inside function — ugly, prevents static analysis |
| H8 | No shell completion (bash/zsh/fish) |
| H9 | No `py.typed` marker — type checkers can't verify downstream usage |
| H10 | `get_multi_repo_stats()` hardcoded `days=7` — ignores CLI args |

### 2.4 Medium-Priority Improvements (For Production)

| # | Issue |
|---|-------|
| M1 | No Docker / `Dockerfile` |
| M2 | No CI/CD (GitHub Actions) |
| M3 | No man page or `--help` examples |
| M4 | No progress spinner / rich live display during LLM inference |
| M5 | No caching for repeated queries on same repo |
| M6 | No `--author` / `--branch` filter flags |
| M7 | No output templating (custom markdown templates) |
| M8 | No `pre-commit` hooks config |
| M9 | `pyproject.toml` missing `[project.urls]` (homepage, issues) |
| M10 | No performance benchmark for large repos |

---

## 3. Target Personas

1. **Solo Developer** — tracks their own progress across 1–5 repos, generates daily standup notes
2. **Tech Lead / EM** — aggregates team velocity across multiple repos, spots tech debt patterns
3. **Portfolio Reviewer** — evaluates code quality, architecture, and production readiness
4. **Open-source Maintainer** — generates changelogs and release notes from conventional commits

---

## 4. MVP Feature Set (What Ships)

### 4.1 Must Have (Phase 1 — Fix Critical)

- [x] Fix `DEBT_PROMPT` `{week_range}` bug — fill or remove placeholder
- [x] Fix `_fallback_summary()` to respect `detail_level`
- [x] Fix `detect_debt()` off-by-one on final streak
- [x] Add LRU-bounded LLM cache
- [x] Remove unused `rich` dependency or actually use it
- [x] Add pytest test suite (≥ 80% coverage)
- [x] Add `mypy` strict mode + `py.typed`

### 4.2 Should Have (Phase 2 — Core DX)

- [x] `--version` flag
- [x] `--config` flag
- [x] Configure `logging.basicConfig()` at CLI entry
- [x] Deduplicate config parsing — single `Config` class
- [x] `--author` and `--branch` filter flags
- [x] Validate repo path before opening
- [x] Fix `get_multi_repo_stats()` hardcoded days
- [x] Move template imports to module level (lazy via TYPE_CHECKING)
- [x] Add shell completion (argparse built-in or click)

### 4.3 Nice to Have (Phase 3 — Polish)

- [x] Dockerfile + docker-compose (for demo, though CLI tool)
- [x] GitHub Actions CI (lint, test, typecheck, build)
- [x] Rich progress spinner during LLM inference
- [x] `pyproject.toml` metadata (urls, classifiers)
- [x] pre-commit hooks config
- [x] Output templating with `--template`
- [x] Repository-level caching (hash commits → skip re-analysis)
- [x] `--help` examples in argparse

---

## 5. Non-Goals (Explicitly Out of Scope)

- Web UI / dashboard (CLI-only tool)
- GitHub/GitLab API integration (local repos only)
- Real-time git hooks / daemon mode
- Database storage (stateless, reads git objects each run)
- Multi-user / team features
- AI-powered PR descriptions
- SaaS / hosted version
- Plugin system

---

## 6. Success Metrics

| Metric | Target |
|--------|--------|
| Test coverage | ≥ 80% |
| `mypy --strict` errors | 0 |
| `ruff check` warnings | 0 |
| CLI startup time (no LLM) | < 200ms |
| LLM inference (100 commits) | < 5s on CPU |
| pip install time | < 10s |
| Wheel size | < 50KB |

---

## 7. Competitive Landscape

| Tool | Strength | Weakness |
|------|----------|----------|
| `git log` | Built-in, fast | Raw data, no narrative |
| `gitinspector` | Stats + charts | Dead project, no LLM |
| `git-quick-stats` | Shell-based, simple | No LLM, no narrative |
| `commitizen` | Conventional commits | Changelog only, no analysis |
| **CommitStory** | LLM narrative, tech debt detection, multi-repo, fully offline | Currently prototype |

**Differentiator:** The only CLI tool combining local LLM narrative generation with heuristics-based tech debt detection, all offline via GGUF models.

---

## 8. Architecture Decision Records (ADR)

### ADR-1: Keep Python + setuptools (not Poetry/PDM/Hatch)
- **Rationale:** Minimal dep footprint (3 runtime deps), works everywhere. Poetry adds complexity for a 550-line tool.
- **Revisit when:** Project exceeds 2000 LOC or needs complex dependency resolution.

### ADR-2: Keep llama-cpp-python as optional dependency
- **Rationale:** Many users won't have a GGUF model. Stats-only fallback is sufficient for basic use.
- **Implementation:** Keep `try/except ImportError` pattern. Add `pip install commitstory[llm]` extra.

### ADR-3: Use pytest (not unittest)
- **Rationale:** pytest is de facto standard. Fixtures, parametrize, tmp_path built-in.
- **Plugins:** `pytest-cov` for coverage, `pytest-mock` for mocking git.

### ADR-4: Keep GitPython (not dulwich/pygit2)
- **Rationale:** Most ergonomic API for commit iteration. Trade-off: slower on massive repos (>100K commits).
- **Revisit when:** Performance complaints on large repos.

### ADR-5: Single-file templates (not Jinja2)
- **Rationale:** 3 prompt templates, 85 lines total. Jinja2 is overkill.
- **Upgrade when:** User-customizable templates with conditionals/loops needed.

---

## 9. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| GGUF model not found | Medium | Low | Graceful fallback to stats-only, clear error message |
| GitPython fails on shallow clones | Medium | Medium | Catch `GitCommandError`, skip stats, still include commit metadata |
| Large repo (>10K commits) memory blow-up | Low | Medium | Add `--limit` flag (already exists), streaming iterator |
| Breaking changes in llama-cpp-python API | Low | Medium | Pin major version, test matrix in CI |
| `rich` dependency removal breaks users | Low | Low | It's unused — safe to remove |

---

## 10. Timeline (Estimated)

| Phase | Content | Est. Effort |
|-------|---------|-------------|
| Phase 1 | Critical fixes + test suite | 2–3 days |
| Phase 2 | Core DX improvements | 2–3 days |
| Phase 3 | Polish + CI | 1–2 days |
| **Total** | **Prototype → Production-Ready** | **5–8 days** |

---

## 11. References

- [GitPython Docs](https://gitpython.readthedocs.io/)
- [llama-cpp-python](https://github.com/abetlen/llama-cpp-python)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Python Packaging Guide](https://packaging.python.org/en/latest/)
