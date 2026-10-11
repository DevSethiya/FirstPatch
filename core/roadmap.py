"""Roadmap helpers: naming, files to inspect, setup/test detection. No AI needed."""
import json
import re

from core import github

FENCE_RE = re.compile(r"```[\w-]*\n(.*?)```", re.S)
CMD_RE = re.compile(r"^\$?\s*((npm|yarn|pnpm|pip3?|python3?|pytest|make|cargo|go|mvn|gradle|\./gradlew|bundle|rake|"
                    r"composer|dotnet|flutter|poetry|uv|docker)\b.*)$")


# ---------- branch / commit / PR names ----------
def issue_kind(labels, title):
    """Return (branch prefix, commit type). Labels win over title words; bug beats docs."""
    for text in (" ".join(labels), title.lower()):
        if re.search(r"\b(bug|crash|error|broken|fix)", text):
            return "fix", "fix"
        if re.search(r"\b(docs?|documentation|typo|readme)", text):
            return "docs", "docs"
        if re.search(r"\b(enhancement|feature|feat|add)", text):
            return "feat", "feat"
        if re.search(r"\btests?\b", text):
            return "test", "test"
    return "fix", "fix"


def short_title(title):
    """Strip tags like '[Bug]' or 'feat:' and shorten the title."""
    t = re.sub(r"^\s*(\[[^\]]*\]\s*)+", "", title)
    t = re.sub(r"^\s*(bug|fix|feat|feature|docs?|chore|issue)\s*[:\-]\s*", "", t, flags=re.I).strip() or title
    t = t[:60].rstrip()
    return t[0].lower() + t[1:] if t else t


def slugify(text, max_words=5):
    """'Fix broken link in README!' -> 'fix-broken-link-in-readme'."""
    words = re.findall(r"[a-z0-9]+", text.lower())[:max_words]
    return "-".join(words) or "update"


def make_names(c):
    """Branch, commit, PR title and PR body for a candidate issue."""
    prefix, ctype = issue_kind(c["labels"], c["title"])
    st = short_title(c["title"])
    n = c["number"]
    msg = f"{ctype}: {st} (#{n})"
    return {"branch": f"{prefix}/{n}-{slugify(st)}", "commit": msg, "pr_title": msg,
            "pr_body": f"Fixes #{n}"}


# ---------- files to inspect ----------
def files_to_inspect(c, tree):
    """Find files named in the issue and match them against the repo file list.
    Returns (matches, fallback_folders). Only one of them is non-empty."""
    text = f"{c['title']} {c['body']}"
    tokens = {t.strip(".,;:()[]'\"`").lstrip("./") for t in re.findall(r"[\w./\\-]+\.[A-Za-z0-9]{1,8}", text)}
    tokens = {t.replace("\\", "/") for t in tokens if t and not re.fullmatch(r"[\d.]+", t)
              and not t.startswith("http") and "www." not in t}
    paths, by_name = set(tree), {}
    for p in tree:
        by_name.setdefault(p.rsplit("/", 1)[-1], []).append(p)
    found = []
    for t in sorted(tokens):
        hits = [t] if t in paths else [p for p in tree if p.endswith("/" + t)][:3]
        if not hits and "/" not in t and 0 < len(by_name.get(t, [])) <= 3:
            hits = by_name[t]
        for h in hits:
            if h not in found:
                found.append(h)
    if found:
        return found[:6], []
    top = sorted({p.split("/")[0] for p in tree if "/" in p})
    first = [f for f in ("src", "lib", "app", "docs", "tests", "test") if f in top]
    return [], (first + [f for f in top if f not in first])[:8]


# ---------- setup / test detection ----------
def _add(lst, cmd):
    """Append a command once."""
    if cmd and cmd not in lst:
        lst.append(cmd)


def commands_from_readme(readme):
    """Pull install/test-looking commands out of README code blocks."""
    setup, test = [], []
    for block in FENCE_RE.findall(readme or ""):
        for line in block.splitlines():
            m = CMD_RE.match(line.strip())
            if m:
                _add(test if "test" in m.group(1).lower() else setup, m.group(1).strip())
    return setup[:5], test[:3]


def detect_setup(full, tree, readme, fetch=github.fetch_file):
    """Detect commands from manifest files, then fall back to the README."""
    root = {p for p in tree if "/" not in p}
    setup, test, sources = [], [], []
    has_tests = any(p.startswith(("tests/", "test/")) or "/test_" in p or p.startswith("test_") for p in tree)

    if "package.json" in root:
        try:
            scripts = json.loads(fetch(full, "package.json") or "{}").get("scripts", {}) or {}
        except (ValueError, AttributeError):
            scripts = {}
        pm = "yarn" if "yarn.lock" in root else "pnpm" if "pnpm-lock.yaml" in root else "npm"
        _add(setup, f"{pm} install")
        if "build" in scripts:
            _add(setup, f"{pm} run build")
        if "test" in scripts:
            _add(test, f"{pm} test")
        sources.append("package.json")
    if "requirements.txt" in root:
        _add(setup, "pip install -r requirements.txt"); sources.append("requirements.txt")
    if "pyproject.toml" in root or "setup.py" in root:
        _add(setup, "pip install -e ."); sources.append("pyproject.toml" if "pyproject.toml" in root else "setup.py")
    if sources and any(s in sources for s in ("requirements.txt", "pyproject.toml", "setup.py")) and has_tests:
        _add(test, "pytest")
    if "Makefile" in root:
        targets = set(re.findall(r"^([A-Za-z0-9_.-]+):", fetch(full, "Makefile") or "", re.M))
        for t in ("install", "setup", "deps", "build"):
            if t in targets:
                _add(setup, f"make {t}")
        for t in ("test", "check"):
            if t in targets:
                _add(test, f"make {t}")
        sources.append("Makefile")
    simple = {"go.mod": (["go mod download"], ["go test ./..."]), "Cargo.toml": (["cargo build"], ["cargo test"]),
              "pom.xml": (["mvn install"], ["mvn test"]), "build.gradle": (["./gradlew build"], ["./gradlew test"]),
              "build.gradle.kts": (["./gradlew build"], ["./gradlew test"]),
              "composer.json": (["composer install"], []), "Gemfile": (["bundle install"], ["bundle exec rake test"]),
              "pubspec.yaml": (["flutter pub get"], ["flutter test"])}
    for f, (s, t) in simple.items():
        if f in root:
            [_add(setup, x) for x in s]; [_add(test, x) for x in t]; sources.append(f)
    if any(p.endswith((".sln", ".csproj")) for p in tree):
        _add(setup, "dotnet build"); _add(test, "dotnet test"); sources.append(".NET project")

    r_setup, r_test = commands_from_readme(readme)
    from_readme = False
    if not setup and r_setup:
        setup, from_readme = r_setup, True
    if not test and r_test:
        test, from_readme = r_test, True
    if from_readme:
        sources.append("README")
    return {"setup": setup[:6], "test": test[:4], "sources": sources}
