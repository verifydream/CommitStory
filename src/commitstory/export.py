"""Export — markdown and JSON output."""
import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .git_parser import CommitInfo
    from .analytics import AnalyticsReport


def to_markdown(
    commits: list["CommitInfo"],
    narrative: str = "",
    analytics: "AnalyticsReport | None" = None,
) -> str:
    """Export commit history + narrative as markdown."""
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [
        f"# CommitStory — {today}",
        "",
        f"**Total commits:** {len(commits)}",
        "",
    ]

    if narrative:
        lines.append(narrative)
        lines.append("")

    if analytics:
        lines.append("## 📊 Analytics")
        if analytics.frequency:
            f = analytics.frequency
            lines.extend([
                f"- **Peak commit hour:** {f.peak_hour}:00",
                f"- **Peak day:** {f.peak_day}",
                f"- **Streak:** {f.streak_days} days",
                f"- **Velocity:** {f.velocity} commits/day",
                "",
            ])
        if analytics.flags:
            lines.append("### 🚩 Tech Debt Flags")
            for flag in analytics.flags:
                lines.append(f"- [{flag.severity.upper()}] {flag.module}: {flag.description}")
            lines.append("")

    lines.append("## Commit Log")
    for c in commits:
        ct = f"[{c.conventional_type}] " if c.conventional_type else ""
        lines.append(f"- {c.short_sha} {ct}{c.summary}")
        if c.total_additions or c.total_deletions:
            lines.append(f"  +{c.total_additions} / -{c.total_deletions} — {', '.join(c.files_changed[:5])}")

    return "\n".join(lines)


def to_json(commits: list["CommitInfo"]) -> str:
    """Export as JSON."""
    data = {
        "generated_at": datetime.now().isoformat(),
        "total_commits": len(commits),
        "commits": [
            {
                "sha": c.sha,
                "short_sha": c.short_sha,
                "summary": c.summary,
                "message": c.message,
                "author": c.author,
                "date": c.date.isoformat(),
                "additions": c.total_additions,
                "deletions": c.total_deletions,
                "files": c.files_changed,
                "type": c.conventional_type,
                "is_merge": c.is_merge,
            }
            for c in commits
        ],
    }
    return json.dumps(data, indent=2)


def write_to_file(content: str, output_path: str | Path) -> Path:
    """Write content to file, return path."""
    p = Path(output_path).expanduser()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return p
