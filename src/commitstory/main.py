"""CommitStory — CLI entry point."""
import argparse
from pathlib import Path

from .config import Config
from .git_parser import get_commits, get_repo
from .summarizer import summarize
from .analytics import detect_debt, analyze_frequency
from .dashboard import build_dashboard, scan_config_repos
from .export import to_markdown, to_json, write_to_file


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CommitStory — git history to readable dev diary",
    )
    parser.add_argument("--repo", "-r", type=str, default=".", help="Path to git repo (default: cwd)")
    parser.add_argument("--days", "-d", type=int, default=1, help="Days of history to fetch")
    parser.add_argument("--format", "-f", choices=["markdown", "json"], default="markdown", help="Output format")
    parser.add_argument("--output", "-o", type=str, help="Output file path")
    parser.add_argument("--detail", choices=["daily", "weekly", "debt"], default="daily", help="Narrative detail level")
    parser.add_argument("--model", type=str, help="GGUF model path")
    parser.add_argument("--multi", action="store_true", help="Multi-repo dashboard mode")
    parser.add_argument("--no-llm", action="store_true", help="Force fallback (no LLM)")

    args = parser.parse_args()

    if args.multi:
        repos = scan_config_repos() or [args.repo]
        from .git_parser import get_multi_repo_stats
        data = get_multi_repo_stats(repos)
        dashboard = build_dashboard(data)
        print(dashboard)
        if args.output:
            write_to_file(dashboard, args.output)
        return

    # Single repo
    try:
        repo = get_repo(args.repo)
    except Exception as e:
        print(f"Error: cannot open repo at '{args.repo}': {e}")
        raise SystemExit(1)

    commits = get_commits(repo, days=args.days)

    if not commits:
        print("No commits found in period.")
        return

    narrative = ""
    if not args.no_llm:
        narrative = summarize(commits, detail_level=args.detail, model_path=args.model)

    flags = detect_debt(commits)
    freq = analyze_frequency(commits)
    from .analytics import AnalyticsReport
    analytics = AnalyticsReport(flags=flags, frequency=freq)

    if args.format == "json":
        output = to_json(commits)
    else:
        output = to_markdown(commits, narrative=narrative, analytics=analytics)

    if args.output:
        out_path = write_to_file(output, args.output)
        print(f"Written to {out_path}")
    else:
        print(output)
