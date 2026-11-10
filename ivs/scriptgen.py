"""AI script drafting for stories. The AI may only REPHRASE material it is given (the verified translation and the author's sourced notes).
Free + local: Ollama on the user's own PC (e.g. `ollama pull qwen2.5:3b`). Without it, a deterministic fallback drafts from the translation alone.
Every draft goes to content/stories/drafts/ and still needs HUMAN review before it is moved into content/stories/ (and again at approval)."""
from __future__ import annotations
import json, re
from pathlib import Path
import requests, yaml
from .quran import SURAH_NAMES
from .hooks import FORBIDDEN

ARABIC = re.compile(r"[؀-ۿ]")
QURANIC_MARKS = re.compile(r"[ؐ-ًؚ-ٟۖ-ٰۭ]")        # tashkeel/tajweed marks: never in AI-written lines
VISUAL_BAN = re.compile(r"\b(looked like|his face|her face|appearance of|handsome|beard|wearing|dressed in)\b", re.I)
STOP = set("the a an and of to in is was were are be been it its this that these those for with as by on at from or but not he she they them his her their we you our your who which what when then so than also into upon over after before about has have had will would can could may might do did does".split())

class Ollama:
    def __init__(self, url="http://localhost:11434", model="qwen2.5:3b", timeout=300):
        self.url, self.model, self.timeout = url.rstrip("/"), model, timeout
    def available(self) -> bool:
        try: return requests.get(self.url + "/api/tags", timeout=3).ok
        except Exception: return False
    def generate(self, prompt: str) -> str:
        r = requests.post(self.url + "/api/generate", json={"model": self.model, "prompt": prompt, "stream": False, "format": "json", "options": {"temperature": 0.4}}, timeout=self.timeout)
        r.raise_for_status(); return r.json()["response"]

class Gemini:
    """Google Gemini API, FREE tier (key from https://aistudio.google.com/apikey, no card; keep billing OFF so it can never charge).
    Same interface as Ollama. The key is read from GEMINI_API_KEY and sent only in the x-goog-api-key header (never in a URL or log).
    Only public text goes out: the verified translation + your sourced notes. Output is still validated line by line and still needs human review."""
    URL = "https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent"
    def __init__(self, key=None, model=None, timeout=90, tries=4):
        import os
        self.key = key or os.environ.get("GEMINI_API_KEY", ""); self.model = model or os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        self.timeout, self.tries = timeout, tries
    def available(self) -> bool: return bool(self.key.strip())
    def generate(self, prompt: str) -> str:
        import time
        body = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.4, "responseMimeType": "application/json"}}
        err = None
        for i in range(self.tries):
            r = requests.post(self.URL.format(m=self.model), json=body, headers={"x-goog-api-key": self.key}, timeout=self.timeout)
            if r.status_code in (429, 500, 503): err = f"HTTP {r.status_code}"; time.sleep(min(60, 8 * 2 ** i)); continue   # free-tier rate limit: back off, never pay
            if r.status_code in (400, 403) and "API key" in r.text: raise RuntimeError("Gemini rejected the API key")
            r.raise_for_status()
            try: return r.json()["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError): raise RuntimeError("Gemini returned no text (blocked or empty): " + r.text[:200])
        raise RuntimeError(f"Gemini free-tier limit/unavailable ({err})")

# provider presets: (env key var, base url, default model, free tier?)
PRESETS = {
    "groq":       ("GROQ_API_KEY", "https://api.groq.com/openai/v1", "llama-3.3-70b-versatile", True),
    "openrouter": ("OPENROUTER_API_KEY", "https://openrouter.ai/api/v1", "meta-llama/llama-3.3-70b-instruct:free", True),
    "mistral":    ("MISTRAL_API_KEY", "https://api.mistral.ai/v1", "mistral-small-latest", True),
    "together":   ("TOGETHER_API_KEY", "https://api.together.xyz/v1", "meta-llama/Llama-3.3-70B-Instruct-Turbo", False),
    "deepseek":   ("DEEPSEEK_API_KEY", "https://api.deepseek.com/v1", "deepseek-chat", False),
    "openai":     ("OPENAI_API_KEY", "https://api.openai.com/v1", "gpt-4o-mini", False),
}

class OpenAICompat:
    """Any OpenAI-compatible chat API (OpenAI, Groq, OpenRouter, Mistral, Together, DeepSeek, LM Studio, vLLM...).
    Generic: AI_API_KEY + AI_BASE_URL + AI_MODEL. Or a provider's own key var (see PRESETS). Key goes only in the Authorization header.
    NOTE: providers marked non-free in PRESETS may bill you; the $0 guarantee only holds on free tiers."""
    def __init__(self, key=None, base=None, model=None, name="custom", timeout=90, tries=4):
        self.key, self.base, self.model, self.name, self.timeout, self.tries = key or "", (base or "").rstrip("/"), model or "", name, timeout, tries
    def available(self) -> bool: return bool(self.key.strip() and self.base and self.model)
    def generate(self, prompt: str) -> str:
        import time
        body = {"model": self.model, "temperature": 0.4, "messages": [{"role": "user", "content": prompt}]}
        err = None
        for i in range(self.tries):
            r = requests.post(self.base + "/chat/completions", json=body, headers={"Authorization": "Bearer " + self.key}, timeout=self.timeout)
            if r.status_code in (429, 500, 502, 503): err = f"HTTP {r.status_code}"; time.sleep(min(60, 8 * 2 ** i)); continue
            if r.status_code in (401, 403): raise RuntimeError(f"{self.name} rejected the API key")
            r.raise_for_status()
            try: return r.json()["choices"][0]["message"]["content"]
            except (KeyError, IndexError): raise RuntimeError(f"{self.name} returned no text: " + r.text[:200])
        raise RuntimeError(f"{self.name} rate limit/unavailable ({err})")

class Anthropic:
    """Claude API (ANTHROPIC_API_KEY). Paid per token - not part of the $0 guarantee."""
    def __init__(self, key=None, model=None, timeout=90):
        import os
        self.key = key or os.environ.get("ANTHROPIC_API_KEY", ""); self.model = model or os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5"); self.timeout = timeout
    def available(self) -> bool: return bool(self.key.strip())
    def generate(self, prompt: str) -> str:
        r = requests.post("https://api.anthropic.com/v1/messages", headers={"x-api-key": self.key, "anthropic-version": "2023-06-01"}, timeout=self.timeout,
                          json={"model": self.model, "max_tokens": 2000, "messages": [{"role": "user", "content": prompt}]})
        if r.status_code in (401, 403): raise RuntimeError("Anthropic rejected the API key")
        r.raise_for_status()
        return r.json()["content"][0]["text"]

def _others(prefer: str, model: str | None):
    import os
    out = []
    if prefer in ("auto", "custom") and os.environ.get("AI_API_KEY"):
        out.append(OpenAICompat(os.environ["AI_API_KEY"], os.environ.get("AI_BASE_URL", "https://api.openai.com/v1"), model or os.environ.get("AI_MODEL", ""), "custom"))
    for name, (kv, base, dm, _free) in PRESETS.items():
        if prefer in ("auto", name) and os.environ.get(kv):
            out.append(OpenAICompat(os.environ[kv], os.environ.get(name.upper() + "_BASE_URL", base), model or os.environ.get(name.upper() + "_MODEL", dm), name))
    if prefer in ("auto", "anthropic", "claude"): out.append(Anthropic(model=model if prefer != "auto" else None))
    return [o for o in out if o.available()]

def pick_llm(model: str | None = None, prefer: str | None = None):
    """IVS_LLM=auto (default) tries, in order: Gemini, any OpenAI-compatible key (AI_API_KEY/AI_BASE_URL/AI_MODEL or GROQ_/OPENROUTER_/MISTRAL_/TOGETHER_/DEEPSEEK_/OPENAI_API_KEY),
    Anthropic, local Ollama, else None (deterministic fallback). Force one with IVS_LLM=gemini|custom|groq|openrouter|mistral|together|deepseek|openai|anthropic|ollama|none."""
    import os
    prefer = (prefer or os.environ.get("IVS_LLM", "auto")).lower()
    if prefer == "none": return None
    if prefer in ("auto", "gemini"):
        g = Gemini(model=model if prefer == "gemini" else None)
        if g.available(): return g
    o2 = _others(prefer, model)
    if o2: return o2[0]
    if prefer in ("auto", "ollama"):
        o = Ollama(model=model or os.environ.get("OLLAMA_MODEL", "qwen2.5:3b"))
        if o.available(): return o
    return None

PROMPT = """You write short narration for an Islamic story video. STRICT RULES:
- Use ONLY the SOURCE MATERIAL below. Do not add events, names, numbers, dates, causes or details that are not in it.
- Do not quote or write Arabic. Do not describe any prophet's appearance. Never invent hadith, scholars or opinions.
- If you are unsure, write less. Plain, calm English; Urdu must be simple and correct.
- No clickbait, no claims of certainty beyond the source.
Return JSON: {{"hook": "<one question, <= 12 words>", "hook_candidates": ["...","..."], "narration": [{{"after_ayah": <int>, "en": "...", "ur": "..."}}], "takeaway": {{"en": "...", "ur": "..."}}}}
Write 4 to 7 narration items, each 1-2 sentences, each tied to the source (after_ayah = the ayah number it follows, or 0 for the introduction).

TITLE: {title}
SOURCE MATERIAL (verified translation, then author's notes):
{source}
"""

def _content_words(t: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]{4,}", t.lower()) if w not in STOP}

def check_line(text: str, lang: str, corpus: str, support_min: float = 0.3) -> str | None:
    """Returns a rejection reason or None. Guards against invention, Arabic/Quran text, forbidden or visual-description language."""
    if not text.strip(): return "empty"
    if lang == "en" and ARABIC.search(text): return "Arabic text in English line"
    if QURANIC_MARKS.search(text): return "tashkeel/Quranic marks: AI must never write Quranic text"
    if any(re.search(p, text.lower()) for p in FORBIDDEN): return "forbidden clickbait/certainty phrase"
    if VISUAL_BAN.search(text): return "describes a person's appearance"
    if lang != "en": return None
    cw = _content_words(text); cc = _content_words(corpus)
    if cw and len(cw & cc) / len(cw) < support_min: return f"not supported by the source material ({len(cw & cc)}/{len(cw)} words)"
    for n in re.findall(r"\b\d[\d,\.]*\b", text):
        if n not in corpus: return f"number '{n}' not in source"
    for name in re.findall(r"(?<![.!?]\s)(?<!^)\b[A-Z][a-z]{3,}\b", text):
        if name.lower() not in corpus.lower(): return f"name '{name}' not in source"
    return None

ENV_KEYS = [(("sea", "ship", "boat", "fish", "wave"), "sea_calm"), (("darkness", "night"), "night_sea"), (("mountain", "hill"), "mountain_dawn"), (("star", "sky", "heaven"), "sky_stars")]
ACT_KEYS = [(("elephant",), "army_march"), (("bird", "birds"), "flock"), (("journey", "winter", "summer", "caravan", "travel"), "caravan"), (("gather", "people", "crowd"), "crowd_gather")]

def _scene_action(text: str) -> tuple[str, str]:
    low = text.lower(); scene = next((s for ks, s in ENV_KEYS if any(k in low for k in ks)), "desert_dawn")
    return scene, next((a for ks, a in ACT_KEYS if any(k in low for k in ks)), "none")

def _fallback(title: str, sur: int, a1: int, a2: int, en: list[str]) -> dict:
    nm = SURAH_NAMES.get(sur, f"Surah {sur}"); n = a2 - a1 + 1
    return {"hook": f"What does {nm} ask us to reflect on?", "hook_candidates": [f"What can we learn from {nm}?", f"Have you reflected on {nm}?"],
            "narration": [{"after_ayah": 0, "en": f"{nm} has {n} ayat. Let us read them and reflect.", "ur": ""}],
            "takeaway": {"en": f"Reflect on the ayat of {nm} and what they teach us.", "ur": ""}}

def draft_story(quran, ref: str, story_id: str, title: str, theme: str, notes: list[dict] | None = None, llm=None, out_dir: Path | None = None) -> tuple[dict | None, dict]:
    """notes: [{"text": "...", "source": "Ibn Kathir, Tafsir of Surah ..."}] written/pasted by the human. Returns (story_dict, report)."""
    sur, rng = ref.split(":"); a1, _, a2 = rng.partition("-"); sur, a1, a2 = int(sur), int(a1), int(a2 or a1)
    rep = quran.verify(sur, a1, a2)
    if not rep["ok"]: return None, {"ok": False, "problems": rep["problems"]}
    en = quran.range_text("en", sur, a1, a2); notes = notes or []
    corpus = " ".join(en + [n["text"] for n in notes] + [title])
    src = "\n".join([f"Ayah {a1 + i}: {t}" for i, t in enumerate(en)] + [f"Note ({n['source']}): {n['text']}" for n in notes])
    report = {"ok": True, "mode": "fallback", "dropped": [], "problems": []}
    plan = None
    if llm is not None and (not hasattr(llm, "available") or llm.available()):
        try:
            plan = json.loads(llm.generate(PROMPT.format(title=title, source=src))); report["mode"] = "llm"
        except Exception as e:
            report["problems"].append(f"LLM failed, using fallback: {e}")
    if plan is None: plan = _fallback(title, sur, a1, a2, en)
    items = []
    for it in plan.get("narration", []):
        why = check_line(it.get("en", ""), "en", corpus) or (check_line(it["ur"], "ur", corpus) if it.get("ur") else None)
        if why: report["dropped"].append({"line": it.get("en", "")[:80], "why": why}); continue
        items.append(it)
    if report["mode"] == "llm" and len(items) < 3:                       # too little survived validation: do not ship a thin AI draft
        report["problems"].append("fewer than 3 narration lines passed validation; used fallback"); plan = _fallback(title, sur, a1, a2, en); items = plan["narration"]; report["mode"] = "fallback"
    hook = plan.get("hook", "")
    if check_line(hook, "en", corpus, 0.0): hook = _fallback(title, sur, a1, a2, en)["hook"]
    cands = [h for h in plan.get("hook_candidates", []) if h and not check_line(h, "en", corpus, 0.0)][:3] or _fallback(title, sur, a1, a2, en)["hook_candidates"]
    tk = plan.get("takeaway") or {}
    if check_line(tk.get("en", ""), "en", corpus) or (tk.get("ur") and check_line(tk["ur"], "ur", corpus)): tk = _fallback(title, sur, a1, a2, en)["takeaway"]
    lines = []
    for it in [i for i in items if int(i.get("after_ayah", 0)) <= 0]:
        sc, ac = _scene_action(it["en"]); lines.append({"scene": sc, "action": ac, "narration": {k: it[k] for k in ("en", "ur") if it.get(k)}})
    for i, a in enumerate(range(a1, a2 + 1)):
        sc, ac = _scene_action(en[i]); lines.append({"scene": sc, "action": ac, "quran": f"{sur}:{a}", "expect": next(iter(sorted(_content_words(en[i]), key=len, reverse=True)), "")})
        for it in [x for x in items if int(x.get("after_ayah", 0)) == a - a1 + 1]:
            sc2, ac2 = _scene_action(it["en"]); lines.append({"scene": sc2, "action": ac2, "narration": {k: it[k] for k in ("en", "ur") if it.get(k)}})
    story = {"id": story_id, "title": title, "theme": theme, "hook": hook, "hook_candidates": cands,
             "sources": [f"Quran {ref} ({SURAH_NAMES.get(sur, 'Surah ' + str(sur))})"] + [n["source"] for n in notes], "lines": lines, "takeaway": tk,
             "draft": {"generated_by": report["mode"], "needs_human_review": True}}
    report["lines"] = len(lines)
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"{story_id}.yaml").write_text("# DRAFT written by the script assistant. REVIEW every line against its source, then move to content/stories/.\n" +
                                                  yaml.safe_dump(story, allow_unicode=True, sort_keys=False, width=100), encoding="utf-8")
    return story, report
