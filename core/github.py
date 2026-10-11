"""GitHub API helpers. No Streamlit here, so this file is easy to test."""
import os
import re
import time
from datetime import datetime, timezone
from urllib.parse import quote

import requests

API = "https://api.github.com"
CACHE_SECONDS = 600
_CACHE = {}  # (path, params, raw, token) -> (time, data)


class GitHubError(Exception):
    """kind is 'notfound', 'ratelimit' or 'other'."""

    def __init__(self, kind, message=""):
        super().__init__(message)
        self.kind = kind


def friendly_error(e):
    """Turn a GitHubError into a message a beginner understands."""
    if e.kind == "notfound":
        return "Repo not found. Check the spelling (private repos can't be read)."
    if e.kind == "ratelimit":
        return ("GitHub rate limit reached (only 60 requests per hour without a token). "
                "Add a free GITHUB_TOKEN to your .env file (no permissions needed) "
                "or try again in a few minutes.")
    return f"GitHub problem: {e}"


def get(path, params=None, raw=False):
    """Call the GitHub API (cached for 10 minutes). Returns JSON, or text if raw=True."""
    token = os.getenv("GITHUB_TOKEN", "").strip()
    key = (path, tuple(sorted((params or {}).items())), raw, token)
    hit = _CACHE.get(key)
    if hit and time.time() - hit[0] < CACHE_SECONDS:
        return hit[1]
    headers = {"Accept": "application/vnd.github.raw+json" if raw else "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = requests.get(API + path, headers=headers, params=params, timeout=20)
    except requests.RequestException as ex:
        raise GitHubError("other", f"network error ({ex.__class__.__name__})")
    if r.status_code == 404:
        raise GitHubError("notfound")
    if r.status_code in (403, 429) and ("rate limit" in r.text.lower()
                                        or r.headers.get("X-RateLimit-Remaining") == "0"):
        raise GitHubError("ratelimit")
    if r.status_code == 401:
        raise GitHubError("other", "your GITHUB_TOKEN looks invalid. Fix or remove it in .env")
    if r.status_code >= 400:
        raise GitHubError("other", f"HTTP {r.status_code}")
    data = r.text if raw else r.json()
    _CACHE[key] = (time.time(), data)
    return data


def parse_repo(text):
    """Accept 'https://github.com/owner/repo' or 'owner/repo'. Returns 'owner/repo' or None."""
    text = (text or "").strip().rstrip("/")
    m = re.match(r"^(?:https?://)?(?:www\.)?github\.com/([\w.-]+)/([\w.-]+?)(?:\.git)?(?:/.*)?$", text)
    if not m:
        m = re.match(r"^([\w.-]+)/([\w.-]+)$", text)
    if not m:
        return None
    return f"{m.group(1)}/{m.group(2).removesuffix('.git')}"


def days_since(iso):
    """How many days ago a GitHub ISO date was (9999 if missing)."""
    if not iso:
        return 9999
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return (datetime.now(timezone.utc) - dt).days


def fetch_file(full, path):
    """Return the text of one file in the repo, or '' if it does not exist."""
    try:
        return get(f"/repos/{full}/contents/{quote(path)}", raw=True)
    except GitHubError as e:
        if e.kind == "ratelimit":
            raise
        return ""


def fetch_bundle(full):
    """Fetch everything the analysis needs: info, README, CONTRIBUTING, file tree, issues, PRs."""
    info = get(f"/repos/{full}")
    branch = info.get("default_branch", "main")
    try:
        items = get(f"/repos/{full}/git/trees/{quote(branch)}", {"recursive": "1"}).get("tree", [])
        tree = [i["path"] for i in items if i.get("type") == "blob"][:5000]
    except GitHubError as e:
        if e.kind == "ratelimit":
            raise
        tree = []
    try:
        readme = get(f"/repos/{full}/readme", raw=True)
    except GitHubError as e:
        if e.kind == "ratelimit":
            raise
        readme = ""
    contributing = ""
    for p in tree:
        if p.lower() in ("contributing.md", ".github/contributing.md", "docs/contributing.md"):
            contributing = fetch_file(full, p)
            break
    raw_issues = get(f"/repos/{full}/issues", {"state": "open", "per_page": 100, "sort": "updated"})
    issues = [i for i in raw_issues if "pull_request" not in i][:40]
    prs = get(f"/repos/{full}/pulls", {"state": "open", "per_page": 40})
    return {"info": info, "branch": branch, "tree": tree, "readme": readme or "",
            "contributing": contributing or "", "issues": issues, "prs": prs}
