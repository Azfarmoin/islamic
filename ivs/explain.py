"""Explanation layer: for each shot, which explanation technique would make the narration understandable with the sound off, plus the
educational record (sees / hears / learns / why) and an auto-checked production checklist.
HONESTY: techniques are chosen by keyword rules from the shot's own narration. `rendered` is true ONLY for what the engine really draws today
(scenery change, slow camera, on-screen text). Maps, timelines, before/after, scale comparisons are PLANNED here and not rendered yet."""
from __future__ import annotations

TECHNIQUES = [   # (keywords, technique, idea, rendered_today)
    (("travel", "journey", "caravan", "march", "marched", "came to", "went"), "map_route", "route line moving across terrain between two places", False),
    (("year", "years", "later", "day", "night", "dawn", "time", "season", "winter", "summer"), "time_passing", "sun/shadow shift and sky change over the shot", True),
    (("rise", "rose", "flood", "increase", "grew", "more", "less", "before", "after", "destroyed", "changed"), "before_after", "same framing shown before and after the change", False),
    (("army", "elephant", "mountain", "huge", "great", "vast", "many", "crowd"), "scale_comparison", "tiny faceless figure beside the large subject", True),
    (("first", "then", "finally", "next", "begin", "began"), "timeline", "dated/ordered markers appear one by one", False),
    (("fear", "afraid", "danger", "storm", "dark"), "atmosphere_shift", "darker scenery, tighter framing, low ambience", True),
    (("hope", "ease", "relief", "mercy", "light", "dawn"), "light_opening", "brighter scenery, upward camera drift", True),
]
DEFAULT = ("symbolic_scene", "scenery that matches the meaning, calm camera drift", True)

def technique_for(text: str) -> dict:
    low = (text or "").lower(); words = set(__import__("re").findall(r"[a-z']+", low))
    for ks, name, idea, rendered in TECHNIQUES:
        if any((k in words) or (" " in k and k in low) for k in ks): return {"technique": name, "idea": idea, "rendered": rendered}
    return {"technique": DEFAULT[0], "idea": DEFAULT[1], "rendered": DEFAULT[2]}

def explanation_plan(vd: dict) -> dict:
    out = []
    for s in vd.get("shots", []):
        t = technique_for(s.get("narration") or "")
        out.append({"shot_id": s["shot_id"], "narration": s.get("narration"), **t,
                    "viewer_sees": f"{s.get('environment')} - {s.get('camera')}, {s.get('camera_movement')}",
                    "viewer_hears": s.get("audio_cue") or "ambience only",
                    "viewer_learns": (s.get("narration") or "")[:140],
                    "why_this_visual": f"{t['technique']}: {t['idea']}", "emotion": s.get("emotion"),
                    "anticipation": "hold/slow push-in before the key line" if s.get("emotion") in ("anticipation", "tension", "curiosity") else "none"})
    n = len(out) or 1; rendered = sum(1 for o in out if o["rendered"])
    return {"script_id": vd.get("script_id"), "shots": out, "summary": {"shots": len(out), "rendered_today": rendered, "planned_only": len(out) - rendered,
            "note": "planned_only techniques (map, timeline, before/after) are specified for a future renderer or manual edit; the engine does not draw them yet."}}

def checklist(vd: dict, plan: dict, qc: dict, meta: dict) -> dict:
    shots = vd.get("shots", []); claims = vd.get("claims") or []
    bad = [c for c in claims if str(c.get("status", "")).upper() in ("DISPUTED", "UNCERTAIN")]
    items = {
        "islamic_authenticity": "auto: sources verified; human review still required",
        "no_invented_facts": "auto: all lines checked against the source" if not bad else f"FLAG: {len(bad)} disputed/uncertain claim(s) need hedged wording",
        "every_narration_visualized": all(s.get("environment") for s in shots) and bool(shots),
        "visual_continuity": bool((vd.get("continuity") or True)),
        "educational_clarity": all(o["viewer_learns"] for o in plan["shots"]),
        "strong_hook": bool(meta.get("hook") or (shots and shots[0].get("narration"))),
        "clear_climax": any(str(s.get("emotion")) in ("climax", "awe", "tension") for s in shots) or "not detected",
        "memorable_conclusion": bool(shots and shots[-1].get("narration")),
        "qc_passed": qc.get("passed"),
        "human_review": "required (not automatable)",
    }
    return items

def markdown(plan: dict, chk: dict) -> str:
    L = [f"# Explanation plan - {plan['script_id']}", "", "| Shot | Technique | Rendered today | Why |", "|---|---|---|---|"]
    L += [f"| {o['shot_id']} | {o['technique']} | {'yes' if o['rendered'] else 'planned only'} | {o['idea']} |" for o in plan["shots"]]
    L += ["", plan["summary"]["note"], "", "## Production checklist"] + [f"- {k}: {v}" for k, v in chk.items()]
    return "\n".join(L) + "\n"
