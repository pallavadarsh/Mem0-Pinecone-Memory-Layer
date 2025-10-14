from __future__ import annotations
import json, re
from dataclasses import dataclass
from typing import List

TOKEN_RE = re.compile(r"[A-Za-z0-9_\-]+")
SECRET_PATTERNS = [
    re.compile(r"sk_[A-Za-z0-9]{16,}"),
    re.compile(r"(?i)api[_-]?key\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}['\"]?"),
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9\-_.]+"),
]

def _tok(t: str): return TOKEN_RE.findall(t.lower())

def redact(text: str) -> tuple[str, bool]:
    out = text; had = False
    for pat in SECRET_PATTERNS:
        if pat.search(out):
            out = pat.sub("<REDACTED>", out); had = True
    return out, had

def specificity(text: str) -> float:
    return min(1.0, len(set(_tok(text))) / 20.0)

def longevity(text: str, mtype: str) -> float:
    base = min(1.0, len(_tok(text)) / 30.0)
    if mtype in {"factual","semantic","procedure"}:
        base = min(1.0, base + 0.15)
    if any(k in text.lower() for k in ["today","now","just now","btw"]):
        base = max(0.0, base - 0.15)
    return base

def final_score(novelty: float, spec: float, longv: float) -> float:
    return 0.35*novelty + 0.35*spec + 0.30*longv

@dataclass
class PolicyConfig:
    dedup_sim_threshold: float = 0.90
    decision_threshold: float = 0.60

def classify_llm(groq_client, text: str, type_hint: str | None) -> tuple[str, str]:
    if type_hint and type_hint.lower() != "auto":
        return type_hint.lower(), "hint"
    system = (
        "You classify memory candidates. Choose exactly one type: "
        "factual, semantic, episodic, preference, task_state, procedure, ltm, stm. "
        "Return strict JSON: {\"type\":\"...\",\"rationale\":\"...\"}. No extra text."
    )
    prompt = (
        "Classify the following text:\n\n"
        f"{text}\n\n"
        "Rules:\n"
        "- factual: concrete statements about systems, endpoints, versions, settings.\n"
        "- semantic: definitions or conceptual relationships (X is Y).\n"
        "- episodic: past interactions/experiences (yesterday/last week/previously/I asked...).\n"
        "- preference: stable user preferences (I prefer, I like, default).\n"
        "- task_state: commitments, todos, reminders, deadlines.\n"
        "- procedure: how-to steps, commands, endpoints, ports.\n"
        "- ltm: long, durable info that doesn't match above.\n"
        "- stm: short, likely only for current session.\n"
        "Respond JSON only."
    )
    raw = groq_client.chat(system, prompt)
    try:
        data = json.loads(raw)
        return data.get("type","stm").lower(), data.get("rationale","")
    except Exception:
        return ("ltm" if len(text.split()) > 12 else "stm"), "fallback"

def is_duplicate_from_matches(matches: List[dict], threshold: float) -> bool:
    for m in matches:
        s = m.get("score")
        if s is not None and s >= threshold:
            return True
    return False