"""Multi-repo dashboard — aggregate commits across repos."""
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .git_parser import CommitInfo


def scan_config_repos(config_path: str | Path = "~/.commitstory.json") -> list[str]:
    """Read repo list from config."""
    import json
    p = Path(config_path).expanduser()
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text())
        return data.get("repos", [])
    except Exception:
        return []


def build_dashboard(
    repo_data: dict[str, list["CommitInfo"]],
) -> str:
    """Build a text dashboard from multiple repos."""
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")

    lines = [
        f"# CommitStory Dashboard — {today}",
        f"**Repos tracked:** {len(repo_data)}",
        "",
    ]

    grand_total = 0
    for repo_name, commits in sorted(repo_data.items()):
        total = len(commits)
        grand_total += total
        add = sum(c.total_additions for c in commits)
        dele = sum(c.total_deletions for c in commits)
        files = len(set(f for c in commits for f in c.files_changed))
        authors = set(c.author for c in commits)
        lines.extend([
            f"## {repo_name}",
            f"- {total} commits | +{add} / -{dele} lines | {files} files | {len(authors)} contributors",
            "",
        ])

    lines.insert(2, f"**Total commits:** {grand_total}")
    return "\n".join(lines)
