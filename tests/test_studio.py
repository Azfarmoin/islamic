from ivs import studio

def sc(n, role, d): return {"scene": n, "role": role, "duration_s": d}

def test_plan_modes_priority_and_honest_labels():
    scenes = [sc(1, "hook", 4), sc(2, "setup", 10), sc(3, "peak", 6), sc(4, "setup", 12), sc(5, "conclusion", 5)]
    p = studio.plan_modes(scenes, "hd", cpus=2, safe_limit_s=3000)
    m = {r["scene"]: r["mode"] for r in p["scenes"]}
    assert m[2] == "2.5D" and m[4] == "2.5D" and m[1] != "2.5D" and m[3] != "2.5D"
    assert all(r["estimated_render_s"] == 0 for r in p["scenes"] if r["mode"] == "2.5D")
    tight = studio.plan_modes(scenes, "hd", cpus=2, safe_limit_s=100)
    assert all(r["mode"] == "2.5D" for r in tight["scenes"])            # budget too small -> never fake 3D

def test_cleanup_is_dry_by_default(tmp_path, monkeypatch):
    monkeypatch.setattr(studio, "ROOT", tmp_path); d = tmp_path / "out" / "0001_x"; d.mkdir(parents=True); (d / "clip1.mp4").write_bytes(b"x"); (d / "video.mp4").write_bytes(b"v")
    import os; os.utime(d, (1, 1))
    r = studio.cleanup({"paths": {"output": "out"}}, 1, False); assert r["dirs"] and (d / "clip1.mp4").exists()
    studio.cleanup({"paths": {"output": "out"}}, 1, True); assert not (d / "clip1.mp4").exists() and (d / "video.mp4").exists()

def test_story_split_keeps_lines_and_order():
    from ivs import content as C
    lines = [{"narration": {"en": "word " * 18, "ur": "x"}} for _ in range(12)]
    parts = C.split_story({"id": "s", "title": "S", "lines": lines}, 60)
    assert len(parts) >= 2 and sum(len(p["lines"]) for p in parts) == 12
    assert [l for p in parts for l in p["lines"]] == lines and parts[1]["id"] == "s-p2"
    short = {"id": "t", "lines": lines[:3]}; assert C.split_story(short, 60) == [short]

def test_scenery_sequence_is_distinct():
    from ivs import scenery as S
    for key in ("quran:94:5-6", "hadith:x", "quran:2:153"):
        for n in (3, 4):
            s = S.sequence("patience and hardship", key, n); assert len(s) == n == len(set(s))

def test_docfacts_blocks_uncertain_claim_stated_as_fact_and_builds_chapters():
    from ivs import docfacts as F
    ok = {"claims": [{"text": "t", "status": "uncertain", "source": "s", "match": "army"}], "lines": [{"narration": {"en": "Reports say an army came."}}]}
    bad = {"claims": [{"text": "t", "status": "uncertain", "source": "s", "match": "army"}], "lines": [{"narration": {"en": "An army came."}}]}
    assert F.validate_claims(ok) == [] and F.validate_claims(bad)
    assert F.validate_claims({"claims": [{"text": "t", "status": "sure", "source": "s"}]})
    assert F.chapters([(0, "hook"), (5, "narration"), (20, "narration"), (30, "ayah"), (45, "outro")])[0].startswith("0:00 Opening")
    assert F.chapters([(0, "hook"), (4, "narration")]) == []

def test_video_director_for_verse_and_story():
    from types import SimpleNamespace as N
    c = N(key="quran:1:1", reference_line="r", category="quran_ayah", source={})
    d = studio.video_director(c, {}, {}, {"marks": [(0, "hook"), (5, "ayah"), (20, "outro")], "duration": 30}, {"passed": True})
    assert len(d["shots"]) == 3 and d["emotion_arc"][0] == "curiosity" and d["shots"][1]["characters"] == "none"
    pk = {"film_plan": {"scenes": [{"scene": 1, "duration_s": 5, "narration": "n", "purpose": "hook", "story_beat": "Hook", "environment": {"location": "x", "lighting": "l"},
          "characters": {"who": "none", "action": "none"}, "props": "none", "camera": {"type": "wide", "lens_mm": 28, "move": "push"}, "sound": "s", "transition": "cut"}]}}
    assert studio.video_director(c, pk, {}, None, {"passed": True})["shots"][0]["shot_id"] == "1.1"

def test_production_files_complete_and_honest():
    from types import SimpleNamespace as N
    c = N(key="story:x", reference_line="r", category="story", source={})
    pk = {"film_plan": {"scenes": [{"scene": 1, "duration_s": 5, "narration": "n", "purpose": "hook", "story_beat": "Question", "environment": {"location": "x", "lighting": "l"},
          "characters": {"who": "spearmen x3", "action": "march"}, "props": "spears", "camera": {"type": "wide", "lens_mm": 28, "move": "push"}, "sound": "s", "transition": "cut"}]}}
    f = studio.production_files(c, pk, {}, {"assets": [], "marks": []}, {"passed": True})
    for n in ("SHOT_LIST", "CHARACTER_BIBLE", "ENVIRONMENT_BIBLE", "PROP_BIBLE", "CAMERA_PLAN", "ANIMATION_PLAN", "VFX_PLAN", "SFX_TIMELINE", "LIGHTING_PLAN", "EDIT_TIMELINE", "CONTINUITY", "AUTHENTICITY_NOTES"):
        assert n + ".json" in f
    assert f["CAMERA_PLAN.json"]["shots"][0]["aperture"] == "not modelled" and f["EDIT_TIMELINE.json"]["total_s"] == 5

def test_explanation_plan_honest():
    from ivs import explain
    assert explain.technique_for("The army marched toward the city")["technique"] == "map_route"
    assert explain.technique_for("The water rose")["rendered"] is False
    from types import SimpleNamespace as N
    c = N(key="story:x", reference_line="r", category="story", source={})
    pk = {"film_plan": {"scenes": [{"scene": 1, "duration_s": 5, "narration": "Then the sea rose.", "purpose": "hook", "story_beat": "Question", "environment": {"location": "x", "lighting": "l"},
          "characters": {"who": "none", "action": "none"}, "props": "none", "camera": {"type": "wide", "lens_mm": 28, "move": "push"}, "sound": "s", "transition": "cut"}]}}
    f = studio.production_files(c, pk, {}, {"assets": [], "marks": []}, {"passed": True})
    assert f["EXPLANATION_PLAN.json"]["summary"]["planned_only"] >= 1 and "human_review" in f["PRODUCTION_CHECKLIST.json"]
