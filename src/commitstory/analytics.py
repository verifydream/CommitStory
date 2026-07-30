"""Tech debt detection and commit frequency analysis."""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .git_parser import CommitInfo


@dataclass
class DebtFlag:
    severity: str  # low | medium | high
    module: str
    description: str
    suggestion: str

@dataclass
class FrequencyReport:
    peak_hour: int
    peak_day: str
    commits_per_day: dict[str, int]
    streak_days: int
    velocity: float  # avg commits/day

@dataclass
class AnalyticsReport:
    flags: list[DebtFlag]
    frequency: FrequencyReport | None = None
    raw: dict = field(default_factory=dict)


def detect_debt(commits: list[CommitInfo]) -> list[DebtFlag]:
    """Detect tech debt patterns from commits."""
    flags = []
    module_commits: dict[str, list[CommitInfo]] = defaultdict(list)

    for c in commits:
        for f in c.files_changed:
            module_commits[f].append(c)

    # Repeated refactors: a module with many refactor commits
    refactor_counts: Counter[str] = Counter()
    for f, cs in module_commits.items():
        refactors = [c for c in cs if c.conventional_type == "refactor"]
        if len(refactors) >= 3:
            refactor_counts[f] = len(refactors)

    for module, count in refactor_counts.most_common(5):
        flags.append(DebtFlag(
            severity="high" if count >= 5 else "medium",
            module=module,
            description=f"{count}x refactor commits — module may need redesign",
            suggestion="Consider extracting stable API or rewriting module",
        ))

    # Fix chains: multiple fix commits in a row
    fix_streaks = 0
    for i, c in enumerate(commits):
        if c.conventional_type == "fix":
            fix_streaks += 1
        else:
            if fix_streaks >= 3:
                flags.append(DebtFlag(
                    severity="medium",
                    module="(general)",
                    description=f"Chain of {fix_streaks} consecutive fix commits — possible instability",
                    suggestion="Add regression tests before further fixes",
                ))
            fix_streaks = 0

    return flags


def analyze_frequency(commits: list[CommitInfo]) -> FrequencyReport:
    """Analyze commit frequency patterns."""
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    commits_per_day: dict[str, int] = defaultdict(int)
    hour_counts: Counter[int] = Counter()

    for c in commits:
        d = c.date.strftime("%A")
        commits_per_day[d] += 1
        hour_counts[c.date.hour] += 1

    peak_hour = hour_counts.most_common(1)[0][0] if hour_counts else 0
    peak_day = max(commits_per_day, key=commits_per_day.get) if commits_per_day else "N/A"
    streak = _calc_streak(commits)
    velocity = round(len(commits) / len(commits_per_day), 1) if commits_per_day else 0.0

    return FrequencyReport(
        peak_hour=peak_hour,
        peak_day=peak_day,
        commits_per_day=dict(commits_per_day),
        streak_days=streak,
        velocity=velocity,
    )


def _calc_streak(commits: list[CommitInfo]) -> int:
    """Calculate consecutive day streak (from most recent)."""
    if not commits:
        return 0
    seen_dates = sorted({c.date.date() for c in commits}, reverse=True)
    streak = 0
    from datetime import timedelta
    for i, d in enumerate(seen_dates):
        if i == 0:
            streak = 1
        elif (seen_dates[i - 1] - d).days == 1:
            streak += 1
        else:
            break
    return streak
