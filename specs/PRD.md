# CommitStory — Product Requirements Document

> **Status:** Prototype → MVP → Production-Ready  
> **Stack:** Python CLI (GitPython + llama-cpp-python + Rich)  
> **Target:** pip-installable dev tool for portfolio  
> **Author:** Hermes Agent (review of `verifydream/CommitStory`)  
> **Date:** 2026-08-01

---

## 1. Executive Summary

CommitStory is a Python CLI that reads git commit history and generates readable dev diaries via local LLM (llama.cpp). Core flow works: parse commits → detect patterns → generate narrative → export markdown/JSON. Multi-repo dashboard included.

**Goal:** Polish into a `pip install`-able production CLI with tests, CI, and proper packaging.

---

## 2. Current State Assessment

### 2.1 What Works (Keep)
| Area | Assessment |
|------|-----------|
| Git parsing | GitPython wrapper solid — `CommitInfo` dataclass, conventional commit detection |
| LLM integration | llama-cpp-python with fallback to stats-only mode |
| Analytics | Tech debt detection (refactor chains, fix streaks) + frequency analysis |
| Multi-repo | Dashboard mode via config file `~/.commitstory.json` |
| Export | Markdown + JSON output, file writing with parent dir creation |
| CLI UX | argparse with rich flags: `--days`, `--format`, `--detail`, `--model`, `--output` |

### 2.2 Critical Issues
| # | Issue | Impact | Effort |
|---|-------|--------|--------|
| C1 | Zero tests — no test dir at all | Confidence | M |
| C2 | `llama-cpp-python` as hard dependency — breaks `pip install` for many users | Adoption | L |
| C3 | No CI/CD — no validation on push | Quality | S |
| C4 | No shell completions — bare CLI | DX | S |
| C5 | `git.Repo` opens search_parent_directories — ambiguous | Edge case | XS |
| C6 | No `.gitignore` entries for build artifacts, venv | DX | XS |
| C7 | Rich imported but never used — dead dependency | Cruft | XS |

### 2.3 High-Priority Gaps
| # | Issue |
|---|-------|
| H1 | No `--config` flag to specify custom config path |
| H2 | LLM caching per model path works but no memory management |
| H3 | Analytics only detects 2 debt patterns — limited |
| H4 | No `--since` / `--until` date range (only `--days`) |
| H5 | No `--branch` in CLI (git_parser supports it) |
| H6 | No progress bar for large repos |
| H7 | Markdown export has no "weekly" template — narrative gets appended but weekly format mismatches |

### 2.4 Medium Priority
| # | Issue |
|---|-------|
| M1 | No `commitstory --help` examples |
| M2 | No version flag (`--version`) |
| M3 | `pyproject.toml` missing metadata: `authors`, `license`, `classifiers` |
| M4 | No logging setup — print() only |
| M5 | No shell autocomplete scripts |

---

## 3. MVP Feature Set

### Phase 1 — Critical Fixes
- [ ] Make `llama-cpp-python` optional (`[llm]` extra)
- [ ] Add pytest test suite for git_parser, analytics, export
- [ ] Add GitHub Actions CI (lint + test)
- [ ] Add `--version` flag

### Phase 2 — Core UX
- [ ] Add `--since` / `--until` date range
- [ ] Add `--branch` flag
- [ ] Rich progress bar for large repos
- [ ] Proper `pyproject.toml` metadata (author, license, classifiers)
- [ ] Fix `_LLM_CACHE` memory — add LRU eviction

### Phase 3 — Polish
- [ ] Shell completions (bash, zsh, fish)
- [ ] `--help` examples section
- [ ] Logging with `logging` module
- [ ] More debt patterns in analytics
- [ ] CHANGELOG.md

---

## 4. Architecture Decisions

### ADR-1: llama-cpp-python as optional extra
- **Rationale:** Most users just want stats. LLM is power-user feature.
- **Install:** `pip install commitstory[llm]`

### ADR-2: Pytest over unittest
- **Rationale:** Python ecosystem standard. Better fixtures, parametrize.

### ADR-3: Keep GitPython
- **Rationale:** Battle-tested. No need to shell out to `git` CLI.

---

## 5. Risk Register

| Risk | Mitigation |
|------|-----------|
| llama-cpp-python compile fails | Fallback always works; LLM is optional |
| GitPython API changes | Pin version, CI catches breakage |
| Large repo performance | Progress bar + streaming output |

---

## 6. Success Metrics

| Metric | Target |
|--------|--------|
| `pip install` works | ✅ no errors |
| Test coverage | ≥ 70% |
| CI green | ✅ |
| `commitstory --help` | Clear, examples |
