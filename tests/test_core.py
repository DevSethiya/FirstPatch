"""Small offline tests for the core logic. Run: python -m pytest tests  (or python tests/test_core.py)"""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core import ai, discover, github, roadmap, scoring  # noqa: E402


def iso(days_ago):
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")


def issue(n, title="Fix typo in README.md", labels=("good first issue",), assignee=None, days=5, body="", locked=False):
    return {"number": n, "title": title, "body": body, "labels": [{"name": l} for l in labels], "assignee": assignee,
            "locked": locked, "updated_at": iso(days), "html_url": f"https://x/{n}", "comments": 0}


def test_parse_repo():
    assert github.parse_repo("https://github.com/a/b") == "a/b"
    assert github.parse_repo("https://github.com/a/b.git/") == "a/b"
    assert github.parse_repo("a/b") == "a/b"
    assert github.parse_repo("nonsense") is None


def test_fit_score_worked_example():
    s, _ = scoring.score_issue(issue(1, "Add Python example", body="python"), ["Python"])
    assert s == 100  # 30 + 25 + 20 + 15 + 10
    s, _ = scoring.score_issue(issue(2, labels=(), days=200), [])
    assert s == 45  # 25 + 20


def test_rank_and_skip():
    prs = [{"title": "Fix", "body": "Fixes #3"}]
    cands, skipped = scoring.rank_issues(
        [issue(1), issue(2, assignee={"login": "bob"}), issue(3), issue(4, locked=True)], prs, [])
    assert [c["number"] for c in cands] == [1]
    assert {s["number"]: s["reason"] for s in skipped} == {2: "assigned to bob", 3: "an open PR already mentions it", 4: "locked"}


def test_claimed(monkeypatch=None):
    orig = github.get
    github.get = lambda *a, **k: [{"body": "Hi, can I work on this?"}]
    try:
        c = scoring.rank_issues([dict(issue(1), comments=1), issue(2)], [], [])[0]
        c = scoring.check_claimed("a/b", c)
    finally:
        github.get = orig
    assert {x["number"]: x["status"] for x in c} == {1: "Possibly claimed", 2: "Available"}


def test_names():
    n = roadmap.make_names({"number": 123, "title": "[Bug] Broken link in the Docs page!", "labels": ["bug"]})
    assert n["branch"] == "fix/123-broken-link-in-the-docs"
    assert n["commit"] == "fix: broken link in the Docs page! (#123)"
    assert n["pr_body"] == "Fixes #123"
    assert roadmap.make_names({"number": 5, "title": "Typo", "labels": ["documentation"]})["branch"].startswith("docs/5-")


def test_files_to_inspect():
    tree = ["src/app/main.py", "docs/index.md", "README.md", "src/util.py"]
    c = {"title": "Crash in main.py", "body": "See `src/util.py` and README.md", "labels": []}
    files, folders = roadmap.files_to_inspect(c, tree)
    assert set(files) == {"src/app/main.py", "src/util.py", "README.md"} and folders == []
    files, folders = roadmap.files_to_inspect({"title": "Improve things", "body": "", "labels": []}, tree)
    assert files == [] and folders == ["src", "docs"]


def test_detect_setup():
    fake = {"package.json": json.dumps({"scripts": {"test": "jest", "build": "tsc"}}), "Makefile": "install:\n\tx\ntest:\n\ty\n"}
    r = roadmap.detect_setup("a/b", ["package.json", "Makefile", "yarn.lock"], "", fetch=lambda f, p: fake.get(p, ""))
    assert r["setup"] == ["yarn install", "yarn run build", "make install"] and r["test"] == ["yarn test", "make test"]
    readme = "```bash\npip install foo\npytest -q\n```"
    r = roadmap.detect_setup("a/b", ["README.md"], readme, fetch=lambda f, p: "")
    assert r["setup"] == ["pip install foo"] and r["test"] == ["pytest -q"] and r["sources"] == ["README"]


def test_ai_clean_and_errors():
    out = ai.clean({"project_summary": "s", "tasks": [{"issue_number": 1, "why": "w", "hints": ["h"]},
                                                     {"issue_number": 99, "why": "invented"}]}, {1})
    assert list(out["tasks"]) == [1]

    class E(Exception):
        def __init__(self, code, status=""):
            super().__init__(f"{code} {status}"); self.code, self.status = code, status
    assert ai.classify(E(403, "PERMISSION_DENIED")) == "permission"
    assert ai.classify(E(404, "NOT_FOUND")) == "model_not_found"
    assert ai.classify(E(429, "RESOURCE_EXHAUSTED")) == "quota"
    assert ai.classify(E(400, "INVALID_ARGUMENT API key not valid")) == "invalid_key"
    assert ai.classify(E(503)) == "unavailable"
    import os
    os.environ["GEMINI_API_KEY"] = ""
    try:
        ai.explain("", "", [], [])
        assert False
    except ai.AIError as e:
        assert e.kind == "missing_key"


def test_discover():
    assert discover.health_label(10) == "Active" and discover.health_label(45) == "Slow" and discover.health_label(80) == "Inactive"
    q = discover.build_query("C++", "Good for resume", True)
    assert 'language:"C++"' in q and "topic:hacktoberfest" in q and "stars:300..20000" in q
    items = [{"full_name": f"o/r{i}", "html_url": "u", "stargazers_count": i, "language": "Go", "description": None,
              "open_issues_count": 1, "pushed_at": iso(i)} for i in range(5)]
    orig, calls = github.get, []
    github.get = lambda path, params=None, raw=False: (calls.append(params["q"]) or {"items": items if "algorithms" not in params["q"] else []})
    try:
        res = discover.search(["Go", "Rust", "Java", "PHP"], "Easy problem solving", True)
    finally:
        github.get = orig
    assert len(res["repos"]) == 5 and res["repos"][0]["full_name"] == "o/r0" and "first 3" in res["note"] and "relaxed" in res["note"]


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print("ok", name)
