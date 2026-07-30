"""Git repository parsing — commits, diffs, stats."""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

from git import Repo, GitCommandError


@dataclass
class FileStats:
    path: str
    additions: int
    deletions: int


@dataclass
class CommitInfo:
    sha: str
    short_sha: str
    message: str
    summary: str
    author: str
    date: datetime
    files_changed: list[str] = field(default_factory=list)
    file_stats: list[FileStats] = field(default_factory=list)
    total_additions: int = 0
    total_deletions: int = 0
    is_merge: bool = False
    conventional_type: str | None = None  # feat, fix, refactor, etc.


def parse_conventional_commit(message: str) -> str | None:
    """Detect conventional commit type from message prefix."""
    first_line = message.split("\n", 1)[0].strip()
    for prefix in ("feat", "fix", "refactor", "docs", "test", "chore", "perf", "ci", "build", "style"):
        if first_line.lower().startswith(f"{prefix}:") or first_line.lower().startswith(f"{prefix}("):
            return prefix
    return None


def get_repo(repo_path: str | Path) -> Repo:
    """Open a git repository."""
    return Repo(repo_path, search_parent_directories=True)


def get_commits(
    repo: Repo,
    days: int = 1,
    branch: str | None = None,
    limit: int = 200,
) -> list[CommitInfo]:
    """Get commits from the last N days."""
    since = datetime.now() - timedelta(days=days)
    ref = branch or repo.active_branch.name if not repo.head.is_detached else repo.head.commit.hexsha

    try:
        commits = list(repo.iter_commits(ref, since=since, max_count=limit))
    except GitCommandError:
        return []

    result = []
    for c in commits:
        ci = _commit_to_info(c)
        result.append(ci)
    return list(reversed(result))  # oldest first


def _commit_to_info(commit) -> CommitInfo:
    """Convert a git.Commit to CommitInfo."""
    file_stats = []
    total_add = 0
    total_del = 0
    files_changed = []
    try:
        diffs = commit.stats
        files_changed = list(diffs.files.keys())
        for fpath, stat in diffs.files.items():
            a = stat.get("lines_inserted", 0) or 0
            d = stat.get("lines_deleted", 0) or 0
            file_stats.append(FileStats(path=fpath, additions=a, deletions=d))
            total_add += a
            total_del += d
    except GitCommandError:
        pass  # shallow clone or missing objects — skip stats

    msg = commit.message.strip()
    summary = msg.split("\n", 1)[0] if "\n" in msg else msg
    return CommitInfo(
        sha=commit.hexsha,
        short_sha=commit.hexsha[:8],
        message=msg,
        summary=summary,
        author=str(commit.author),
        date=datetime.fromtimestamp(commit.committed_date),
        files_changed=files_changed,
        file_stats=file_stats,
        total_additions=total_add,
        total_deletions=total_del,
        is_merge=bool(commit.parents and len(commit.parents) > 1),
        conventional_type=parse_conventional_commit(msg),
    )


def get_multi_repo_stats(repo_paths: list[str | Path]) -> dict[str, list[CommitInfo]]:
    """Get commits from multiple repos."""
    result = {}
    for p in repo_paths:
        try:
            repo = get_repo(p)
            name = Path(p).name
            result[name] = get_commits(repo, days=7)
        except Exception:
            continue
    return result
