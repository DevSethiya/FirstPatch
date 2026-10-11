"""Fit Score rules. The app COMPUTES these facts; the AI never decides them."""
import re

from core import github

GOOD_LABELS = ("good first issue", "good-first-issue", "beginner", "easy", "help wanted",
               "documentation", "hacktoberfest", "first-timers-only")
CLAIM_RE = re.compile(r"can i (work|take|try|pick)|i'?ll take|i will take|i'?d like to (work|take)|"
                      r"working on (this|it)|assign (this )?to me|i want to work|let me (work|take)", re.I)
SKILL_WORDS = {
    "Python": ["python", ".py", "pip", "django", "flask"],
    "JavaScript": ["javascript", ".js", "node", "npm", "react"],
    "TypeScript": ["typescript", ".ts", ".tsx"],
    "Java": ["java", ".java", "maven", "gradle"], "C": [".c", ".h"], "C++": ["c++", ".cpp"],
    "C#": ["c#", ".cs", "dotnet", ".net"], "Go": ["golang", ".go"], "Rust": ["rust", ".rs", "cargo"],
    "PHP": ["php"], "Ruby": ["ruby", ".rb", "rails"], "Swift": ["swift"], "Kotlin": ["kotlin", ".kt"],
    "Dart": ["dart", "flutter"], "R": [" r ", ".r"], "SQL": ["sql", "query", "database"],
    "Shell": ["bash", "shell", ".sh"], "HTML/CSS": ["html", "css", "style", "layout"],
    "Machine Learning": ["machine learning", "model", "pytorch", "tensorflow", "ml"],
    "Web": ["web", "frontend", "backend", "website", "api"], "Mobile": ["android", "ios", "mobile"],
    "Data Science": ["data", "pandas", "notebook", "dataset"], "DevOps": ["docker", "ci", "deploy", "kubernetes"],
    "Games": ["game", "unity", "godot"], "Docs": ["docs", "documentation", "readme", "typo"],
    "Security": ["security", "vulnerability", "auth"],
}


def label_names(issue):
    """Lower-case label names of an issue."""
    return [l.get("name", "").lower() for l in issue.get("labels", []) if isinstance(l, dict)]


def matches_skills(text, labels, skills):
    """True if the issue text or labels mention any chosen skill."""
    blob = f" {text} {' '.join(labels)} ".lower()
    return any(w in blob for s in skills for w in SKILL_WORDS.get(s, [s.lower()]))


def score_issue(issue, skills):
    """Apply the 5 Fit Score rules. Returns (score, list of reasons)."""
    labels = label_names(issue)
    text = f"{issue.get('title', '')} {issue.get('body') or ''}"
    score, why = 0, []
    if any(g in l for l in labels for g in GOOD_LABELS):
        score += 30; why.append("beginner-friendly label (+30)")
    if not issue.get("assignee"):
        score += 25; why.append("nobody assigned (+25)")
    score += 20; why.append("no open PR mentions it (+20)")  # caller skips issues that have one
    if github.days_since(issue.get("updated_at")) <= 60:
        score += 15; why.append("updated in the last 60 days (+15)")
    if skills and matches_skills(text, labels, skills):
        score += 10; why.append("matches your skills (+10)")
    return score, why


def pr_mentions(prs):
    """Set of issue numbers mentioned (like #123) in open PR titles/bodies."""
    nums = set()
    for p in prs:
        nums.update(int(n) for n in re.findall(r"#(\d+)", f"{p.get('title', '')} {p.get('body') or ''}"))
    return nums


def rank_issues(issues, prs, skills):
    """Split issues into (candidates sorted by score, skipped with reasons)."""
    mentioned = pr_mentions(prs)
    cands, skipped = [], []
    for i in issues:
        n = i["number"]
        reason = ("assigned to " + i["assignee"]["login"]) if i.get("assignee") else \
            "locked" if i.get("locked") else "an open PR already mentions it" if n in mentioned else None
        if reason:
            skipped.append({"number": n, "title": i["title"], "url": i["html_url"], "reason": reason})
            continue
        score, why = score_issue(i, skills)
        cands.append({"number": n, "title": i["title"], "url": i["html_url"], "labels": label_names(i),
                      "body": (i.get("body") or "")[:1500], "score": score, "why_score": why,
                      "status": "Available", "updated_days": github.days_since(i.get("updated_at")),
                      "comments": i.get("comments", 0)})
    cands.sort(key=lambda c: -c["score"])
    return cands, skipped


def check_claimed(full, cands, limit=8):
    """Mark issues whose comments sound like someone already claimed them (checks the top few only)."""
    for c in cands[:limit]:
        if not c["comments"]:
            continue
        try:
            comments = github.get(f"/repos/{full}/issues/{c['number']}/comments", {"per_page": 30})
        except github.GitHubError as e:
            if e.kind == "ratelimit":
                raise
            continue
        if any(CLAIM_RE.search(cm.get("body") or "") for cm in comments):
            c["status"] = "Possibly claimed"
    cands.sort(key=lambda c: (c["status"] != "Available", -c["score"]))
    return cands
