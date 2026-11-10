"""Bridge to Lemo-Opuscar (github.com/lemomo-ai/lemo-opuscar, MIT): a Claude Code plugin whose agent directs a short film in code
from one of 59 STYLE.md prompts. IMPORTANT HONESTY: it needs an LLM agent session (tokens) for every film, so it is NOT free to run
unattended and is NOT part of the GitHub Actions flow. This module (1) vendors the MIT style prompts under third_party/, (2) ranks
them by how figure-free they are (our rules: no faces, no depiction of Allah/prophets), (3) writes a brief containing our VERIFIED
text, sources and religious guard rails to paste into that plugin on your own PC when you choose to spend tokens on a premium film."""
from __future__ import annotations
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STY = ROOT / "third_party" / "lemo-opuscar" / "styles"
FIGURE_WORDS = re.compile(r"\b(faces?|characters?|persons?|people|figures?|portraits?|puppets?|actors?|humans?|crowd|swordsman|hero(?:es)?)\b", re.I)
RELIGIOUS_RISK = re.compile(r"\b(saints?|halos?|crosses|cross|angels?|deity|gods?|temple|buddha|shrine)\b", re.I)

def styles() -> list[dict]:
    out = []
    for d in sorted(STY.glob("*/")):
        sj = d / "style.json"; md = d / "STYLE.md"
        if not md.exists(): continue
        meta = json.loads(sj.read_text(encoding="utf-8")) if sj.exists() else {}
        txt = md.read_text(encoding="utf-8"); words = max(1, len(txt.split()))
        fig = len(FIGURE_WORDS.findall(txt)); rel = len(RELIGIOUS_RISK.findall(txt))
        out.append({"slug": d.name, "name": meta.get("en", d.name), "category": meta.get("category_en", ""), "figure_mentions": fig,
                    "figure_density": round(fig * 1000 / words, 2), "religious_imagery_mentions": rel, "fps": meta.get("fps")})
    return sorted(out, key=lambda s: (s["figure_density"], s["religious_imagery_mentions"]))

def verified_text(pipe, key: str) -> dict:
    """key: 'story:<id>' or 'quran:<surah>:<a>[-<b>]' -> verified Content as dict (no network if data cached)."""
    from . import content as C
    from .catalog import QURAN
    if key.startswith("story:"):
        d = next((d for d in C.load_stories(pipe.sel.stories_dir) if f"story:{d['id']}" == key), None)
        c = C.build_story(d, pipe.sel.quran)[0] if d else None
    else:
        _, s, rng = key.split(":"); a1, _, a2 = rng.partition("-"); a1 = int(a1); a2 = int(a2 or a1)
        e = next((e for e in QURAN if (e[0], e[1], e[2]) == (int(s), a1, a2)), None)
        c = C.build_quran(pipe.sel.quran, e)[0] if e else C.build_quran_seq(pipe.sel.quran, int(s), a1, a2)[0]
    if c is None: raise SystemExit("content failed verification: nothing to brief")
    return {"key": c.key, "title": (c.source.get("title") if isinstance(c.source.get("title"), str) else None) or c.reference_line, "theme": c.theme, "category": c.category,
            "lines": [{"ar": s.ar, "ur": s.ur, "en": s.en, "label": s.label} for s in c.segments], "source": c.source}

RULES = """## Non-negotiable rules (from the Islamic video engine)
1. **No faces, no human figures with features.** Silhouettes/shadows only. **Never depict Allah, any prophet or messenger, the Sahaba, or angels** in any form (not as figures, shadows, light-shaped people or text-as-people).
2. **Quran text is used exactly as given below** (Arabic with tashkeel, as written). Do not reword, abbreviate, re-order or "improve" it. Do not add, invent or paraphrase any verse, hadith, quote or historical detail beyond the lines supplied.
3. **No synthetic voice for the Quran.** Recitation must be an authentic human recording that I supply (`recitation.mp3`); if none is supplied, show the verses as text only. Narration of non-Quran lines may use Kokoro (offline, free).
4. **No music over recitation.** Light ambience only. No music with the Quran verses.
5. **No religious imagery of other faiths, no idols, no symbolic "gods"**, no clickbait claims ("shocking", "secret", guarantees).
6. Vertical **1080x1920, 24 fps, 20-120 seconds**. Subtitles burned in (Arabic, Urdu, English) and exported as .srt.
7. Credit the translations and sources on the last card exactly as listed below.
8. Deliver `TREATMENT.md` first and wait for my approval of the storyboard before rendering.
"""

INTRO = {
    "lemo": "Use the Lemo-Opuscar plugin: `claude plugin marketplace add lemomo-ai/lemo-opuscar` then `claude plugin install lemo-opuscar@lemolab`. This costs Claude tokens (about 30-60 minutes of agent time per film).",
    "bang": "Use the Bang Motion skill: `/plugin marketplace add bangtutorial/bang-motion` then `/plugin install bang-motion@bang-motion`. Build a single index.html with window.OPENER.tl, **9:16 (1080x1920)**, kinetic typography, GSAP. Render it free with `python -m ivs bang-render index.html --out film.mp4`. Uses Claude tokens.",
    "motion-kit": "Use motion-kit (github.com/kiselas/every-frame-is-code, MIT; copy in third_party/motion-kit/): read its SKILL.md and 00-agent-brief.md first. Build ONE html page where a frame is a pure function of time and expose `window.__meta={W:1080,H:1920,FPS:30,DURATION:s}`, `window.__draw(t)`, `window.__ready=true`. Render it free with `python -m ivs bang-render page.html --out film.mp4`. Uses Claude tokens.",
    "animated-shorts": "Claude Animated Shorts (github.com/mromidev/claude-animated-shorts, MIT; docs in third_party/claude-animated-shorts/). WARNING: its characters are cartoon cards WITH FACES and it renders through Remotion (check Remotion's licence terms yourself: free use is limited to individuals/small teams as far as I know). Under our rules use only the world/camera/lighting/grade ideas and make every figure a faceless silhouette or back view. If that is not possible, do not use it.",
    "opus-studio": "Opus Video Studio (github.com/xdis/opus-video-studio, MIT; docs in third_party/opus-video-studio/). Use ONLY its Route A (code-drawn Canvas/Three.js/Blender frames). Route B needs an Apple-silicon Mac and large local AI models, Route C needs paid APIs: do not use them. Its voice step uses edge-tts (online, unofficial): never for Quran. Render a `window.__draw(t)` page free with `python -m ivs bang-render`.",
}

def brief(pipe, key: str, style: str | None = None, tool: str = "lemo") -> str:
    avail = {s["slug"]: s for s in styles()}
    if style and style not in avail: raise SystemExit(f"unknown style '{style}'. Run: python -m ivs lemo-styles")
    c = verified_text(pipe, key); st = avail.get(style) if style else None
    L = [f"# Film brief: {c['title']}", "", f"Style: **{st['name']}** (`{style}`)" if st else "Style: you choose from the style list (prefer figure-free ones).", "",
         INTRO.get(tool, INTRO["lemo"]), "",
         RULES, "## Verified text (do not alter)", ""]
    for i, s in enumerate(c["lines"], 1):
        L += [f"### Line {i}: {s['label'] or 'narration (editorial context, not Quran)'}", f"- Arabic: {s['ar'] or '(none: narrated line)'}", f"- Urdu: {s['ur']}", f"- English: {s['en']}", ""]
    tr = c["source"].get("translations") or {}
    L += ["## Sources to credit", f"- Quran text: fawazahmed0/quran-api (SHA-256 pinned, cross-checked against a second Arabic edition)"]
    for k, v in tr.items(): L.append(f"- {k.upper()} translation: {v}")
    L += ["", f"Theme: {c['theme']}", "", "Duration target: 45-90 s. Keep the first 3 seconds a hook that shows motion, not a logo."]
    return "\n".join(L) + "\n"
