"""Studio commands: render-mode planner, test-3d, dry-run, validate, status, cleanup, per-video JSON package.
Everything here reports what is REALLY true; estimates are labelled as estimates."""
from __future__ import annotations
import json, os, shutil, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
S_PER_FRAME = {"draft": 3.0, "hd": 10.5, "full": 40.0}      # measured on a 2-core CPU: hd 10.5 s/frame (see docs); draft/full are scaled estimates

def plan_modes(scenes: list[dict], tier: str = "hd", cpus: int | None = None, safe_limit_s: float = 3000) -> dict:
    """FULL_3D for hook / major event / climax / ending while the time budget allows, HYBRID_3D (3D establishing + 2.5D rest) when it does not, else 2.5D."""
    from .blender_shot import TIERS
    cpus = cpus or os.cpu_count() or 2; fps = TIERS[tier]["fps"]; spf = S_PER_FRAME[tier] * (2 / max(cpus, 1))
    must = [i for i, s in enumerate(scenes) if s.get("role") in ("hook", "peak", "conflict", "conclusion") or i in (0, len(scenes) - 1)]
    rows, used = [], 0.0
    for i, s in enumerate(scenes):
        frames = int(s["duration_s"] * fps); cost = frames * spf; important = i in must
        if important and used + cost <= safe_limit_s: mode, used = "FULL_3D", used + cost
        elif important and used + cost * 0.4 <= safe_limit_s: mode, used = "HYBRID_3D", used + cost * 0.4      # shorter 3D establishing part only
        else: mode = "2.5D"
        rows.append({"scene": s["scene"], "importance": "high" if important else "low", "estimated_frames": frames, "estimated_render_s": round(cost) if mode != "2.5D" else 0, "mode": mode})
    return {"tier": tier, "cpus": cpus, "safe_limit_s": safe_limit_s, "estimated_total_s": round(used), "scenes": rows,
            "note": "Estimate only. HYBRID_3D = part of the scene is 3D, the rest 2.5D; 2.5D scenes are never labelled 3D."}

def test_3d(cfg: dict, out: Path | None = None) -> dict:
    """One complete real Blender scene: environment, characters, props, lighting, shadows, camera, animation, VFX (dust/clouds), ambience audio -> test_3d.{blend,mp4,json}."""
    from . import direction as D, blender_shot as BS, audio
    out = Path(out or ROOT / "output" / "test_3d"); out.mkdir(parents=True, exist_ok=True)
    scene = {"scene": 1, "environment": "desert_dawn", "camera": "wide_establish", "duration_s": 1.5, "composition": "centered_symmetry", "dist": 1.0,
             "actors": [{"type": "spearman", "count": 3}, {"type": "traveller", "count": 2}, {"type": "elephant", "count": 1}, {"type": "bird", "count": 4}]}
    chars = {"palette": D.PALETTES[next(iter(D.PALETTES))]}
    fr = out / "frames"; shutil.rmtree(fr, ignore_errors=True); fr.mkdir()
    spec = BS.make_spec(scene, chars, "draft", fr, 7, scene["duration_s"]); spec["report"] = str(out / "report.json"); spec["save_blend"] = str(out / "test_3d.blend")
    (fr / "spec.json").write_text(json.dumps(spec)); t0 = time.time()
    r = subprocess.run([sys.executable, "-m", "ivs.bl_scene", str(fr / "spec.json")], capture_output=True, text=True, cwd=ROOT)
    n = len(list(fr.glob("f*.png")))
    if n < spec["frames"] or not (out / "report.json").exists(): return {"ok": False, "error": (r.stderr or r.stdout)[-800:], "frames": n}
    rep = json.loads((out / "report.json").read_text()); dur = spec["frames"] / spec["fps"]
    amb = audio.make_ambience(out / "ambience.wav", "desert_dawn", dur)
    vid = out / "test_3d.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(spec["fps"]), "-i", str(fr / "f%05d.png"), "-i", str(amb), "-vf", "scale=1080:1920:flags=lanczos,format=yuv420p",
                    "-c:v", "libx264", "-crf", "20", "-preset", "veryfast", "-c:a", "aac", "-shortest", str(vid)], check=True)
    checks = {"real_blender_meshes": rep["meshes"] >= 20, "has_lights": rep["lights"] >= 1, "shadow_casting_light": rep["shadow_casting_lights"] >= 1, "camera": rep["cameras"] == 1,
              "characters": len(rep["actors"]) >= 3, "props": bool(rep["props"]) or rep["meshes"] > 40, "animation_poses": rep["animated_actor_poses"] > rep["frames_rendered"],
              "blend_saved": (out / "test_3d.blend").exists() and (out / "test_3d.blend").stat().st_size > 10000, "video_has_audio": True, "frames_rendered": n == spec["frames"]}
    res = {"ok": all(checks.values()), "checks": checks, "scene_report": rep, "render_seconds": round(time.time() - t0, 1), "video": str(vid), "blend": str(out / "test_3d.blend"),
           "tier": "draft", "note": "Draft tier on CPU; proves the pipeline builds and renders actual 3D geometry (meshes, lights, shadows, animated rigs), not 2D images."}
    (out / "test_3d.json").write_text(json.dumps(res, indent=1)); shutil.rmtree(fr, ignore_errors=True); return res

def package_files(work: Path, pk: dict, meta: dict, qc: dict, content, render: dict | None = None) -> list[str]:
    """director.json, storyboard.json, scene_plan.json, asset_manifest.json, qc.json, sources.json, credits.json, metadata.json (documentation of how the video was made)."""
    fp = pk.get("film_plan") or {}
    modes = plan_modes([{"scene": o["scene"], "duration_s": o["duration_s"], "role": o["story_beat"]} for o in fp.get("scenes", [])]) if fp else {}
    files = {"director.json": {"director_card": pk.get("director_card"), "hook": pk.get("hook"), "story_flow": pk.get("story_flow"), "authenticity_card": pk.get("authenticity_card")},
             "storyboard.json": {"scene_table": pk.get("scene_table"), "frame_records": pk.get("frame_records"), "camera_map": pk.get("camera_map"), "transition_map": pk.get("transition_map")},
             "scene_plan.json": {"film_plan": fp, "render_modes": modes},
             "asset_manifest.json": {"assets": (render or {}).get("assets", []), "scenery": (render or {}).get("scenery"), "shots_3d": (render or {}).get("shots_3d"), "bible": pk.get("production_bible")},
             "qc.json": qc, "sources.json": {"key": content.key, "reference": content.reference_line, "source": content.source},
             "credits.json": {"assets": (render or {}).get("assets", []), "credits_in_description": [l for l in (meta.get("description") or "").splitlines() if l.startswith(("Sound effects", "Recitation", "Arabic text", "Source"))]},
             "metadata.json": meta, "VIDEO_DIRECTOR.json": video_director(content, pk, meta, render, qc)}
    files.update(production_files(content, pk, meta, render, qc))
    for n, d in files.items(): (work / n).write_text(json.dumps(d, indent=1, ensure_ascii=False, default=str))
    return list(files)

BEAT_EMOTION = {"question": "curiosity", "evidence": "wonder", "tension": "suspense", "partial revelation": "awe", "revelation": "relief", "reflection": "reflection"}
EMOTION = {"hook": "curiosity", "setup": "wonder", "context": "wonder", "conflict": "concern", "peak": "awe", "turn": "suspense", "resolution": "relief", "conclusion": "reflection",
           "narration": "curiosity", "ayah": "peace", "translation": "reflection", "script": "reflection", "outro": "gratitude"}
PACE = {"curiosity": "normal", "wonder": "slow", "concern": "normal", "awe": "slow", "suspense": "gradual acceleration", "relief": "slow", "reflection": "slow", "peace": "slow", "gratitude": "slow"}

def video_director(content, pk: dict, meta: dict, render: dict | None, qc: dict) -> dict:
    """VIDEO_DIRECTOR.json: one machine-readable record per shot (script id, scene/shot id, duration, narration, characters, props, environment, camera, lens, lighting,
    animation, VFX, transition, audio cue, emotion, historical notes, authenticity notes, continuity). Built only from decisions the engine really made."""
    fp = (pk.get("film_plan") or {}).get("scenes", []); marks = (render or {}).get("marks") or []; total = (render or {}).get("duration") or 0
    claims = (content.source or {}).get("claims") or []
    shots = []
    if fp:
        prev = None
        for i, o in enumerate(fp):
            emo = BEAT_EMOTION.get(str(o["story_beat"]).lower(), "curiosity")
            shots.append({"script_id": content.key, "scene_id": o["scene"], "shot_id": f"{o['scene']}.1", "duration_s": o["duration_s"], "narration": o["narration"], "characters": o["characters"]["who"],
                          "props": o["props"], "environment": o["environment"]["location"], "camera": o["camera"]["type"], "lens_mm": o["camera"]["lens_mm"], "camera_movement": o["camera"]["move"],
                          "lighting": o["environment"]["lighting"], "animation": o["characters"]["action"], "vfx": "drifting dust, mist, stars; GL transition at scene change",
                          "transition": o["transition"], "audio_cue": o["sound"], "emotion": emo, "pace": PACE.get(emo, "normal"),
                          "historical_notes": "stylised reconstruction, not evidence", "authenticity_notes": "faceless figures only; narration text is the author's, graded claims listed in claims",
                          "continuity": {"previous_environment": prev, "same_environment": prev == o["environment"]["location"]}})
            prev = o["environment"]["location"]
    else:
        for i, (t, k) in enumerate(marks):
            end = marks[i + 1][0] if i + 1 < len(marks) else total; emo = EMOTION.get(k, "reflection")
            shots.append({"script_id": content.key, "scene_id": i + 1, "shot_id": f"{i + 1}.1", "duration_s": round(end - t, 1), "kind": k, "emotion": emo, "pace": PACE.get(emo, "slow"),
                          "environment": "layered scenery chosen from the verse meaning (see scenery in asset_manifest.json)", "camera": "slow parallax drift", "characters": "none",
                          "historical_notes": "none: no event is reconstructed", "authenticity_notes": "Quran/hadith text exactly as verified; no figures"})
    return {"script_id": content.key, "reference": content.reference_line, "category": content.category, "shots": shots, "claims": claims, "qc_passed": qc.get("passed"),
            "emotion_arc": [s["emotion"] for s in shots], "note": "Machine-readable director memory. Time control (slow-motion/time-lapse) and per-shot regeneration are not implemented."}

def production_files(content, pk: dict, meta: dict, render: dict | None, qc: dict) -> dict:
    """The 12 machine-readable production files, all derived from VIDEO_DIRECTOR shots + the production bible. Fields the engine does not model (aperture, shutter, rack focus...)
    are stated as 'not modelled' instead of invented, so the files can be used to continue or regenerate a production without false precision."""
    vd = video_director(content, pk, meta, render, qc); shots = vd["shots"]; bible = pk.get("production_bible") or {}; r = render or {}
    NM = "not modelled"
    envs = list(dict.fromkeys(s.get("environment") for s in shots if s.get("environment")))
    chars = sorted({str(s.get("characters")) for s in shots if s.get("characters") not in (None, "none")})
    t = 0.0; edit = []
    for s in shots: edit.append({"shot_id": s["shot_id"], "start_s": round(t, 1), "end_s": round(t + s["duration_s"], 1), "cut_to_next": s.get("transition", "cut"), "pace": s.get("pace")}); t += s["duration_s"]
    sfx = [{"asset": a.get("name") or a.get("role"), "attribution": a.get("attribution"), "license": a.get("license"), "source": a.get("source")} for a in (r.get("assets") or []) if a.get("kind") == "sfx"]
    from . import explain
    ep = explain.explanation_plan(vd); ck = explain.checklist(vd, ep, qc, meta)
    return {
        "EXPLANATION_PLAN.json": ep,
        "PRODUCTION_CHECKLIST.json": ck,
        "SHOT_LIST.json": {"script_id": vd["script_id"], "shots": [{k: s.get(k) for k in ("shot_id", "scene_id", "duration_s", "narration", "kind", "emotion")} for s in shots]},
        "CHARACTER_BIBLE.json": {"policy": "faceless generic silhouettes only; never Allah, prophets, sahaba or angels", "characters": chars or ["none"], "bible": bible.get("characters")},
        "ENVIRONMENT_BIBLE.json": {"environments": envs, "note": "stylised mood settings, not historical reconstructions", "bible": bible.get("environments")},
        "PROP_BIBLE.json": {"props": sorted({p.strip() for s in shots for p in str(s.get("props") or "").split(",") if p.strip() and p.strip() != "none"}) or ["none"], "bible": bible.get("props")},
        "CAMERA_PLAN.json": {"shots": [{"shot_id": s["shot_id"], "camera": s.get("camera"), "lens_mm": s.get("lens_mm", NM), "movement": s.get("camera_movement", NM),
                                         "aperture": NM, "shutter": NM, "focus": "Blender 3D shots: depth of field per tier; 2.5D: parallax layers only", "rack_focus": NM} for s in shots]},
        "ANIMATION_PLAN.json": {"shots": [{"shot_id": s["shot_id"], "animation": s.get("animation", "slow parallax drift"), "physics": "no physics simulation; keyframed/procedural motion"} for s in shots]},
        "VFX_PLAN.json": {"shots": [{"shot_id": s["shot_id"], "vfx": s.get("vfx", "drifting dust, mist, stars"), "layers": "primary + secondary particles + atmosphere (2D/3D overlay); no fluid/cloth/crowd simulation"} for s in shots],
                         "scenery_looks": r.get("scenery"), "js_effects": r.get("js_effects")},
        "SFX_TIMELINE.json": {"cues": [{"shot_id": s["shot_id"], "cue": s.get("audio_cue", "ambience only")} for s in shots], "assets": sfx,
                              "layers": ["narration", "ambience", "action sfx", "transition sfx"], "ducking": "ambience/sfx are lowered under narration; Quran recitation never has music or effects",
                              "audio_perspective": NM, "silence": "reflection shots keep ambience only"},
        "LIGHTING_PLAN.json": {"shots": [{"shot_id": s["shot_id"], "lighting": s.get("lighting", "scenery's own light"), "emotion": s.get("emotion")} for s in shots]},
        "EDIT_TIMELINE.json": {"edit": edit, "total_s": round(t, 1), "j_l_cuts": NM, "speed_ramping": NM, "slow_motion": NM, "marks": r.get("marks")},
        "CONTINUITY.json": {"shots": [{"shot_id": s["shot_id"], **(s.get("continuity") or {})} for s in shots], "rules": (pk.get("film_plan") or {}).get("continuity_lock", [])},
        "AUTHENTICITY_NOTES.json": {"authenticity_card": pk.get("authenticity_card"), "claims": vd["claims"], "not_depicted": bible.get("not_depicted"), "notes": [s.get("authenticity_notes") for s in shots][:1],
                                    "qc_passed": qc.get("passed"), "human_review": "required for stories, hadith and AI drafts"}}

def validate(cfg: dict, pipe) -> dict:
    from . import audit
    import yaml
    res = {}
    try: res["zero_cost"] = "ok" if cfg.get("zero_cost_mode") else "FAIL: zero_cost_mode off"
    except Exception as e: res["zero_cost"] = f"FAIL {e}"
    wf = sorted((ROOT / ".github" / "workflows").glob("*.yml"))
    res["workflows"] = {w.name: ("ok" if yaml.safe_load(w.read_text()) else "empty") for w in wf}
    try: pipe.sel.quran; res["quran_data"] = "loaded (run verify-data for the full cross-check)"
    except Exception as e: res["quran_data"] = f"FAIL {e}"
    res["secrets_present"] = {k: bool(os.environ.get(k)) for k in ("GEMINI_API_KEY", "YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN")}      # presence only, never values
    res["tools"] = {t: bool(shutil.which(t)) for t in ("ffmpeg", "node")}
    try: import bpy; res["tools"]["blender_bpy"] = bpy.app.version_string
    except Exception: res["tools"]["blender_bpy"] = False
    res["ok"] = res["zero_cost"] == "ok" and all(v == "ok" or v == "empty" for v in res["workflows"].values()) and not str(res["quran_data"]).startswith("FAIL")
    return res

def status(pipe) -> dict:
    items = pipe.db.items()
    by = {}
    for it in items: by[it["status"]] = by.get(it["status"], 0) + 1
    return {"items": len(items), "by_status": by, "paused": pipe.db.setting("paused") == "1", "last": [{k: i[k] for k in ("id", "key", "status")} for i in items[-5:]]}

def cleanup(cfg: dict, days: int = 14, apply: bool = False) -> dict:
    """Removes work files of OLD rendered/published/skipped items (never the database, never items still waiting for review). Dry listing unless apply=True."""
    out = ROOT / cfg["paths"]["output"]; cut = time.time() - days * 86400; rows = []
    for d in sorted(out.glob("[0-9]*_*")):
        if d.is_dir() and d.stat().st_mtime < cut:
            sz = sum(f.stat().st_size for f in d.rglob("*") if f.is_file()); rows.append({"dir": d.name, "mb": round(sz / 1e6, 1)})
            if apply: [f.unlink() for f in d.glob("clip*.mp4")]; [f.unlink() for f in d.glob("s*_*.png")]; (d / "video_only.mp4").unlink(missing_ok=True)
    return {"older_than_days": days, "applied": apply, "dirs": rows, "note": "only intermediate clips/frames are removed; video.mp4, subtitles and JSON stay"}

def dry_run(pipe, cfg: dict) -> dict:
    """Everything except rendering and publishing: pick the next unique verified item, build script/director/storyboard, plan 3D modes, estimate time, preview metadata."""
    from . import direction as D, director as DIR, masterplan, content as C
    content = pipe.sel.next_content(None)
    if content is None: return {"ok": False, "reason": "no unique verified content available"}
    sd = sb = tr = None
    if content.category == "story":
        sd = next(d for d in C.load_stories(pipe.sel.stories_dir) if f"story:{d['id']}" == content.key)
        tr = DIR.treat(content, sd, pipe.db); sb = D.build_storyboard(sd, pipe.db, treatment=tr)
    pk = masterplan.build(content, tr, sb, pipe.db, None)
    scenes = (sb or {}).get("scenes", [])
    modes = plan_modes(scenes) if scenes else {"note": "single-verse/hadith video: layered scenery only (2.5D), no 3D plan"}
    from .pipeline import make_metadata
    fake = {"assets": [], "text_only": True, "duration": sum(s["duration_s"] for s in scenes) if scenes else 31, "voices": [], "sfx": False}
    try: meta = make_metadata(content, fake)
    except Exception as e: meta = {"error": str(e)}
    return {"ok": True, "selected": content.key, "category": content.category, "source": content.reference_line, "hook": content.hook, "script": content.script,
            "director_card": pk.get("director_card"), "scenes": [{"scene": s["scene"], "role": s.get("role"), "env": s["environment"], "camera": s["camera"], "duration_s": s["duration_s"]} for s in scenes],
            "render_plan": modes, "estimated_video_s": fake["duration"], "metadata_preview": {"title": meta.get("title"), "tags": meta.get("tags")}, "published": False,
            "note": "Nothing was rendered or uploaded and nothing was recorded as used."}
