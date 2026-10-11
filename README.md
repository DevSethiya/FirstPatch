<div align="center">

<img src="assets/logo.png" alt="FirstPatch logo" width="140">

# FirstPatch

**Turn an unfamiliar open-source repository into a clear, evidence-backed path to your first contribution.**

![Python](https://img.shields.io/badge/Python-3.10%2B-8B5CF6?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Built%20with-Streamlit-A855F7)
![Gemma 4](https://img.shields.io/badge/AI-Gemma%204-6D28D9)
![License](https://img.shields.io/badge/License-MIT-C4B5FD)
![Hacktoberfest](https://img.shields.io/badge/Hacktoberfest-2026-F97316)

</div>

---

## Table of Contents
1. [Overview](#overview)
2. [Key Features](#key-features)
3. [How It Works](#how-it-works)
4. [Tech Stack](#tech-stack)
5. [Project Structure](#project-structure)
6. [Getting Started](#getting-started)
7. [Configuration](#configuration)
8. [Usage](#usage)
9. [Fit Score](#fit-score)
10. [Testing](#testing)
11. [Troubleshooting](#troubleshooting)
12. [Limitations](#limitations)
13. [Roadmap](#roadmap)
14. [Contributing](#contributing)
15. [License](#license)

---

## Overview

Many beginners never make an open-source contribution because the first step is unclear: which repository to choose, which issue is suitable, whether someone is already working on it, and what to do next.

**FirstPatch** removes that uncertainty. It searches GitHub for beginner-friendly repositories and issues that match your skills, checks live facts about each issue (is it assigned, does a pull request already exist, is it recently active), and gives you a numbered roadmap from forking the repository to opening your pull request.

> **Design principle:** the application *computes* facts from the live GitHub API. Gemma 4 only *explains* them in simple language. The AI is never the source of truth, and anything it invents is filtered out.

Built for **MLH Hacktoberfest Hack Day** (Best Use of Gemma 4, Best Open-Source AI Project).

## Key Features

### Analyze a repository
- Paste a repository URL (`https://github.com/owner/repo`) or `owner/repo`.
- Select your skills from clickable blocks; selected skills glow.
- The top 3-4 issues are shown side by side with a Fit Score and a status chip: **Available**, **Possibly claimed**.
- Choose one task and the whole roadmap follows your choice.
- Issues that are assigned, locked or already covered by an open PR are listed under **Skipped issues** with the reason.

### 8-step roadmap
Fork, clone, branch, set up, find and change the code, test, commit and push, open a pull request. The issue number is filled into every step using standard conventions:

| Item | Example |
|---|---|
| Branch | `fix/123-short-title` |
| Commit message | `fix: short title (#123)` |
| PR title | `fix: short title (#123)` |
| PR description | `Fixes #123` |

### Works without AI
- **Files to inspect:** files named in the issue are matched against the repository file list. If none are named, the main folders are suggested.
- **Setup and test commands:** detected from `package.json`, `requirements.txt`, `pyproject.toml`, `Makefile`, `go.mod`, `Cargo.toml`, `pom.xml`, `Gemfile` and others, with a fallback to commands found in the README.

### Discover repositories
- Live repositories from GitHub, 30 at a time, with **Load more** up to 100.
- Goal filter: *Easy bug fixes*, *Easy problem solving*, *Good for resume*.
- 25 skills: Python, JavaScript, TypeScript, Java, C, C++, C#, Go, Rust, PHP, Ruby, Swift, Kotlin, Dart, R, SQL, Shell, HTML/CSS, Machine Learning, Web, Mobile, Data Science, DevOps, Games, Docs and Security.
- Ranked by recent activity and labelled **Active**, **Slow** or **Inactive**.
- One click on **Analyze this repo** sends the repository to the Analyze page.

### Interface
- Dark purple theme, responsive from phone to desktop.
- Single rounded navigation bar with smooth page transitions.
- **About** menu explaining how the app works.

## How It Works

```
Repository URL ─► GitHub API ─► Live facts ─► Fit Score ─► Top 3-4 issues
                      │                                         │
                      ├─► Files / setup / test detection        │
                      │        (plain code, no AI)              │
                      └─────────────────────────────────────────┴─► Gemma 4 explains
                                                                       (output validated)
                                                                              │
                                                              You pick a task ─► 8-step roadmap

Discover: skills + goal ─► GitHub Search API ─► ranked by last push ─► "Analyze this repo"
```

**Preventing AI hallucination:** Gemma 4 receives only facts computed by the app and must reply in JSON. Any issue number not in the computed list is discarded. File paths, commands and branch names are produced by code, never by the AI. If the AI step fails for any reason, the application continues without the explanations.

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.10+ |
| UI | [Streamlit](https://streamlit.io) with custom CSS |
| Data | [GitHub REST API](https://docs.github.com/en/rest) |
| AI | Gemma 4 through the [Gemini API](https://ai.google.dev) (`google-genai`) |
| Config | `python-dotenv` |
| HTTP | `requests` |

## Project Structure

```
firstpatch/
├── app.py              # Streamlit UI: navigation, pages, cards, roadmap
├── core/
│   ├── github.py       # API calls, caching, URL parsing, error handling
│   ├── scoring.py      # Fit Score, skipped issues, "possibly claimed" check
│   ├── roadmap.py      # Branch/commit/PR names, files to inspect, setup detection
│   ├── ai.py           # Gemma 4 call, output validation, error classification
│   └── discover.py     # Repository search and activity labels
├── ui/styles.py        # Theme CSS and logo helper
├── assets/logo.png     # Project logo
├── tests/test_core.py  # Offline unit tests
├── .streamlit/config.toml
├── .env.example        # Sample environment file
├── requirements.txt
├── EXPLAIN.md          # Plain-language explanation and demo script
└── LICENSE
```

## Getting Started

### Prerequisites
- Python 3.10 or newer
- A free Gemini API key from [Google AI Studio](https://aistudio.google.com) (optional; see note below)
- A GitHub personal access token (optional)

### Installation

```bash
git clone https://github.com/<your-username>/firstpatch.git
cd firstpatch

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### Set up your environment file

A sample environment file, **`.env.example`**, is included in the project so you can add your own API keys. After adding them, **rename the file to `.env`** and it will work as a normal environment file:

```bash
cp .env.example .env             # Windows: copy .env.example .env
```

Then open `.env` and fill in your values (see [Configuration](#configuration)).

> **Security:** `.env` is listed in `.gitignore`. Never commit real keys or share them publicly.

### Run

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

## Configuration

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | Optional | Key from [aistudio.google.com](https://aistudio.google.com). Enables AI explanations. Without it, every other feature still works. |
| `GEMMA_MODEL` | Optional | Exact Gemma 4 model name. Default: `gemma-4-31b-it`. Verify the current name in Google AI Studio. |
| `GITHUB_TOKEN` | Optional | Raises GitHub's limit from 60 to 5,000 requests per hour. No scopes or permissions are needed. It is read from `.env` only and is never shown in the app. |

Creating a GitHub token: GitHub → Settings → Developer settings → Personal access tokens → generate a token with no scopes.

## Usage

**Analyze a repository**
1. Open **Analyze** and paste a repository URL.
2. Select your skills (optional).
3. Click **Find my first issue**.
4. Choose one of the top issues and follow the 8-step roadmap.

**Discover repositories**
1. Open **Discover** and select your skills and goal.
2. Click **Find repos**.
3. Use **Load more** to see additional results, then click **Analyze this repo** on any result.

Click **About** in the navigation bar for a short in-app guide.

## Fit Score

Each issue receives a score from 0 to 100 using five transparent rules:

| Rule | Points |
|---|---|
| Beginner-friendly label (good first issue, beginner, easy, help wanted, documentation, hacktoberfest) | +30 |
| No assignee | +25 |
| No open PR mentions the issue | +20 |
| Updated in the last 60 days | +15 |
| Issue text or labels match your skills | +10 |

**Example:** an unassigned issue labelled *good first issue*, updated 5 days ago, mentioning Python while you selected Python scores 30 + 25 + 20 + 15 + 10 = **100**.

## Testing

Offline unit tests cover scoring, issue skipping, naming conventions, file matching, setup detection, AI output validation and Discover logic. No network is required.

```bash
python tests/test_core.py
# or, if pytest is installed:
python -m pytest tests
```

## Troubleshooting

| Problem | Solution |
|---|---|
| "GitHub rate limit reached" | Add `GITHUB_TOKEN` to `.env`, or wait and retry. Unauthenticated access allows 60 requests per hour. |
| "Repo not found" | Check the spelling. Private repositories cannot be read. |
| "No suitable issues" | Every open issue is assigned, locked or has a PR. Try another repository or use Discover. |
| No AI explanations appear | Check `GEMINI_API_KEY` and `GEMMA_MODEL` in `.env`. The rest of the app works without them. A 403 error means Google blocked that key's project; create a key from another Google account or a new project. |
| Discover returns few results | Select fewer skills or choose a different goal. |

## Limitations

- Tests of the target repository are **not executed**; FirstPatch only tells you which commands to run.
- GitHub API limits apply (60 requests per hour without a token).
- Discover ranks by last push date, not by exact commit counts.
- Only public repositories are supported.
- Setup detection depends on standard project files or README instructions.

## Roadmap

- Sandboxed test execution
- Skill-based ranking across many repositories
- Saved progress and contribution history
- Support for GitLab and other platforms

## Contributing

Contributions are welcome.

1. Fork the repository
2. Create a branch: `git checkout -b feat/<issue>-short-title`
3. Make your changes and run `python tests/test_core.py`
4. Commit using conventional messages, e.g. `feat: add language filter (#12)`
5. Open a pull request that references the issue (`Fixes #12`)

## License

Released under the [MIT License](LICENSE).

## Screenshots

| Analyze | Discover |
|---|---|
| _Add screenshot_ | _Add screenshot_ |

---

<div align="center">Made for first-time contributors. Happy Hacktoberfest!</div>
