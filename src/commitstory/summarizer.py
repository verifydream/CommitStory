"""Summarizer — commits → narrative via local LLM."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .git_parser import CommitInfo

logger = logging.getLogger(__name__)

try:
    from llama_cpp import Llama

    _LLAMA_AVAILABLE = True
except ImportError:
    _LLAMA_AVAILABLE = False


_LLM_CACHE: dict[str, "Llama"] = {}


def _format_commits(commits: list[CommitInfo]) -> str:
    """Format commits for LLM input."""
    lines = []
    for c in commits:
        files = ", ".join(c.files_changed[:10])
        ct = f"[{c.conventional_type}] " if c.conventional_type else ""
        extra = f" ({c.total_additions}+, {c.total_deletions}-)" if c.total_additions or c.total_deletions else ""
        lines.append(f"  - {c.short_sha} {ct}{c.summary}{extra} — files: {files}")
    return "\n".join(lines)


def _get_llm(model_path: str | None, n_ctx: int = 4096) -> "Llama | None":
    """Get or create an LLM instance (cached)."""
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
    return _LLM_CACHE[key]


def summarize(
    commits: list[CommitInfo],
    detail_level: str = "detailed",
    model_path: str | None = None,
    n_ctx: int = 4096,
) -> str:
    """Generate narrative from commits using local LLM."""
    from .templates.prompts import (
        DAILY_PROMPT as _DAILY,
        WEEKLY_PROMPT as _WEEKLY,
        DEBT_PROMPT as _DEBT,
    )

    prompt_map = {
        "daily": _DAILY,
        "weekly": _WEEKLY,
        "debt": _DEBT,
    }

    prompt_key = detail_level
    if prompt_key not in prompt_map:
        prompt_key = "daily"

    template = prompt_map[prompt_key]
    formatted = _format_commits(commits)
    if not formatted.strip():
        return "_No commits in this period._"

    prompt = template.replace("{commits}", formatted)

    llm = _get_llm(model_path, n_ctx)
    if llm is None:
        # Fallback: structured summary without LLM
        return _fallback_summary(commits, detail_level)

    try:
        resp = llm(prompt, max_tokens=1024, temperature=0.3, stop=["<|end|>", "###"])
        return resp["choices"][0]["text"].strip()
    except Exception as e:
        logger.error("LLM inference failed: %s", e)
        return _fallback_summary(commits, detail_level)


def _fallback_summary(commits: list[CommitInfo], detail_level: str) -> str:
    """Fallback: basic stats-based summary when LLM unavailable."""
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

    lines = [
        f"## {today} — Dev Diary ({len(commits)} commits)",
        "",
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
