# CommitStory — Task Checklist

> Track completion status per task. ✅ = done, 🔴 = not started, 🟡 = in progress, ⚠️ = blocked

---

## Phase 1: Critical Fixes + Test Suite

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1.1 | Fix `{week_range}` placeholder bug in DEBT_PROMPT/WEEKLY_PROMPT | 🔴 | |
| 1.2 | Fix `_fallback_summary()` to respect `detail_level` | 🔴 | |
| 1.3 | Fix `detect_debt()` off-by-one on final fix streak | 🔴 | |
| 1.4 | Add LRU-bounded LLM cache (max 2 models) | 🔴 | |
| 1.5 | Remove unused `rich` dependency | 🔴 | |
| 1.6 | Add pytest test suite with ≥ 80% coverage | 🔴 | |
| 1.7 | Add `mypy --strict` + `py.typed` marker | 🔴 | |

**Phase 1 Gate:** `pytest` all green, `mypy` zero errors, `ruff` zero warnings, `pip install -e .` works.

---

## Phase 2: Core DX Improvements

| # | Task | Status | Notes |
|---|------|--------|-------|
| 2.1 | Add `--version` flag | 🔴 | |
| 2.2 | Add `--config` flag | 🔴 | |
| 2.3 | Configure `logging.basicConfig()` + `--verbose` | 🔴 | |
| 2.4 | Deduplicate config parsing in `dashboard.py` | 🔴 | |
| 2.5 | Add `--author` and `--branch` filter flags | 🔴 | |
| 2.6 | Validate repo path before opening | 🔴 | |
| 2.7 | Fix `get_multi_repo_stats()` hardcoded `days=7` | 🔴 | |
| 2.8 | Move template imports to module level | 🔴 | |
| 2.9 | Add shell completion (argcomplete) | 🔴 | |

**Phase 2 Gate:** All CLI flags work. `--help` shows complete usage. `--version` returns correct version.

---

## Phase 3: Polish + Production Readiness

| # | Task | Status | Notes |
|---|------|--------|-------|
| 3.1 | Add Dockerfile + docker-compose | 🔴 | |
| 3.2 | Add GitHub Actions CI (lint, typecheck, test matrix) | 🔴 | |
| 3.3 | Rich progress spinner during LLM inference | 🔴 | |
| 3.4 | Add `[project.urls]` + classifiers to pyproject.toml | 🔴 | |
| 3.5 | Add pre-commit hooks config | 🔴 | |
| 3.6 | Add `--template` flag for custom output | 🔴 | |
| 3.7 | Add repository-level cache key generation | 🔴 | |
| 3.8 | Add usage examples to `--help` | 🔴 | |

**Phase 3 Gate:** `docker compose up` works. CI green. `pip install` pulls from PyPI or local. All flags documented.

---

## Final Verification Checklist

- [ ] `pip install -e ".[dev]"` — no errors
- [ ] `ruff check src/ tests/` — zero warnings
- [ ] `mypy src/commitstory/` — zero errors
- [ ] `pytest --cov=src/commitstory --cov-fail-under=80` — all passing
- [ ] `commitstory --version` — shows correct version
- [ ] `commitstory --help` — shows examples + all flags
- [ ] `docker compose up` — runs without errors (demo mode)
- [ ] Test on a real git repo: `commitstory --days 7`
- [ ] Test fallback mode: `commitstory --no-llm --days 7`
- [ ] Test multi-repo: `commitstory --multi --days 7`

---

## Known Technical Debt (Post-MVP)

| Item | Priority | Effort |
|------|----------|--------|
| Full cache deserialization (CommitInfo → JSON → CommitInfo) | Medium | M |
| Performance benchmark on 10K+ commit repos | Low | M |
| Streaming iterator for large repos (memory) | Low | M |
| LLM prompt tuning for better narrative quality | Low | M |
| `--model` auto-download (pull from HuggingFace) | Low | L |
| Web dashboard / Live reload mode | Low | L |
| Git hook integration (post-commit auto diary) | Low | M |
| Support for non-conventional commit projects | Low | S |
