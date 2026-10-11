"""Discover mode: live repo search on GitHub, ranked by recent activity."""
from datetime import datetime, timedelta, timezone

from core import github

LANGS = {"Python": "Python", "JavaScript": "JavaScript", "TypeScript": "TypeScript", "Java": "Java", "C": "C",
         "C++": '"C++"', "C#": '"C#"', "Go": "Go", "Rust": "Rust", "PHP": "PHP", "Ruby": "Ruby", "Swift": "Swift",
         "Kotlin": "Kotlin", "Dart": "Dart", "R": "R", "Shell": "Shell", "HTML/CSS": "HTML"}
TOPICS = {"SQL": "sql", "Machine Learning": "machine-learning", "Web": "webdev", "Mobile": "mobile",
          "Data Science": "data-science", "DevOps": "devops", "Games": "gamedev", "Docs": "documentation",
          "Security": "security"}
SKILLS = list(LANGS) + list(TOPICS)
GOALS = ["Easy bug fixes", "Easy problem solving", "Good for resume"]
MAX_SKILLS = 3


def health_label(days):
    """Active / Slow / Inactive from days since the last push."""
    return "Active" if days <= 30 else "Slow" if days <= 60 else "Inactive"


def build_query(skill, goal, hacktoberfest, relaxed=False):
    """Build one GitHub repository-search query string."""
    since = (datetime.now(timezone.utc) - timedelta(days=90)).strftime("%Y-%m-%d")
    stars = "300..20000" if goal == "Good for resume" else "50..20000"
    q = [f"stars:{stars}", f"pushed:>{since}", "archived:false"]
    if hacktoberfest:
        q.append("topic:hacktoberfest")
    if skill in LANGS:
        q.append(f"language:{LANGS[skill]}")
    elif skill in TOPICS:
        q.append(f"topic:{TOPICS[skill]}")
    q.append("good-first-issues:>0")
    if goal == "Easy problem solving" and not relaxed:
        q.append("topic:algorithms")
    return " ".join(q)


def search(skills, goal, hacktoberfest):
    """Return {'repos': [...], 'note': str}. Raises GitHubError on API problems."""
    chosen = list(skills)
    note = f"Only the first {MAX_SKILLS} skills were used." if len(chosen) > MAX_SKILLS else ""
    skills = chosen[:MAX_SKILLS] or [None]
    seen, repos = set(), []
    for s in skills:
        sort = "stars" if goal == "Good for resume" else "updated"
        params = {"sort": sort, "order": "desc", "per_page": 100}
        items = github.get("/search/repositories", {**params, "q": build_query(s, goal, hacktoberfest)}).get("items", [])
        if not items and goal == "Easy problem solving":
            items = github.get("/search/repositories", {**params, "q": build_query(s, goal, hacktoberfest, True)}).get("items", [])
            note = (note + " No exact matches, so the problem-solving filter was relaxed.").strip()
        for r in items:
            if r["full_name"] in seen:
                continue
            seen.add(r["full_name"])
            days = github.days_since(r.get("pushed_at"))
            repos.append({"full_name": r["full_name"], "url": r["html_url"], "stars": r["stargazers_count"],
                          "language": r.get("language") or "-", "description": r.get("description") or "",
                          "open_issues": r.get("open_issues_count", 0), "days": days, "health": health_label(days)})
    repos.sort(key=lambda r: (r["days"], -r["stars"]))
    return {"repos": repos, "note": note}
