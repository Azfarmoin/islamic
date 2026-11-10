"""Documentary layer: evidence status for story claims (VERIFIED / DISPUTED / UNCERTAIN), hedging check, chapters, production report.
Nothing here creates facts. Claims are written by the story author in the YAML (`claims:`); this module only validates and presents them.
A claim marked disputed/uncertain whose narration reads like established fact BLOCKS the story (STOP PRODUCTION), as the documentary spec requires."""
from __future__ import annotations
import re

STATUSES = ("verified", "disputed", "uncertain")
HEDGE = re.compile(r"\b(report|reports|reported|according|some|scholars?|commentar\w+|tradition\w*|said|narrat\w+|it is said|many|differ\w*|may|might|perhaps|believed)\b", re.I)

def validate_claims(story: dict) -> list[str]:
    probs = []; texts = [(l.get("narration") or {}).get("en", "") for l in story.get("lines", [])]
    for i, c in enumerate(story.get("claims") or []):
        st = str(c.get("status", "")).lower()
        if st not in STATUSES: probs.append(f"claim {i}: status must be one of {STATUSES}"); continue
        if not c.get("text") or not c.get("source"): probs.append(f"claim {i}: needs `text` and `source`")
        m = c.get("match")
        if m and st != "verified":
            hit = [t for t in texts if m.lower() in t.lower()]
            if hit and not all(HEDGE.search(t) for t in hit): probs.append(f"claim {i} is {st.upper()} but the narration states it as fact (add attribution such as 'reports say'): {m!r}")
    return probs

def claims_for(content) -> list[dict]:
    allc = (content.source or {}).get("claims") or []
    if not allc: return []
    narr = " ".join(s.en for s in content.segments).lower()
    return [c for c in allc if not c.get("match") or c["match"].lower() in narr]

def evidence_lines(content) -> list[str]:
    cl = claims_for(content)
    if not cl: return []
    out = ["Evidence status of the claims in this video:"]
    for c in cl: out.append(f"- {str(c['status']).upper()}: {c['text']} (source: {c['source']})")
    out.append("VERIFIED = supported by the cited source; DISPUTED = scholars/historians differ; UNCERTAIN = evidence insufficient. Reviewed by the story author, not a scholar.")
    return out

NAMES = {"hook": "Opening", "narration": "The story", "ayah": "Primary source (Quran)", "translation": "Primary source (Quran)", "script": "Reflection", "outro": "Sources"}

def chapters(marks: list[tuple[float, str]]) -> list[str]:
    """YouTube chapters: first at 0:00, at least 3, each >= 10 s long; consecutive duplicates merge."""
    out = []
    for t, k in marks:
        n = NAMES.get(k, "The story")
        if out and out[-1][1] == n: continue
        if out and t - out[-1][0] < 10: continue
        out.append((t, n))
    if len(out) < 3: return []
    return [f"{int(t // 60)}:{int(t % 60):02d} {n}" for t, n in out]

def production_report(content, meta: dict, qc: dict, render: dict) -> str:
    cl = claims_for(content)
    L = [f"# Production report: {content.key}", "", f"- Reference: {content.reference_line}", f"- Duration: {render.get('duration')} s", f"- Audio mode: {render.get('audio_mode')}",
         f"- QC passed: {qc.get('passed')}  (failed: {', '.join(qc.get('failed', [])) or 'none'})", f"- Religious verification: {meta.get('religious_verification')}",
         "", "## Evidence status"] + ([f"- {c['status'].upper()}: {c['text']} ({c['source']})" for c in cl] or ["- No per-claim grading in this item (only verified Quran/hadith text and author narration)."])
    L += ["", "## Not achieved (honest report)", "- No animated map or historical-border engine (no free offline map data bundled).", "- No manuscript images or archaeological photos are generated or shown.",
          "- Scenery is a stylised reconstruction, never evidence. Faces are never drawn.", "- A qualified person must still review narration against the cited sources."]
    return "\n".join(L)
