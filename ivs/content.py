"""Turns catalog references / story files into normalized Content objects (always verified at build time)."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
import yaml
from .quran import Quran, SURAH_NAMES
from .hadith import Hadith
from .catalog import QURAN, HADITH, script_for

@dataclass
class Segment:
    ar: str = ""
    ur: str = ""
    en: str = ""
    label: str = ""                      # e.g. "Al-Baqarah 2:153"
    audio_ref: tuple[int, int] | None = None   # (surah, ayah) for recitation lookup
    kind: str = "verse"                  # "verse" (Arabic + translations, recitation) | "narration" (en/ur caption)
    action: str = "none"                 # faceless-actor action (anim.ACTIONS)
    scene: str = ""                      # animated scenery tag for stories (see anim.SCENES)
    line: int = -1                       # index of the story line this segment came from (for the Director)

@dataclass
class Content:
    category: str
    key: str
    theme: str
    hook: str
    segments: list[Segment]
    source: dict
    reference_line: str
    needs_review: bool = False
    review_reason: str = ""
    ayat: list[tuple[int, int]] = field(default_factory=list)
    series: str = ""
    hook_ur: str = ""
    hook_candidates_author: list = field(default_factory=list)
    cta: str = ""
    hook_action: str = "none"
    script: dict | None = None            # {'context':{en,ur}, 'takeaway':{en,ur}, 'reviewed':bool}

    def similarity_text(self) -> str:
        return " ".join(s.ar + " " + s.en for s in self.segments)

def surah_label(s: int) -> str:
    return f"Surah {SURAH_NAMES.get(s, s)}"

def build_quran(q: Quran, entry: tuple) -> tuple[Content | None, dict]:
    s, a1, a2, theme, hook, expect = entry
    rep = q.verify(s, a1, a2)
    if rep["ok"]:
        en = " ".join(q.range_text("en", s, a1, a2))
        if expect.lower() not in en.lower():
            rep["ok"] = False
            rep["problems"].append(f"expected keyword '{expect}' not in English translation: wrong reference?")
    if not rep["ok"]:
        return None, rep
    rng = f"{a1}" if a1 == a2 else f"{a1}-{a2}"
    segs = [Segment(ar=q.ayah("ar", s, a), ur=q.ayah("ur", s, a), en=q.ayah("en", s, a),
                    label=f"{SURAH_NAMES.get(s, 'Surah ' + str(s))} {s}:{a}", audio_ref=(s, a)) for a in range(a1, a2 + 1)]
    ed = rep["editions"]
    src = {"type": "quran", "surah": s, "ayah_from": a1, "ayah_to": a2, "verification": rep,
           "translations": {"ur": ed["ur"]["description"], "en": ed["en"]["description"]}}
    key = f"quran:{s}:{rng}"
    return Content("quran_ayah", key, theme, hook, segs, src,
                   f"{surah_label(s)} ({s}:{rng})", ayat=[(s, a) for a in range(a1, a2 + 1)], script=script_for(key)), rep

SEQ_ORDER = list(range(114, 77, -1)) + list(range(77, 0, -1))      # Juz Amma first (short surahs), then the rest

def seq_chunks(q: Quran):
    """Endless-in-practice pool: the whole Quran in order, cut at ayah boundaries into 1-4 ayat (<=240 Arabic chars). Pure recitation + translation, no editorial text."""
    for s in SEQ_ORDER:
        n = q.verse_count(s); a = 1
        while a <= n:
            b, chars = a, len(q.ayah("ar", s, a))
            while b < n and b - a < 3 and chars + len(q.ayah("ar", s, b + 1)) <= 240:
                b += 1; chars += len(q.ayah("ar", s, b))
            yield (s, a, b); a = b + 1

def build_quran_seq(q: Quran, s: int, a1: int, a2: int) -> tuple[Content | None, dict]:
    rep = q.verify(s, a1, a2)
    if not rep["ok"]: return None, rep
    rng = f"{a1}" if a1 == a2 else f"{a1}-{a2}"
    segs = [Segment(ar=q.ayah("ar", s, a), ur=q.ayah("ur", s, a), en=q.ayah("en", s, a), label=f"{SURAH_NAMES.get(s, 'Surah ' + str(s))} {s}:{a}", audio_ref=(s, a)) for a in range(a1, a2 + 1)]
    ed = rep["editions"]
    src = {"type": "quran", "surah": s, "ayah_from": a1, "ayah_to": a2, "verification": rep, "sequence": True,
           "translations": {"ur": ed["ur"]["description"], "en": ed["en"]["description"]}}
    sl = surah_label(s); vs = f"verse {a1}" if a1 == a2 else f"verses {a1} to {a2}"
    T = [f"Have you reflected on {sl}, {vs}?", f"Do you know what {sl} says in {vs}?", f"Can you hear the calm in {sl}, {vs}?", f"Have you listened closely to {sl}, {vs}?"]
    return Content("quran_ayah", f"quran:{s}:{rng}", sl, T[(s + a1) % len(T)], segs, src,
                   f"{surah_label(s)} ({s}:{rng})", ayat=[(s, a) for a in range(a1, a2 + 1)], script=None), rep

def build_hadith(h: Hadith, entry: dict) -> tuple[Content | None, dict]:
    r = h.build(entry)
    if not r["ok"]:
        return None, r
    seg = Segment(ar=r["ar"], ur=r["ur"], en=r["en"], label=f"{r['source']['collection']} {entry['number']}")
    c = Content("hadith", f"hadith:{entry['collection']}:{entry['number']}", entry["theme"], entry["hook"], [seg],
                {"type": "hadith", **r["source"], "verification": {k: r[k] for k in ("problems", "grades")}},
                f"{r['source']['collection']}, {entry['book_ref']} (no. {entry['number']})",
                needs_review=True, script=script_for(f"hadith:{entry['collection']}:{entry['number']}"),
                review_reason="Hadith: automated checks cannot establish authenticity; scholar/human review required.")
    return c, r

SPLIT_TARGET = [60.0]        # set from config video.length_seconds by the pipeline

def _line_seconds(l: dict) -> float:
    from .subtitles import read_seconds
    if "quran" in l:
        rng = str(l["quran"]).split(":")[-1]; a1, _, a2 = rng.partition("-"); return 9.0 * (int(a2 or a1) - int(a1) + 1)
    n = l.get("narration") or {}      # calibrated on real renders: English narration speech (Urdu is text only)
    return max(4.5, 1.6 + 0.07 * len(n.get("en", "")), read_seconds(n.get("ur", ""), "ur") * 0.8)

def split_story(d: dict, target: float = 60.0, tolerance: float = 1.25) -> list[dict]:
    """A story longer than target*tolerance is cut at LINE boundaries into numbered parts of about `target` seconds (hook ~3.5 s + outro ~4.5 s included).
    Author lines are never edited or reordered; each part is its own unique item (id-p1, id-p2 ...). Short stories are returned unchanged."""
    lines = d.get("lines", []); body = target - 8.0
    if sum(_line_seconds(l) for l in lines) + 8.0 <= target * tolerance or len(lines) < 4: return [d]
    n = max(2, round(sum(_line_seconds(l) for l in lines) / body)); goal = sum(_line_seconds(l) for l in lines) / n
    parts, cur, acc = [], [], 0.0
    for i, l in enumerate(lines):
        cur.append(l); acc += _line_seconds(l)
        if acc >= goal and len(parts) < n - 1 and len(lines) - i - 1 >= 2: parts.append(cur); cur, acc = [], 0.0
    if cur: parts.append(cur)
    if len(parts) < 2: return [d]
    out = []
    for k, ls in enumerate(parts, 1):
        p = dict(d); p["id"] = f"{d['id']}-p{k}"; p["title"] = f"{d.get('title', d['id'])} (Part {k}/{len(parts)})"; p["lines"] = ls; p["_part"] = (k, len(parts))
        if k > 1: p["hook"] = f"{d.get('title', d['id'])}, part {k}: what happened next?"; p["hook_candidates"] = []; p["hook_action"] = ls[0].get("action", "none")
        out.append(p)
    return out

def load_stories(dir_: Path, split: bool = True) -> list[dict]:
    out = []
    for p in sorted(Path(dir_).glob("*.yaml")):
        if p.name.startswith("_"):
            continue
        d = yaml.safe_load(p.read_text(encoding="utf-8")) | {"_file": p.name}
        if (d.get("draft") or {}).get("needs_human_review"): continue        # AI/auto drafts stay out of production until a human deletes this flag (the review act)
        out.extend(split_story(d, float(SPLIT_TARGET[0])) if split else [d])
    return out

def build_story(d: dict, q: Quran | None = None) -> tuple[Content | None, dict]:
    """Stories are HUMAN-authored YAML. Verse lines (`quran: "105:1-2"`) are pulled from the verified Quran source;
    narration lines are the author's words. Always needs_review. No people are ever drawn (anim.py is scenery only)."""
    from .anim import SCENES, ACTIONS
    problems, segs, ayat, ver = [], [], [], {"ok": True, "problems": []}
    if not d.get("sources"): problems.append("story has no source references")
    if not d.get("lines"): problems.append("story has no lines")
    from . import docfacts; problems += docfacts.validate_claims(d)
    for i, l in enumerate(d.get("lines", [])):
        scene = l.get("scene", "sky_stars"); action = l.get("action", "none")
        if action not in ACTIONS: problems.append(f"line {i}: unknown action '{action}' (only generic faceless actors exist; prophets/companions are never drawn)")
        if scene not in SCENES: problems.append(f"line {i}: unknown scene '{scene}'")
        if "quran" in l:
            if q is None: problems.append("quran line but no Quran provider"); continue
            sur, rng = str(l["quran"]).split(":"); a1, _, a2 = rng.partition("-"); sur, a1, a2 = int(sur), int(a1), int(a2 or a1)
            rep = q.verify(sur, a1, a2)
            if rep["ok"] and l.get("expect") and l["expect"].lower() not in " ".join(q.range_text("en", sur, a1, a2)).lower():
                rep["ok"] = False; rep["problems"].append(f"expected '{l['expect']}' not in translation: wrong reference?")
            if not rep["ok"]: problems += [f"line {i}: {p}" for p in rep["problems"]]; continue
            ver = {"ok": True, "problems": [], "editions": rep["editions"], "verified_on": rep["verified_on"]}
            for a in range(a1, a2 + 1):
                segs.append(Segment(ar=q.ayah("ar", sur, a), ur=q.ayah("ur", sur, a), en=q.ayah("en", sur, a),
                                    label=f"{SURAH_NAMES.get(sur, 'Surah ' + str(sur))} {sur}:{a}", audio_ref=(sur, a), kind="verse", scene=scene, action=action, line=i))
                ayat.append((sur, a))
        else:
            n = l.get("narration") or {}
            if not (n.get("en") or n.get("ur")): problems.append(f"line {i}: needs `quran` or `narration`"); continue
            segs.append(Segment(ur=n.get("ur", ""), en=n.get("en", ""), label="", kind="narration", scene=scene, action=action, line=i))
    if problems:
        return None, {"ok": False, "problems": problems}
    ed = ver.get("editions")
    src = {"type": "story", "title": d["title"], "sources": d["sources"], "file": d["_file"], "verification": ver}
    if d.get("claims"): src["claims"] = d["claims"]
    if d.get("views"): src["views"] = d["views"]
    if ed: src["translations"] = {"ur": ed["ur"]["description"], "en": ed["en"]["description"]}
    tk = d.get("takeaway")
    script = {"takeaway": tk, "reviewed": False, "author": "story author"} if tk else None
    c = Content("story", f"story:{d['id']}", d.get("theme", "story"), d.get("hook", d["title"]), segs, src,
                "Sources: " + "; ".join(d["sources"]), needs_review=True, ayat=ayat, script=script,
                review_reason="Stories always require human review of every claim against the cited sources.")
    c.hook_candidates_author = list(d.get("hook_candidates", []) or []); c.hook_ur = d.get("hook_ur", ""); c.hook_action = d.get("hook_action", "none")
    if c.hook_action not in ACTIONS: return None, {"ok": False, "problems": [f"unknown hook_action '{c.hook_action}'"]}
    return c, {"ok": True, "problems": []}
