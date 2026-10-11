"""FirstPatch - turns an unfamiliar open-source repo into a clear path to your first contribution.
UI only. The logic lives in core/ (GitHub facts, scoring, roadmap, AI)."""
import html

import streamlit as st
from dotenv import load_dotenv

load_dotenv()  # reads GEMINI_API_KEY, GEMMA_MODEL, GITHUB_TOKEN from .env

from core import ai, discover, github, roadmap, scoring  # noqa: E402
from ui.styles import CSS, LOGO, logo_uri  # noqa: E402

st.set_page_config(page_title="FirstPatch", page_icon=str(LOGO), layout="wide", initial_sidebar_state="collapsed")
st.markdown(CSS, unsafe_allow_html=True)

STATUS_COLORS = {"Available": "#3FB950", "Possibly claimed": "#F5A524", "Taken": "#F85149",
                 "Active": "#3FB950", "Slow": "#F5A524", "Inactive": "#F85149"}
PAGES = {"analyze": "🔍 Analyze", "discover": "🧭 Discover"}

for k, v in {"page": "analyze", "repo_input": "", "analysis": None, "selected": None, "disc": None, "shown": 30}.items():
    st.session_state.setdefault(k, v)


# ---------------- small helpers ----------------
def esc(text):
    """Escape repo-derived text before it goes into HTML."""
    return html.escape(str(text or ""))


def chip(text):
    """A coloured status chip."""
    c = STATUS_COLORS.get(text, "#8B5CF6")
    return f'<span class="chip" style="color:{c};border-color:{c};background:{c}22">{esc(text)}</span>'


def hero(title, sub):
    """Gradient page title with a short tagline."""
    st.markdown(f'<div class="hero"><div class="h1">{esc(title)}</div><p>{esc(sub)}</p></div>', unsafe_allow_html=True)


def heading(text, level=3):
    """Section heading drawn as a styled div, so Streamlit adds no link icon."""
    st.markdown(f'<div class="h{level}">{text}</div>', unsafe_allow_html=True)


def set_page(name):
    """Callback: switch page."""
    st.session_state.page = name


def select_task(n):
    """Callback: remember which issue the user picked."""
    st.session_state.selected = n


def pick_repo(full_name):
    """Callback for 'Analyze this repo' in Discover: fill the URL, switch page, auto-run."""
    st.session_state.repo_input = full_name
    st.session_state.page = "analyze"
    st.session_state.auto_run = True


def load_more():
    """Callback: show 30 more repos (max 100)."""
    st.session_state.shown = min(st.session_state.shown + 30, 100)


# ---------------- navbar ----------------
def navbar():
    """One rounded pill: logo+name left, page buttons middle, Settings right."""
    with st.container(key="navbar"):
        c = st.columns([1.6, 1, 1, 1.3], vertical_alignment="center")
        c[0].markdown(f'<div class="brand"><img src="{logo_uri()}" alt="logo"><span>FirstPatch</span></div>',
                      unsafe_allow_html=True)
        for col, (key, label) in zip(c[1:3], PAGES.items()):
            col.button(label, key=f"nav_{key}", use_container_width=True, on_click=set_page, args=(key,),
                       type="primary" if st.session_state.page == key else "secondary")
        with c[3].popover("ℹ️ About", use_container_width=True):
            t1, t2 = st.tabs(["How it works", "About"])
            with t1:
                st.markdown(
                    "1. **Pick a way in:** analyze a repo you already like, or let Discover find repos for you.\n"
                    "2. **Choose your skills** so the best matches rise to the top.\n"
                    "3. **FirstPatch searches GitHub** for the best and easiest issues for your choices and skill set.\n"
                    "4. **Pick one task** from the top picks, shown side by side.\n"
                    "5. **Follow the 8-step roadmap** to solve it, from fork to pull request.")
            with t2:
                st.markdown(
                    "**FirstPatch** helps first-time open-source contributors. It looks through GitHub for the "
                    "best, easiest issues based on your choices and skills, shows you the best one, and gives you "
                    "the steps to solve it.\n\nFacts (is it assigned? is a PR open? is it recent?) come live from "
                    "GitHub. FirstPatch uses Gemma 4 together with live GitHub data to surface the most suitable " 
                    "repositories and issues for you, and presents them with clear, beginner-friendly explanations.")


# ---------------- Analyze page ----------------
def run_analysis():
    """Fetch GitHub facts, score issues, detect commands, then ask Gemma 4 (optional)."""
    full = github.parse_repo(st.session_state.repo_input)
    if not full:
        st.error("That doesn't look like a GitHub repo. Use https://github.com/owner/repo or owner/repo.")
        return
    skills = st.session_state.get("skills_a") or []
    try:
        with st.status("Analyzing repo...", expanded=True) as status:
            st.write("Fetching repo, README and file tree...")
            b = github.fetch_bundle(full)
            st.write("Scoring issues...")
            cands, skipped = scoring.rank_issues(b["issues"], b["prs"], skills)
            if not cands:
                status.update(label="No suitable issues", state="error")
                st.session_state.analysis = None
                st.warning("No suitable issues found: every open issue is assigned, locked or already has a PR. "
                           "Try another repo or use Discover.")
                return
            st.write("Checking claimed issues...")
            cands = scoring.check_claimed(full, cands)
            st.write("Detecting setup and test commands...")
            setup = roadmap.detect_setup(full, b["tree"], b["readme"])
            top = cands[:4]
            st.write("Asking Gemma 4...")
            ai_data, ai_error = {"summary": "", "tasks": {}}, None
            try:
                ai_data = ai.explain(b["readme"], b["contributing"], b["tree"], top)
            except ai.AIError as e:
                ai_error = str(e)
            status.update(label="Done", state="complete", expanded=False)
    except github.GitHubError as e:
        st.error(github.friendly_error(e))
        return
    st.session_state.analysis = {"full": full, "b": b, "top": top, "skipped": skipped, "setup": setup,
                                 "ai": ai_data, "ai_error": ai_error}
    st.session_state.selected = top[0]["number"]


def step(n, title):
    """Numbered step heading."""
    st.markdown(f'<div class="step"><div class="num">{n}</div>{esc(title)}</div>', unsafe_allow_html=True)


def render_roadmap(a, c):
    """The 8-step plain roadmap for the selected issue."""
    full, name, branch = a["full"], a["full"].split("/")[1], a["b"]["branch"]
    names = roadmap.make_names(c)
    files, folders = roadmap.files_to_inspect(c, a["b"]["tree"])
    ai_task = a["ai"]["tasks"].get(c["number"], {})
    heading(f"Your roadmap for issue #{c['number']}")
    with st.container(border=True):
        step(1, "Fork the repository")
        st.markdown(f"Create your own copy on GitHub. Then leave a short comment on "
                    f"[issue #{c['number']}]({c['url']}) so others know you're on it.")
        st.link_button("Open GitHub's fork page", f"https://github.com/{full}/fork")
    with st.container(border=True):
        step(2, "Clone your fork")
        st.code(f"git clone https://github.com/YOUR-USERNAME/{name}.git\ncd {name}\n"
                f"git remote add upstream https://github.com/{full}.git", language="bash")
        st.caption("Replace YOUR-USERNAME with your GitHub username.")
    with st.container(border=True):
        step(3, "Create a branch")
        st.code(f"git checkout -b {names['branch']}", language="bash")
    with st.container(border=True):
        step(4, "Set up the project")
        if a["setup"]["setup"]:
            st.code("\n".join(a["setup"]["setup"]), language="bash")
            st.caption("Detected from: " + ", ".join(a["setup"]["sources"]))
        else:
            st.info("No setup commands detected. Read the README / CONTRIBUTING file.")
    with st.container(border=True):
        step(5, "Find and change the code")
        if files:
            st.markdown("Files named in the issue that exist in the repo:")
            for f in files:
                st.markdown(f"- [`{f}`](https://github.com/{full}/blob/{a['b']['branch']}/{f})")
        else:
            st.markdown("No file is named in the issue. Start by exploring the main folders:")
            st.markdown(" ".join(f"`{f}/`" for f in folders) or "_No folders found._")
        if ai_task.get("hints"):
            st.markdown("**Hints from Gemma 4:**\n" + "\n".join(f"- {esc(h)}" for h in ai_task["hints"]))
    with st.container(border=True):
        step(6, "Run the tests")
        if a["setup"]["test"]:
            st.code("\n".join(a["setup"]["test"]), language="bash")
        else:
            st.info("No test command detected. Check the README / CONTRIBUTING for how to test.")
        st.caption("FirstPatch does not run tests for you.")
    with st.container(border=True):
        step(7, "Commit and push")
        st.code(f"git add .\ngit commit -m \"{names['commit']}\"\ngit push -u origin {names['branch']}", language="bash")
    with st.container(border=True):
        step(8, "Open the pull request")
        st.markdown("Title:")
        st.code(names["pr_title"], language=None)
        st.markdown("Description:")
        st.code(names["pr_body"], language=None)
        st.link_button("Open the repo's pull request page", f"https://github.com/{full}/compare")


def render_results():
    """Repo summary, task cards (pick one), roadmap, skipped issues."""
    a = st.session_state.analysis
    if not a:
        return
    info, b = a["b"]["info"], a["b"]
    heading(f'<a href="{esc(info["html_url"])}" target="_blank">{esc(a["full"])}</a>', 2)
    lic = (info.get("license") or {}).get("spdx_id") or "no license"
    st.markdown(f'<span class="chip" style="color:#C4B5FD;border-color:#2B1F47">⭐ {info["stargazers_count"]:,}</span>'
                f'<span class="chip" style="color:#C4B5FD;border-color:#2B1F47">{esc(info.get("language") or "-")}</span>'
                f'<span class="chip" style="color:#C4B5FD;border-color:#2B1F47">{esc(lic)}</span>'
                f'<span class="chip" style="color:#C4B5FD;border-color:#2B1F47">last push {github.days_since(info.get("pushed_at"))}d ago</span>',
                unsafe_allow_html=True)
    summary = a["ai"]["summary"] or info.get("description") or "No description available."
    st.markdown(f'<p class="muted">{esc(summary)}</p>', unsafe_allow_html=True)

    heading("Choose your task")
    cols = st.columns(len(a["top"]))
    for col, c in zip(cols, a["top"]):
        sel = st.session_state.selected == c["number"]
        t = a["ai"]["tasks"].get(c["number"], {})
        with col.container(border=True, key=f"taskcard_{'sel' if sel else 'idle'}_{c['number']}"):
            st.markdown(f'<div class="score">{c["score"]}<span class="muted">/100</span></div>'
                        f'{chip(c["status"])}<div class="tcard-title">#{c["number"]} {esc(c["title"])}</div>'
                        + "".join(f'<span class="chip" style="color:#A59BC0;border-color:#2B1F47">{esc(l)}</span>'
                                  for l in c["labels"][:3])
                        + (f'<p class="muted">{esc(t["why"])}</p>' if t.get("why") else "")
                        + (f'<p class="muted">{esc(t["difficulty"])} · {esc(t["estimated_time"])}</p>' if t else ""),
                        unsafe_allow_html=True)
            st.button("✓ Selected" if sel else "Choose this task", key=f"pick_{c['number']}", disabled=sel,
                      use_container_width=True, type="primary" if not sel else "secondary",
                      on_click=select_task, args=(c["number"],))
    chosen = next((c for c in a["top"] if c["number"] == st.session_state.selected), a["top"][0])
    with st.expander("Why this score?"):
        st.markdown("\n".join(f"- {w}" for w in chosen["why_score"]))
    render_roadmap(a, chosen)
    if a["skipped"]:
        with st.expander(f"Skipped issues ({len(a['skipped'])})"):
            for s in a["skipped"]:
                st.markdown(f'{chip("Taken")} [#{s["number"]} {esc(s["title"])}]({s["url"]}) — {esc(s["reason"])}',
                            unsafe_allow_html=True)


def analyze_page():
    """Tab 1: analyze a single repo."""
    with st.container(key="page_analyze"):
        hero("Analyze a repo", "Turn an unfamiliar repository into a clear path to your first contribution.")
        with st.container(border=True):
            st.text_input("GitHub repo", key="repo_input", placeholder="https://github.com/owner/repo  or  owner/repo")
            st.pills("Pick your skills for your first open-source contribution (optional)", discover.SKILLS, selection_mode="multi", key="skills_a")
            go = st.button("Find my first issue", type="primary", key="go_analyze")
        if go or st.session_state.pop("auto_run", False):
            run_analysis()
        render_results()


# ---------------- Discover page ----------------
def scan_repos():
    """Search GitHub live and store the ranked list."""
    try:
        with st.status("Searching GitHub...", expanded=False) as status:
            res = discover.search(st.session_state.get("skills_d") or [],
                                  st.session_state.get("goal", discover.GOALS[0]), False)
            status.update(label=f"Found {len(res['repos'])} repos", state="complete")
    except github.GitHubError as e:
        st.error(github.friendly_error(e))
        return
    st.session_state.disc, st.session_state.shown = res, 30


def discover_page():
    """Tab 2: find good repos for your skills and goal."""
    with st.container(key="page_discover"):
        hero("Discover repos", "Live repositories that welcome beginners, ranked by recent activity.")
        with st.container(border=True):
            st.pills("Pick your skills for your first open-source contribution (up to 3 are used)", discover.SKILLS, selection_mode="multi", key="skills_d")
            st.selectbox("Your goal", discover.GOALS, key="goal")
            find = st.button("Find repos", type="primary", key="go_discover")
        if find:
            scan_repos()
        d = st.session_state.disc
        if not d:
            return
        if not d["repos"]:
            st.warning("No repos matched. Try other skills, another goal, or pick fewer skills.")
            return
        if d["note"]:
            st.info(d["note"])
        total = min(len(d["repos"]), 100)
        shown = min(st.session_state.shown, total)
        st.markdown(f'<p class="muted">Showing {shown} of {total} repos</p>', unsafe_allow_html=True)
        for r in d["repos"][:shown]:
            with st.container(border=True):
                c = st.columns([4, 1, 1.3, 1.2, 1.6], vertical_alignment="center")
                c[0].markdown(f'**[{esc(r["full_name"])}]({r["url"]})**<br><span class="muted">'
                              f'{esc(r["description"][:110])}</span>', unsafe_allow_html=True)
                c[1].markdown(f"⭐ {r['stars']:,}")
                c[2].markdown(esc(r["language"]))
                c[3].markdown(f'{chip(r["health"])}<br><span class="muted">{r["days"]}d ago</span>', unsafe_allow_html=True)
                c[4].button("Analyze this repo", key=f"an_{r['full_name']}", on_click=pick_repo,
                            args=(r["full_name"],), use_container_width=True)
        if shown < total:
            st.button(f"Load more ({total - shown} left)", key="load_more", on_click=load_more, use_container_width=True)


# ---------------- main ----------------
navbar()
if st.session_state.page == "analyze":
    analyze_page()
else:
    discover_page()
