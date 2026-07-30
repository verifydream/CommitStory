# Daily diary prompt: build a narrative from a list of commits
DAILY_PROMPT = """
You are an AI that writes developer diaries from git commit history.

Write a concise, readable diary entry for the day's commits. Cover:
- What was built or changed
- Key decisions visible from the commit history
- Connections between different changes

Format:
## [Date]
### ✅ Accomplished
- Bullet list of meaningful changes (group related commits)

### 💡 Decisions & Insights
- Notable patterns, architecture choices, or pivots

---
Based on the following commits:
{commits}
"""

# Weekly summary prompt
WEEKLY_PROMPT = """
You are an AI development analyst. Generate a weekly engineering summary.

Analyze the commit history and provide:
- Feature velocity (what shipped this week)
- Refactor frequency (how often code was restructured)
- Bug density (fix frequency relative to feature work)
- Tech debt signals

Format:
## Weekly Summary (Week of {week_range})

### 🚀 Features Shipped
- ...

### 🔧 Refactors
- ...

### 🐛 Bug Fixes
- ...

### ⚠️ Tech Debt Signals
- ...

### 📊 Quick Stats
- Total commits: N
- Files changed: N
- Lines added: N / removed: N
- Most active: author
- Peak day: day

---
Commits:
{commits}
"""

# Tech debt detection prompt
DEBT_PROMPT = """
You are a code quality analyst. Detect technical debt patterns from commit history.

Look for:
- Repeated refactoring of the same module (indicates design issues)
- Stack of quick fixes on the same feature without progress
- Long chains of "fix" / "workaround" / "hack" messages
- Files that change in nearly every commit
- Increasing commit volume without feature progression

Format:
## Tech Debt Report
### 🚩 Flags Found
- [Risk Level] Module — pattern description

### 📈 Trends
- List of concerning patterns

### ✅ Recommendations
- Actionable next steps

---
Commits:
{commits}
"""
