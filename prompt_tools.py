"""Prompt utilities: variable extraction, rendering, quality analysis, token estimate, line diff."""
import difflib
import re

VAR_RE = re.compile(r"\{\{\s*([a-zA-Z_][\w ]{0,40}?)\s*\}\}")
VAGUE = ["something", "stuff", "things", "etc", "good", "nice", "maybe", "kind of"]
VERBS = ["write", "summarize", "summarise", "classify", "extract", "explain", "generate", "translate", "list", "compare",
         "analyze", "analyse", "rewrite", "create", "draft", "identify", "evaluate", "convert", "review", "design", "plan"]


def variables(body):
    seen = []
    for v in VAR_RE.findall(body):
        v = v.strip()
        if v not in seen:
            seen.append(v)
    return seen


def render(body, values):
    return VAR_RE.sub(lambda m: str(values.get(m.group(1).strip()) or "{{" + m.group(1).strip() + "}}"), body)


def tokens(text):
    return max(1, round(len(text) / 4))


def analyse(body):
    p = body.lower()
    words = re.findall(r"[a-z']+", p)
    s, tips = {}, []
    s["Role"] = 10 if re.search(r"\byou are\b|\bact as\b", p) else 3
    if s["Role"] < 5:
        tips.append("Add a role, e.g. 'You are a senior data analyst'.")
    verbs = [v for v in VERBS if re.search(rf"\b{v}\b", p)]
    s["Clarity"] = max(0, min(10, 4 + 3 * len(verbs) - sum(f" {v} " in f" {p} " for v in VAGUE) * 2))
    if not verbs:
        tips.append("Start the task with a clear action verb.")
    s["Context"] = 10 if len(words) > 60 or "context" in p else 6 if len(words) > 30 else 3
    if s["Context"] < 6:
        tips.append("Add background: audience, purpose or domain.")
    s["Format"] = 10 if re.search(r"json|table|bullet|markdown|format|list|\d+ (words|sentences|points|bullets)", p) else 3
    if s["Format"] < 5:
        tips.append("Specify the output format and length.")
    s["Constraints"] = 10 if re.search(r"must|do not|don't|avoid|only|limit|under \d+|maximum|at most", p) else 3
    if s["Constraints"] < 5:
        tips.append("Add constraints (tone, length, what to avoid).")
    s["Reusability"] = min(10, 3 + 2 * len(variables(body)))
    if not variables(body):
        tips.append("Use {{variables}} so the prompt becomes a reusable template.")
    return dict(scores=s, overall=round(sum(s.values()) / len(s) * 10), tips=tips, tokens=tokens(body), words=len(words))


def diff(a, b):
    out = []
    for line in difflib.ndiff(a.splitlines(), b.splitlines()):
        tag = line[:2]
        if tag in ("+ ", "- ", "  "):
            out.append({"t": {"+ ": "add", "- ": "del", "  ": "same"}[tag], "s": line[2:]})
    return out
