import json, yaml
from pathlib import Path
from ivs import ci

def test_parse_command_strict():
    assert ci.parse_command("/approve 12") == ("approve", 12)
    assert ci.parse_command("/skip 3\nthanks") == ("skip", 3)
    for bad in ["/approve 12; rm -rf /", "/approve", "/approve -1", "approve 1", "/approve 1 2", "", "x\n/approve 1", "/approve $(id)"]:
        assert ci.parse_command(bad) is None

def test_overrides_need_all_secrets():
    cfg = ci.apply_overrides({}, {"YOUTUBE_CLIENT_ID": "a"})
    assert cfg["publishing"]["platforms"]["youtube"]["enabled"] is False and cfg["three_d"]["enabled"] is False
    full = {"YOUTUBE_CLIENT_ID": "a", "YOUTUBE_CLIENT_SECRET": "b", "YOUTUBE_REFRESH_TOKEN": "c", "IVS_YT_PRIVACY": "private"}
    c2 = ci.apply_overrides({}, full)
    assert c2["publishing"]["platforms"]["youtube"]["enabled"] and c2["publishing"]["platforms"]["youtube"]["privacy"] == "private"
    assert ci.apply_overrides({}, {"IVS_MODE": "bogus"})["publishing"]["mode"] == "auto"

def test_drafts_are_not_loaded(tmp_path):
    from ivs.content import load_stories
    (tmp_path / "a.yaml").write_text(yaml.safe_dump({"id": "a"}))
    (tmp_path / "b.yaml").write_text(yaml.safe_dump({"id": "b", "draft": {"needs_human_review": True}}))
    assert [d["id"] for d in load_stories(tmp_path)] == ["a"]

def test_workflows_are_safe():
    root = Path(__file__).resolve().parent.parent
    for f in (root / ".github" / "workflows").glob("*.yml"):
        y = yaml.safe_load(f.read_text()); assert y.get("jobs")
        txt = f.read_text()
        assert "github.event.comment.body }}" not in txt.replace("COMMENT: ${{ github.event.comment.body }}", "")   # comment only via env
        assert "secrets.GITHUB_TOKEN" in txt or "peter-evans" in txt or f.name == "draft-scripts.yml"
    ap = (root / ".github/workflows/approve.yml").read_text()
    assert "repository_owner" in ap

def test_queue_valid():
    q = yaml.safe_load((Path(__file__).resolve().parent.parent / "content" / "queue.yaml").read_text())
    assert q and all({"id", "ref", "title"} <= set(e) for e in q)

def test_sequence_pool_is_huge_unique_and_covers_quran():
    from ivs.config import load_config
    from ivs.quran import Quran
    from ivs import content as C
    q = Quran(load_config(None))
    ch = list(C.seq_chunks(q))
    keys = [(s, a1, a2) for s, a1, a2 in ch]
    assert len(set(keys)) == len(keys) > 1500
    assert sum(b - a + 1 for _, a, b in ch) == 6236
    c, rep = C.build_quran_seq(q, *ch[0]); assert c and c.script is None and not c.needs_review

def test_sequence_content_rebuilds_from_key_and_threshold():
    from ivs.config import load_config
    from ivs.quran import Quran
    from ivs import content as C, engagement
    q = Quran(load_config(None)); s, a, b = list(C.seq_chunks(q))[5]
    c, _ = C.build_quran_seq(q, s, a, b)
    assert c.key == f"quran:{s}:{a}-{b}" if a != b else f"quran:{s}:{a}"
    assert engagement.min_for(c) == 70 and engagement.min_for(C.build_quran(q, __import__("ivs.catalog", fromlist=["x"]).QURAN[0])[0]) == 80

def test_ten_per_day_capped_by_quota():
    s = ci.slots_for({})
    assert s["videos_per_day"] == 5 and len(set(s["times"])) == 5            # default 5/day, fits the free quota
    s = ci.slots_for({"IVS_VIDEOS_PER_DAY": "10"}); assert s["videos_per_day"] == 6   # 10 asked, free quota allows 6
    s = ci.slots_for({"IVS_VIDEOS_PER_DAY": "10", "IVS_YT_QUOTA": "20000"})
    assert s["videos_per_day"] == 10 and s["times"][0] == "06:00" and len(set(s["times"])) == 10 and all(t < "24:00" for t in s["times"])
    assert ci.slots_for({"IVS_VIDEOS_PER_DAY": "3"})["videos_per_day"] == 3

def test_master_director_package_story_and_ayah():
    from ivs.config import load_config
    from ivs.pipeline import Pipeline
    from ivs import content as C, direction as D, director as DIR, masterplan as M
    p = Pipeline(load_config(None))
    sd = next(d for d in C.load_stories(p.sel.stories_dir, split=False) if d["id"] == "iqra")
    c = C.build_story(sd, p.sel.quran)[0]; t = DIR.treat(c, sd, p.db); sb = D.build_storyboard(sd, p.db, treatment=t)
    pk = M.build(c, t, sb, p.db); md = M.to_markdown(pk)
    for h in ("DIRECTOR CARD", "AUTHENTICITY CARD", "SCENE TABLE", "CONTINUITY BIBLE", "AI GENERATION PROMPTS", "QUALITY CONTROL"): assert h in md
    assert all("no faces" in x["prompt"].lower() and "no prophet" in x["prompt"].lower() for x in pk["ai_generation_prompts"])
    fr = pk["frame_records"]; assert len(fr["records"]) == len(pk["scene_table"]) > 0 and "SECOND CONTINUITY PASS" in md and "FRAME RECORDS" in md
    assert all(r["CHARACTER EXPRESSIONS"].startswith("none") and len(r) >= 25 for r in fr["records"]) and fr["second_pass"]["checked"] == len(fr["records"])
    assert "FILM PLAN" in md and "PRODUCTION TABLE" in md and "CONTINUITY LOCK" in md and all(o["characters"]["face"].startswith("none") for o in pk["film_plan"]["scenes"])
    states = {x["check"]: x["state"] for x in pk["quality_control"]}
    assert states["Prophets are not directly depicted"] == "PASS" and states["No fake quotations"] == "MANUAL"      # human items are never ticked for you
    ay = C.build_quran_seq(p.sel.quran, 114, 1, 4)[0]; pk2 = M.build(ay, None, None, p.db)
    assert pk2["authenticity_card"]["classification"][0]["class"] == "A" and pk2["scene_table"] == [] and pk2["frame_records"] == {}
