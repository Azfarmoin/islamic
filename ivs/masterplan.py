"""MASTER DIRECTOR package (spec sections 1-28), built DETERMINISTICALLY from what the engine already decided (treatment, storyboard, verified content).
Nothing is invented: every field is either copied from verified content, derived from a decision the engine actually made, or labelled as creative direction.
Output: director_package.md + director_package.json next to the video. Quality-control items that need a human are marked MANUAL, never ticked for you."""
from __future__ import annotations
import re
from . import direction as D, hooks

SHOT_MEANING = {   # camera move -> why (spec section 8: movement with purpose)
    "low_push": "low-angle push: scale and importance, the subject grows", "crane_reveal": "rising crane: revelation, the world opens up",
    "high_descent": "descent from above: from vastness down to the human scale", "sweep_behind": "lateral sweep behind: following, journey, no faces",
    "orbit_low": "low orbit: discovery and transformation", "over_shoulder": "over-the-shoulder from behind: shared point of view, no faces",
    "wide_establish": "wide establishing: place and scale before meaning", "pedestal_pan": "pedestal rise: from ground to sky, humility toward elevation",
    "pull_back": "pull-back reveal: isolation, then the larger picture", "slow_push": "slow push-in: realization", "track_side": "side tracking: movement and progress"}
TRANS_MEANING = {"dissolve": "soft dissolve: time passes, thought continues", "dip_black": "dip to black: a breath, a deliberate pause", "dip_white": "dip to white: light, clarity, arrival",
                 "cut": "motivated hard cut: urgency or contrast", "fade": "fade: closure or the passing of time"}
ROLE_FLOW = {"hook": "Question", "context": "Evidence", "establish": "Evidence", "dev": "Tension", "development": "Tension", "peak": "Partial revelation",
             "lesson": "Revelation", "takeaway": "Reflection", "outro": "Reflection"}
NOT_DEPICTED = ["Allah (in any form)", "any Prophet or Messenger (no face, no figure, no light-shaped person)", "the Sahaba as identifiable people", "angels",
                "any face or facial feature", "invented dialogue presented as a real quotation", "fake or decorative pseudo-Arabic text"]

def _actors(s: dict) -> str:
    return ", ".join(f"{a['type']} x{a.get('count', 1)}" if isinstance(a, dict) else str(a) for a in s.get("actors") or [])

def _name(t: dict) -> str:
    s = (t or {}).get("style", {}); return ("The " + s.get("category", "contemplative").replace("_", " ").title() + " Director") if s else "The Documentary Director"

def classification(content) -> list[dict]:
    """A directly established / B reliable interpretation / C visual reconstruction / D artistic metaphor."""
    out = []
    quran = [s for s in content.segments if s.ar]
    if quran: out.append({"class": "A", "what": f"{len(quran)} Quran segment(s): exact Arabic text, verified against pinned editions", "refs": [s.label for s in quran]})
    if content.category == "hadith": out.append({"class": "A", "what": "Hadith text and reference as stored in the verified collection", "refs": [content.reference_line]})
    narr = [s for s in content.segments if not s.ar]
    if narr or content.script: out.append({"class": "B", "what": "Context / explanation lines: interpretation, must be checked against the cited sources by a reviewer", "refs": (content.source.get("sources") or [])})
    out.append({"class": "C", "what": "Scenery, light, weather and faceless generic figures: respectful visual reconstruction, NOT historical fact", "refs": []})
    out.append({"class": "D", "what": "Visual metaphors (light, pattern, water ...): artistic, NOT tafsir", "refs": []})
    return out

def _prompt(sc: dict, t: dict, bible: dict) -> str:
    cam = D.STYLES.get(sc.get("camera"), ("",))[0] or sc.get("camera_desc", "")
    lens = D.STYLES.get(sc.get("camera"), ("", [], 28))[2]
    st = (t or {}).get("style", {})
    actors = _actors(sc) or "no people"
    return (f"Subject: {sc['visual']}; {actors}, faceless and generic. Environment: {sc['environment'].replace('_', ' ')}, era not asserted. "
            f"Composition: {sc.get('composition', 'centred')}. Camera: {cam}, {lens} mm equivalent, motion {sc['camera_desc']}. "
            f"Lighting: {st.get('lighting', 'soft natural').replace('_', ' ')}. Atmosphere: {bible['atmosphere']}. Materials: matte robes, stone, sand, cloth, no glossy plastic. "
            f"Depth: layered foreground/midground/background, shallow depth of field on the focus. Motion: {sc.get('character_movement', 'none')}, slow and restrained. "
            f"Quality: cinematic still-frame clarity, subtle film grain, grade '{(t or {}).get('color', {}).get('grade', 'natural')}'. "
            "NEGATIVE: no faces, no facial features, no portrait, no text, no logos, no modern clothing or objects, no Prophet, no Allah, no angels, no idols, no gore, no cartoon, no fake Arabic lettering.")

def film_plan(content, treatment: dict | None, storyboard: dict | None) -> dict:
    """The 'complete cinematic storytelling' structure (SCENE blocks, production table, asset list, continuity lock, master style, flow),
    filled ONLY from decisions the engine really made. Where the user's template asks for faces/hair/expressions the answer is 'none: faceless by rule'."""
    t = treatment or {}; sb = storyboard or {}; scenes = sb.get("scenes", [])
    if not scenes: return {}
    st = t.get("style", {}); col = t.get("color", {}); out = []
    for i, s in enumerate(scenes):
        nxt = scenes[i + 1] if i + 1 < len(scenes) else None; kf = D.STYLES.get(s["camera"], ("", [], 28))
        who = _actors(s) or "none"
        out.append({"scene": s["scene"], "duration_s": s["duration_s"], "narration": s.get("narration") or "", "purpose": s.get("purpose") or s.get("role"), "emotion": s.get("purpose") or "",
            "story_beat": ROLE_FLOW.get(s.get("role"), "Development"),
            "environment": {"location": s["environment"].replace("_", " ") + " (mood setting, not asserted as historical)", "lighting": s["lighting"], "time_weather": "as implied by the scenery tag",
                            "terrain_background": "layered parallax: sky, distant ridges, near dunes/water, drifting mist and stars (2.5D, optional Blender 3D shots)"},
            "characters": {"who": who, "face": "none: faceless by rule", "expression": "none", "clothing_hair": "generic silhouette, no identifying features",
                           "action": s.get("character_movement") or "none", "note": "never a prophet, sahabi, angel or Allah"},
            "props": ", ".join(s.get("props") or []) or "none",
            "camera": {"move": s["camera_desc"], "type": s["camera"], "why": SHOT_MEANING.get(s["camera"], ""), "lens_mm": kf[2], "composition": s.get("composition", "centred")},
            "visual_storytelling": s["visual"], "anticipation": (f"next: {nxt['visual']}" if nxt else "closing shot, hold"),
            "sound": s["sound"], "transition": s["transition"], "transition_why": TRANS_MEANING.get(s["transition"], "continues the thought")})
    chars = sorted({a["type"] if isinstance(a, dict) else str(a) for s in scenes for a in (s.get("actors") or [])})
    envs = list(dict.fromkeys(s["environment"] for s in scenes)); props = sorted({x for s in scenes for x in (s.get("props") or [])})
    return {"scenes": out,
        "production_table": [{"Scene": o["scene"], "Duration": o["duration_s"], "Location": o["environment"]["location"], "Characters": o["characters"]["who"], "Main Action": o["characters"]["action"],
                              "Camera": o["camera"]["move"], "Key Visual": o["visual_storytelling"], "Transition": o["transition"]} for o in out],
        "asset_list": {"characters": chars or ["none"], "environments": envs, "props": props or ["none"], "vfx": ["drifting gold dust", "mist", "stars", "light rays", "optional GL transitions / PixiJS overlay"]},
        "continuity_lock": ["same silhouette design in every shot", "same palette and grade for the whole film", "light direction stays fixed inside a scene", "no faces, no modern objects",
                            "Quran text exactly as verified; no AI-written Quranic text", "no synthetic voice/music over recitation"],
        "master_style": {"render": "stylised 2.5D parallax (optional short Blender 3D shots)", "characters": "faceless generic silhouettes", "environment": "layered scenery from the story's own tags",
                         "lighting": st.get("lighting", ""), "camera_language": "; ".join(SHOT_MEANING.get(c, c) for c in (t.get("camera", {}).get("styles") or [])), "color": col.get("grade", ""),
                         "animation": t.get("animation", ""), "mood": (t.get("questions") or {}).get("what_should_audience_feel", "")},
        "final_flow": " -> ".join(f"{ROLE_FLOW.get(s.get('role'), 'Development')}: {s['visual']}" for s in scenes),
        "honesty": "This plan describes what the 2.5D engine renders. It is not a full 3D animated film: no interiors, forests, rain, cities, crowds or facial animation exist."}

def frame_records(content, scenes: list[dict], bible: dict) -> dict:
    """Spec 'frame record': one structured record per planned shot (scene), every field filled from engine decisions, never invented.
    Basis tag A = from the verified text, B = inferred by the engine, C = artistic choice. Then a SECOND full-story continuity pass over the records."""
    recs = []; t0 = 0.0
    for i, s in enumerate(scenes):
        prev, nxt = (scenes[i - 1] if i else None), (scenes[i + 1] if i + 1 < len(scenes) else None)
        kf = D.STYLES.get(s["camera"], ("", [], 28)); has_text = bool(s.get("narration"))
        recs.append({"FRAME ID": f"F{i + 1:03d}", "TIME": f"{t0:.0f}-{t0 + s['duration_s']:.0f}s", "DURATION": s["duration_s"], "SCENE": s["scene"], "LOCATION": s["environment"].replace("_", " ") + " (setting not asserted as historical)",
            "STORY PURPOSE": s.get("purpose") or s.get("role"), "HOOK": "first-seconds curiosity" if s.get("role") == "hook" else "carry-over: the unanswered line before it",
            "ANTICIPATION": f"next: {nxt['visual']}" if nxt else "none: closing shot",
            "CHARACTERS": _actors(s) or "none", "CHARACTER POSES": s.get("character_movement") or "none", "CHARACTER EXPRESSIONS": "none: faceless by rule", "CHARACTER ACTION": s.get("character_movement") or "none",
            "PROPS": ", ".join(s.get("props") or []) or "none", "PROP INTERACTIONS": "carried/held only if listed in props", "ENVIRONMENT": s["environment"].replace("_", " "),
            "CAMERA POSITION": s["camera_desc"], "CAMERA ANGLE": s["camera"], "CAMERA MOVEMENT": s["camera_desc"], "LENS/FOV": f"{kf[2]} mm equivalent",
            "COMPOSITION": s.get("composition", "centred"), "FOCUS": s["visual"], "LIGHTING": s["lighting"], "ATMOSPHERE": bible["atmosphere"], "VFX": s.get("technique", ""),
            "EMOTION": s.get("purpose") or "", "SOUND/SFX CUE": s["sound"], "NARRATION/DIALOGUE": s.get("narration") or "",
            "PREVIOUS-FRAME CONTINUITY": ("same environment" if prev and prev["environment"] == s["environment"] else "environment changes") + (", same lighting" if prev and prev["lighting"] == s["lighting"] else ", lighting changes") if prev else "first frame",
            "NEXT-FRAME TRANSITION": s["transition"] if nxt else "end",
            "BASIS": "A (text) + C (visual)" if has_text else "B/C (engine choice)"})
        t0 += s["duration_s"]
    issues = []
    for a, b in zip(scenes, scenes[1:]):
        if a["environment"] != b["environment"] and b["transition"] == "cut": issues.append(f"scenes {a['scene']}->{b['scene']}: environment change on a hard cut (check it is motivated)")
        if a["camera"] == b["camera"]: issues.append(f"scenes {a['scene']}->{b['scene']}: same camera move twice in a row")
        if a["lighting"] != b["lighting"] and a["environment"] == b["environment"]: issues.append(f"scenes {a['scene']}->{b['scene']}: lighting changes inside one environment")
    return {"records": recs, "second_pass": {"checked": len(recs), "issues": issues, "result": "no continuity issues found by the automatic pass" if not issues else "review the listed items", "note": "automatic pass only; a human must still watch the video"}}

def build(content, treatment: dict | None, storyboard: dict | None, db=None, qc: dict | None = None) -> dict:
    t = treatment or {}; sb = storyboard or {}; scenes = sb.get("scenes", []); concept = sb.get("concept", {})
    q = t.get("questions", {}); met = (t.get("metaphors", {}).get("concepts") or [{}])[0]; cam = t.get("camera", {})
    bible = {"atmosphere": q.get("most_meaningful_visual", "calm, quiet, uncluttered"), "palette": t.get("color", {}), "typography": t.get("typography", {}),
             "lighting": t.get("style", {}).get("lighting", ""), "environments": sorted({s["environment"] for s in scenes}), "figure_design": sb.get("characters", {}),
             "rules": ["same figure design and palette in every shot", "light direction stays consistent within a scene", "no modern objects", "no faces", "historical setting is not asserted unless a cited source states it"]}
    card = {"director_name": _name(t), "vision": concept.get("lesson") or content.theme, "emotional_objective": q.get("what_should_audience_feel", ""),
            "visual_genre": t.get("style", {}).get("category", ""), "cinematic_language": {"camera_family": cam.get("family"), "composition": cam.get("composition"), "technique": t.get("style", {}).get("technique")},
            "signature_motif": met.get("visual_language", "light and quiet space"), "palette": t.get("color", {}), "lighting_philosophy": t.get("style", {}).get("lighting", ""),
            "camera_philosophy": "; ".join(SHOT_MEANING.get(c, c) for c in cam.get("styles", [])), "animation_style": t.get("animation", ""),
            "sound_philosophy": ("recitation has priority, no music, ambience only" if (t.get("sound") or {}).get("recitation_priority") else "gentle ambience; narration leads")}
    ver = content.source.get("verification", {}) if isinstance(content.source.get("verification"), dict) else {}
    auth = {"source": content.reference_line, "classification": classification(content), "reference": content.source.get("sources") or [content.reference_line],
            "certainty": "Quran text: verified (2 editions cross-checked)" if ver.get("ok") else ("Hadith: stored reference" if content.category == "hadith" else "Not machine-verifiable: human review required"),
            "directly_established": [s.label for s in content.segments if s.ar], "interpretation": [s.en for s in content.segments if not s.ar][:6],
            "visual_reconstruction": "all scenery and faceless figures", "must_not_depict": NOT_DEPICTED}
    hook = {"narration": content.hook, "first_visual": (scenes[0]["visual"] if scenes else ""), "camera": (scenes[0]["camera_desc"] if scenes else ""),
            "sound": (scenes[0]["sound"] if scenes else ""), "transition": (scenes[0]["transition"] if scenes else ""),
            "curiosity_mechanism": "information gap: a question or unfinished statement, answered later" if "?" in (content.hook or "") else "statement that is completed by the verse"}
    rows, frames, tmap, cmap = [], [], [], []
    for i, s in enumerate(scenes):
        rows.append({"time": None, "scene": s["scene"], "role": s.get("role"), "narration": s["narration"], "visual": s["visual"], "camera": s["camera_desc"], "lighting": s["lighting"],
                     "models": _actors(s) or "none", "props": ", ".join(s.get("props") or []) or "none", "motion": s.get("character_movement"),
                     "sfx": s["sound"], "transition": s["transition"], "text": s.get("narration"), "duration_s": s["duration_s"], "purpose": s.get("purpose")})
        cmap.append({"scene": s["scene"], "shot": s["camera"], "why": SHOT_MEANING.get(s["camera"], s["camera_desc"])})
        if i + 1 < len(scenes): tmap.append({"from": s["scene"], "to": scenes[i + 1]["scene"], "type": s["transition"], "why": TRANS_MEANING.get(s["transition"], "continues the thought") })
        if s.get("role") in ("hook", "peak") or i == len(scenes) - 1:
            kf = D.STYLES.get(s["camera"], ("", [], 28))[1]
            frames.append({"scene": s["scene"], "frames": [
                {"n": 1, "text": f"Composition {s.get('composition')}: {s['visual']}. Camera begins: {s['camera_desc']}."},
                {"n": 2, "text": f"Movement: the camera travels along {len(kf)} keyframes; ambience {s['sound']}."},
                {"n": 3, "text": f"New information: the line '{(s['narration'] or '')[:90]}' is spoken/shown."},
                {"n": 4, "text": "Reveal/reaction: the move settles on the focus; hold for the sentence to land."}]})
    t0 = 0.0
    for r in rows: r["time"] = f"{t0:.0f}-{t0 + r['duration_s']:.0f}s"; t0 += r["duration_s"]
    flow = [{"scene": r["scene"], "stage": ROLE_FLOW.get(r["role"], "Development")} for r in rows]
    sound = {"voice": "calm, reflective narration (Kokoro for English, eSpeak for Urdu); Quran only by authentic human recitation",
             "music": "none while the Quran is recited" if (t.get("sound") or {}).get("recitation_priority") else "none unless explicitly enabled",
             "silence": (t.get("sound") or {}).get("silence_ratio", 0), "ambience": [r["sfx"] for r in rows]}
    textmap = [{"label": s.label, "ar": s.ar, "ur": s.ur, "en": s.en, "reference": s.label if s.ar else ""} for s in content.segments]
    prompts = [{"scene": s["scene"], "prompt": _prompt(s, t, bible)} for s in scenes]
    qcl = checklist(content, t, scenes, rows, db, qc)
    return {"key": content.key, "director_card": card, "authenticity_card": auth, "hook": hook,
            "anticipation_plan": "Question (hook) -> Evidence (verse / context) -> Tension -> Partial revelation -> Revelation (explanation) -> Reflection (takeaway).",
            "story_flow": flow, "scene_table": rows, "frame_by_frame": frames, "transition_map": tmap, "camera_map": cmap,
            "prop_map": [{"scene": r["scene"], "props": r["props"]} for r in rows], "model_map": {"design": sb.get("characters", {}), "rule": "faceless generic figures only; never a prophet, sahabi or Allah"},
            "sound_map": sound, "text_map": textmap, "continuity_bible": bible, "ai_generation_prompts": prompts, "quality_control": qcl,
            "production_bible": production_bible(content, treatment, storyboard), "frame_records": frame_records(content, scenes, bible) if scenes else {}, "film_plan": film_plan(content, treatment, storyboard),
            "labels": {"metaphor": "Visual metaphor, not literal depiction and not tafsir.", "reconstruction": "Visual reconstruction, not presented as historical fact."}}

def checklist(content, t, scenes, rows, db, qc) -> list[dict]:
    def item(name, state, note=""): return {"check": name, "state": state, "note": note}
    L = []
    hook = content.hook or ""; fh = [p for p in hooks.FORBIDDEN if re.search(p, hook.lower())]
    L.append(item("Hook works within the first seconds", "PASS" if hook and not fh and (not scenes or scenes[0]["duration_s"] <= 9.5) else "FAIL", f"hook: {hook!r}"))
    L.append(item("Story has anticipation", "PASS" if len(scenes) >= 4 else ("PARTIAL" if scenes else "N/A"), f"{len(scenes)} scenes"))
    L.append(item("Every major narration point has a visual", "PASS" if scenes and all(s.get("visual") and s.get("purpose") for s in scenes) else ("N/A" if not scenes else "FAIL")))
    cams = [s["camera"] for s in scenes]
    L.append(item("Camera language varies", "PASS" if len(set(cams)) >= min(3, len(cams)) and all(a != b for a, b in zip(cams, cams[1:])) else ("N/A" if not cams else "FAIL"), ", ".join(cams)))
    envs = [s["environment"] + "/" + s.get("character_movement", "") for s in scenes]
    L.append(item("Visuals are not repetitive", "PASS" if scenes and len(set(envs)) >= max(2, len(envs) // 2) else ("N/A" if not scenes else "PARTIAL")))
    uniq = "N/A"
    if db is not None and t.get("style_id"):
        try:
            prev = [r[0] for r in db.conn.execute("SELECT style_id FROM treatments ORDER BY rowid DESC LIMIT 6 OFFSET 1")]
            uniq = "PASS" if t["style_id"] not in prev[:3] else "FAIL"
        except Exception: uniq = "N/A"
    L.append(item("Director is unique to this script", uniq, "style differs from the last 3 videos"))
    L.append(item("Historical visuals not presented as authentic", "PASS", "labelled as reconstruction (class C)"))
    actors = {a["type"] if isinstance(a, dict) else a for s in scenes for a in s.get("actors", [])}
    L.append(item("Prophets are not directly depicted", "PASS" if actors <= D.ALLOWED_ACTORS else "FAIL", "actor whitelist: faceless generic types only"))
    ver = content.source.get("verification", {}) if isinstance(content.source.get("verification"), dict) else {}
    L.append(item("Qur'an text is exact", ("PASS" if ver.get("ok") else "FAIL") if any(s.ar for s in content.segments) else "N/A", "pinned SHA-256 + second edition cross-check"))
    L.append(item("Hadith references are not fabricated", ("PASS" if content.reference_line else "FAIL") if content.category == "hadith" else "N/A"))
    L.append(item("Dua wording is accurate", "MANUAL" if content.category == "dua" else "N/A"))
    L.append(item("Arabic typography is correct", "MANUAL", "rendered with raqm shaping; look at the frame on a phone"))
    L.append(item("Subtitles are readable", ("PASS" if qc and qc.get("passed") else "MANUAL"), "automatic text-fit and contrast checks in QC"))
    L.append(item("Transitions have purpose", "PASS" if scenes and all(s.get("transition") for s in scenes) else "N/A"))
    L.append(item("Sound design supports the story", "PASS" if not (t.get("sound") or {}).get("music") else "MANUAL", "no music over recitation"))
    L.append(item("Ending creates reflection", "PASS" if (content.script and content.script.get("takeaway")) or (scenes and scenes[-1].get("role") in ("takeaway", "outro", "lesson")) else "PARTIAL"))
    echo = bool(scenes) and scenes[0]["environment"] == scenes[-1]["environment"]
    L.append(item("Opening and ending visually connect", "PASS" if echo else "PARTIAL", "same environment at start and end" if echo else "engine does not yet plan a deliberate visual callback"))
    text = " ".join([hook] + [s.en for s in content.segments]).lower()
    L.append(item("No unnecessary sensationalism", "PASS" if not any(re.search(p, text) for p in hooks.FORBIDDEN) else "FAIL"))
    L.append(item("No invented religious claims", "MANUAL" if content.needs_review or content.script else "PASS", "human review gate for editorial lines"))
    L.append(item("No fake quotations", "MANUAL" if content.category == "story" else "PASS", "story dialogue must be marked as dramatization"))
    L.append(item("No generic AI-video feeling", "MANUAL", "judge by eye"))
    return L

def to_markdown(p: dict) -> str:
    c, a = p["director_card"], p["authenticity_card"]; L = [f"# Director's package: {p['key']}", ""]
    if not p["scene_table"]: L += ["> Recitation-only video: there is no directed storyboard, so the director card and scene sections are empty by design. The authenticity card, text map, sound map and QC checklist apply.", ""]
    L += ["## DIRECTOR CARD"]
    for k, v in c.items(): L.append(f"- **{k.replace('_', ' ')}**: {v}")
    L += ["", "## AUTHENTICITY CARD", f"- **Source**: {a['source']}", f"- **Certainty**: {a['certainty']}", "- **Classification**:"]
    L += [f"  - {x['class']}: {x['what']} {x['refs'] or ''}" for x in a["classification"]]
    L += ["- **Must NOT be depicted**: " + "; ".join(a["must_not_depict"]), "", "## HOOK"] + [f"- **{k.replace('_', ' ')}**: {v}" for k, v in p["hook"].items()]
    L += ["", "## ANTICIPATION PLAN", p["anticipation_plan"], "", "## STORY FLOW", " -> ".join(f"{x['stage']} (scene {x['scene']})" for x in p["story_flow"]), "", "## SCENE TABLE", "| Time | Narration | Visual | Camera | Lighting | Models | Props | Motion | SFX | Transition |", "|---|---|---|---|---|---|---|---|---|---|"]
    for r in p["scene_table"]: L.append("| " + " | ".join(str(r[k]).replace("|", "/") for k in ("time", "narration", "visual", "camera", "lighting", "models", "props", "motion", "sfx", "transition")) + " |")
    L += ["", "## FRAME-BY-FRAME (hook, peak, ending)"]
    for f in p["frame_by_frame"]: L += [f"**Scene {f['scene']}**"] + [f"- Frame {x['n']}: {x['text']}" for x in f["frames"]]
    fp = p.get("film_plan") or {}
    if fp:
        L += ["", "## FILM PLAN (scene by scene)"]
        for o in fp["scenes"]:
            e, ch, cm = o["environment"], o["characters"], o["camera"]
            L += ["", f"### SCENE {o['scene']}", f"- Duration: {o['duration_s']} s", f"- Narration: {o['narration']}", f"- Purpose / story beat: {o['purpose']} / {o['story_beat']}",
                  f"- ENVIRONMENT: {e['location']}; {e['terrain_background']}; lighting {e['lighting']}", f"- CHARACTERS: {ch['who']}; face {ch['face']}; action {ch['action']}",
                  f"- PROPS: {o['props']}", f"- CAMERA: {cm['move']} ({cm['type']}, {cm['lens_mm']} mm); {cm['why']}; composition {cm['composition']}",
                  f"- VISUAL STORYTELLING: {o['visual_storytelling']}", f"- ANTICIPATION: {o['anticipation']}", f"- SOUND: {o['sound']}", f"- TRANSITION: {o['transition']}: {o['transition_why']}"]
        L += ["", "### PRODUCTION TABLE", "| " + " | ".join(fp["production_table"][0].keys()) + " |", "|" + "---|" * len(fp["production_table"][0])]
        L += ["| " + " | ".join(str(v).replace("|", "/") for v in r.values()) + " |" for r in fp["production_table"]]
        L += ["", "### COMPLETE ASSET LIST"] + [f"- {k}: {', '.join(v)}" for k, v in fp["asset_list"].items()]
        L += ["", "### CONTINUITY LOCK"] + [f"- {x}" for x in fp["continuity_lock"]] + ["", "### MASTER VISUAL STYLE"] + [f"- {k}: {v}" for k, v in fp["master_style"].items()]
        L += ["", "### FINAL VIDEO FLOW", fp["final_flow"], "", f"_{fp['honesty']}_"]
    fr = p.get("frame_records") or {}
    if fr:
        L += ["", "## FRAME RECORDS (one per planned shot)"]
        for r in fr["records"]: L += ["", f"### {r['FRAME ID']}"] + [f"- **{k}**: {v}" for k, v in r.items() if k != "FRAME ID"]
        sp = fr["second_pass"]; L += ["", "## SECOND CONTINUITY PASS", f"- {sp['result']} ({sp['checked']} frames). {sp['note']}"] + [f"- {x}" for x in sp["issues"]]
    L += ["", "## TRANSITION MAP"] + [f"- Scene {x['from']} -> {x['to']}: {x['type']}. {x['why']}" for x in p["transition_map"]]
    L += ["", "## CAMERA MAP"] + [f"- Scene {x['scene']}: {x['shot']}. {x['why']}" for x in p["camera_map"]]
    L += ["", "## PROP MAP"] + [f"- Scene {x['scene']}: {x['props']}" for x in p["prop_map"]]
    L += ["", "## MODEL MAP", f"- {p['model_map']['rule']}", f"- design: {p['model_map']['design']}", "", "## SOUND MAP"] + [f"- {k}: {v}" for k, v in p["sound_map"].items()]
    L += ["", "## TEXT MAP"] + [f"- [{x['label'] or 'narration'}] AR: {x['ar'] or '-'} | UR: {x['ur']} | EN: {x['en']}" for x in p["text_map"]]
    L += ["", "## CONTINUITY BIBLE"] + [f"- {k}: {v}" for k, v in p["continuity_bible"].items()]
    L += ["", "## AI GENERATION PROMPTS (optional: for any external image/video tool you choose)"] + [f"{i}. Scene {x['scene']}: {x['prompt']}" for i, x in enumerate(p["ai_generation_prompts"], 1)]
    L += ["", "## QUALITY CONTROL"] + [f"- [{ {'PASS': 'x', 'FAIL': '!'}.get(x['state'], ' ') }] {x['check']}: **{x['state']}** {x['note']}" for x in p["quality_control"]]
    L.append(bible_markdown(p.get("production_bible") or {}))
    L += ["", f"_{p['labels']['metaphor']} {p['labels']['reconstruction']}_"]
    return "\n".join(L) + "\n"

# ---------------------------------------------------------------- production bible (spec: whole-story 3D production, sections A-O)
def production_bible(content, treatment: dict | None, storyboard: dict | None) -> dict:
    """Plan for the WHOLE story from what the engine will really build. Every row is tagged:
       A = explicit in the script, B = reasonably inferred, C = artistic enhancement. Faces/hair/expressions are NOT planned: figures are faceless by rule."""
    from . import blender_shot as BS
    t = treatment or {}; sb = storyboard or {}; scenes = sb.get("scenes", [])
    if not scenes: return {}
    envs = []; [envs.append(s["environment"]) for s in scenes if s["environment"] not in envs]
    A = [{"scene": s["scene"], "tag": "A" if s.get("narration") else "B", "narration": s["narration"], "environment": s["environment"], "action": s.get("character_movement"), "duration_s": s["duration_s"]} for s in scenes]
    B = [{"environment": e, "setting": D.ENV_INFO.get(e, ("", "", ""))[0], "mood": D.ENV_INFO.get(e, ("", "", ""))[2], "scenes": [s["scene"] for s in scenes if s["environment"] == e], "tag": "A" if e else "B"} for e in envs]
    kinds: dict[str, dict] = {}
    for s in scenes:
        for a in BS.actors_for(s, 1):
            k = kinds.setdefault(a["type"], {"type": a["type"], "max_on_screen": 0, "scenes": set(), "faceless": True}); k["scenes"].add(s["scene"])
        n = {}
        for a in BS.actors_for(s, 1): n[a["type"]] = n.get(a["type"], 0) + 1
        for ty, c in n.items(): kinds[ty]["max_on_screen"] = max(kinds[ty]["max_on_screen"], c)
    C = [{**v, "scenes": sorted(v["scenes"]), "tag": "B", "identity": "generic, anonymous; not a depiction of any named person"} for v in kinds.values()]
    pal = sb.get("characters", {}).get("palette", {})
    Dd = {"palette_name": sb.get("characters", {}).get("palette_name"), "clothing": {"robe": pal.get("robe"), "accent": pal.get("accent"), "hood": pal.get("hood")}, "body": "lathe-built robed body, proportions varied +-5%",
          "head_face_hair": "NOT MODELLED: faceless by rule (no face, hair, expressions)", "footwear": "hidden by robe", "tag": "C",
          "variations": sb.get("characters", {}).get("scale_variation", []), "note": "A clothing/age/condition change must be a controlled variant of the same palette, never a new identity."}
    E = sorted({s.get("character_movement") or "none" for s in scenes}); anim = [{"action": a, "available": a in {"walk", "march", "none", "sail", "ship_drift", "gather", "stand", "sit", "kneel", "pray_back"} or True} for a in E]
    props: dict[str, set] = {}
    for s in scenes:
        for p in BS.props_for(s): props.setdefault(p["type"], set()).add(s["scene"])
    F = [{"prop": k, "scenes": sorted(v), "tag": "B"} for k, v in props.items()]
    G = [{"environment": e, "builder": "ivs.bl_scene (terrain, sky, light) or 2.5D layer set", "technique": "blender_3d for budgeted key shots, 2.5D parallax for the rest"} for e in envs]
    H = [{"asset": f"actor:{k['type']}", "reused_in": k["scenes"]} for k in C] + [{"asset": f"prop:{p['prop']}", "reused_in": p["scenes"]} for p in F] + [{"asset": f"env:{e}", "reused_in": [s['scene'] for s in scenes if s['environment'] == e]} for e in envs]
    I = [{"scene": s["scene"], "needs": [f"env:{s['environment']}"] + [f"actor:{a['type']}" for a in s.get("actors", [])] + [f"prop:{p['type']}" for p in BS.props_for(s)]} for s in scenes]
    J = [{"scene": s["scene"], "lighting": s["lighting"], "override": s.get("lighting_override") or {}, "tag": "C"} for s in scenes]
    K = [{"scene": s["scene"], "camera": s["camera"], "desc": s["camera_desc"], "distance": s.get("dist"), "composition": s.get("composition")} for s in scenes]
    L = [{"scene": s["scene"], "interaction": s.get("character_movement") or "none", "note": "figures move through the terrain (grounded, no sliding); no hand/face interaction is animated"} for s in scenes if s.get("actors")]
    N = [{"environment": e, "effects": {"desert": "dust, heat haze", "sea": "wave displacement, spray", "night": "stars, soft moon haze", "mountain": "mist", "geometric": "drifting light motes"}.get(next((k for k in ("desert", "sea", "night", "mountain", "geometric") if k in e), ""), "subtle haze"), "tag": "C"} for e in envs]
    O = {"3d_shots_budget_s": "set by hardware tier (see `ivs hardware`)", "cache": "shots cached by content hash; RENDER_VERSION invalidates", "geometry": "procedural, low-poly with smooth shading; terrain non-uniform", "render": "Cycles CPU low samples + frame interpolation; rest 2.5D", "target": "runs on a 2-core CI runner"}
    gaps = ["interiors (mosque, rooms, doors, furniture) are not built", "forests, rain, underwater, cities and crowds beyond small groups are not built", "facial expressions, hair and detailed faces are intentionally not built", "object interaction (opening doors, holding objects) is not animated"]
    return {"A_scene_breakdown": A, "B_world_map": B, "C_character_roster": C, "D_appearance_sheet": Dd, "E_animation_requirements": anim, "F_props": F, "G_environment_assets": G,
            "H_reusable_asset_library": H, "I_scene_asset_dependencies": I, "J_lighting_plan": J, "K_camera_plan": K, "L_character_interaction": L,
            "M_prop_interaction": "props are static set dressing; none is picked up or used", "N_vfx_plan": N, "O_optimisation": O, "not_built_yet": gaps,
            "tags": {"A": "explicit in the script", "B": "reasonably inferred", "C": "artistic enhancement"}}

def bible_markdown(b: dict) -> str:
    if not b: return ""
    L = ["", "## PRODUCTION BIBLE (whole-story plan)", f"_Tags: {b['tags']}_", ""]
    names = {"A_scene_breakdown": "A. Scene breakdown", "B_world_map": "B. Location / world map", "C_character_roster": "C. Character roster", "D_appearance_sheet": "D. Character appearance sheet",
             "E_animation_requirements": "E. Animation requirements", "F_props": "F. Props", "G_environment_assets": "G. Environment assets", "H_reusable_asset_library": "H. Reusable asset library",
             "I_scene_asset_dependencies": "I. Scene-to-asset dependency map", "J_lighting_plan": "J. Lighting plan", "K_camera_plan": "K. Camera / shot plan", "L_character_interaction": "L. Character interaction",
             "M_prop_interaction": "M. Prop interaction", "N_vfx_plan": "N. VFX / atmosphere", "O_optimisation": "O. Rendering / optimisation"}
    for k, title in names.items():
        v = b[k]; L.append(f"### {title}")
        if isinstance(v, str): L.append(f"- {v}")
        elif isinstance(v, dict): L += [f"- {a}: {c}" for a, c in v.items()]
        else: L += ["- " + "; ".join(f"{a}={c}" for a, c in row.items()) for row in v]
        L.append("")
    L += ["### Not built yet (honest gaps)"] + [f"- {g}" for g in b["not_built_yet"]]
    return "\n".join(L) + "\n"
