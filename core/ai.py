"""Gemma 4 via the Gemini API. The AI only EXPLAINS the facts we computed; its output is validated."""
import json
import os

PROMPT_RULES = ("Use ONLY the given context. If something is missing, say 'Not found in repo docs'. "
                "Never invent file paths, commands or issues. Do not write the full solution. "
                "Keep the language simple for a beginner.")
SCHEMA = ('Return JSON only (no markdown) in exactly this shape: {"project_summary": "2-3 simple sentences", '
          '"tasks": [{"issue_number": 0, "why": "one sentence why this suits a beginner", '
          '"difficulty": "Easy|Medium", "estimated_time": "e.g. 1-2 hours", '
          '"hints": ["3-4 short hints, no full solution code"]}]}')

MESSAGES = {
    "missing_key": "No Gemini API key found. Add GEMINI_API_KEY to your .env file (free key at aistudio.google.com).",
    "invalid_key": "Your Gemini API key was rejected. Create a new key at aistudio.google.com and update .env.",
    "permission": ("Permission denied (403). Google blocked this API key's Cloud project, so changing the model "
                   "will not help. Create a key in AI Studio with a different Google account or a brand-new "
                   "project, or contact Google support."),
    "model_not_found": "Model not found. Check the exact Gemma 4 name at aistudio.google.com and set GEMMA_MODEL in .env.",
    "quota": "Gemini quota or rate limit reached. Wait a minute and try again, or use another key.",
    "unavailable": "The Gemini service is temporarily unavailable. Try again shortly.",
    "bad_output": "Gemma 4 answered in an unexpected format. Try again.",
    "other": "The AI step failed (check your internet connection).",
}


class AIError(Exception):
    """kind is a key of MESSAGES."""

    def __init__(self, kind, detail=""):
        super().__init__(MESSAGES.get(kind, MESSAGES["other"]))
        self.kind, self.detail = kind, detail


def classify(e):
    """Turn any exception from the Gemini SDK into an AIError kind."""
    code = getattr(e, "code", None)
    status = str(getattr(e, "status", "") or "").upper()
    msg = str(e).lower()
    if isinstance(e, (ValueError, KeyError)) and code is None:
        return "bad_output"
    if code == 403 or "PERMISSION_DENIED" in status or "permission denied" in msg:
        return "permission"
    if code == 404 or "NOT_FOUND" in status:
        return "model_not_found"
    if code == 429 or "RESOURCE_EXHAUSTED" in status or "quota" in msg:
        return "quota"
    if code in (400, 401) and ("api key" in msg or "api_key" in msg):
        return "invalid_key"
    if isinstance(code, int) and code >= 500:
        return "unavailable"
    return "other"


def _call_model(prompt):
    """Send the prompt to Gemma 4 and return the raw text."""
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key or key.startswith("your_"):
        raise AIError("missing_key")
    from google import genai  # imported here so the app still starts without the package
    client = genai.Client(api_key=key)
    return client.models.generate_content(model=os.getenv("GEMMA_MODEL", "gemma-4-31b-it"), contents=prompt).text or ""


def clean(ai, valid_numbers):
    """Drop anything the AI invented (unknown issue numbers) and force the right types."""
    tasks, seen = {}, set()
    for t in ai.get("tasks", []) if isinstance(ai.get("tasks"), list) else []:
        try:
            n = int(t.get("issue_number"))
        except (TypeError, ValueError, AttributeError):
            continue
        if n not in valid_numbers or n in seen:
            continue
        seen.add(n)
        hints = t.get("hints") if isinstance(t.get("hints"), list) else []
        tasks[n] = {"why": str(t.get("why", "")), "estimated_time": str(t.get("estimated_time") or "Not estimated"),
                    "difficulty": t.get("difficulty") if t.get("difficulty") in ("Easy", "Medium") else "Easy",
                    "hints": [str(h) for h in hints][:4]}
    return {"summary": str(ai.get("project_summary", "")), "tasks": tasks}


def explain(readme, contributing, tree, top):
    """Ask Gemma 4 to explain the top issues. Raises AIError with a specific kind on any failure."""
    facts = [{"issue_number": c["number"], "title": c["title"], "labels": c["labels"], "text": c["body"][:800],
              "fit_score": c["score"], "status": c["status"]} for c in top]
    prompt = (f"{PROMPT_RULES}\n\n{SCHEMA}\n\n## README\n{(readme or 'Not found in repo docs')[:5000]}\n\n"
              f"## CONTRIBUTING\n{(contributing or 'Not found in repo docs')[:3000]}\n\n"
              f"## FILE TREE (first 300)\n{chr(10).join(tree[:300])}\n\n"
              f"## CANDIDATE ISSUES (facts computed from the GitHub API)\n{json.dumps(facts)}")
    try:
        text = _call_model(prompt)
        return clean(json.loads(text[text.find("{"): text.rfind("}") + 1]), {c["number"] for c in top})
    except AIError:
        raise
    except Exception as e:  # noqa: BLE001 - we classify every SDK/network error
        raise AIError(classify(e), str(e)[:200])
