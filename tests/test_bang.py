from pathlib import Path
from ivs import bang, lemo

ROOT = Path(__file__).resolve().parent.parent

def test_reading_time_has_floor_and_grows():
    assert bang.line_seconds("a", "") == 3.5 and bang.line_seconds("x" * 200, "y" * 100) > 10

def test_vendored_bang_motion_is_mit_and_template_shows_text_unmodified():
    assert "MIT License" in (ROOT / "third_party" / "bang-motion" / "LICENSE").read_text()
    t = (ROOT / "js" / "kinetic" / "index.html").read_text()
    assert "window.OPENER" in t and "textContent=v" in t and "split(\"\")" not in t      # whole-line Arabic, never split into letters
    assert "fonts/Amiri-Regular.ttf" in t

def test_bang_brief_carries_rules_and_free_render_command():
    class P: pass
    import ivs.lemo as L
    L.verified_text = lambda pipe, key: {"key": key, "title": "T", "theme": "x", "category": "quran_ayah", "lines": [{"ar": "a", "ur": "u", "en": "e", "label": "S 1:1"}], "source": {}}
    md = L.brief(P(), "quran:1:1", None, "bang")
    assert "bang-render" in md and "No faces" in md and "Never depict Allah" in md.replace("**Never depict Allah, any prophet", "Never depict Allah")

def test_all_tool_briefs_keep_rules_and_flag_costs():
    import ivs.lemo as L
    L.verified_text = lambda pipe, key: {"key": key, "title": "T", "theme": "x", "category": "quran_ayah", "lines": [{"ar": "a", "ur": "u", "en": "e", "label": "S 1:1"}], "source": {}}
    for tool in ("lemo", "bang", "motion-kit", "animated-shorts", "opus-studio"):
        md = L.brief(object(), "quran:1:1", None, tool)
        assert "No faces" in md and "tokens" in md or tool in ("animated-shorts", "opus-studio")
        assert "faceless" in md.lower() or "No faces" in md
    assert "FACES" in L.brief(object(), "quran:1:1", None, "animated-shorts")
    assert "Route B needs" in L.brief(object(), "quran:1:1", None, "opus-studio")

def test_draw_contract_page_renders(tmp_path):
    from ivs import jsfx
    if not jsfx.available()[0]: return
    page = tmp_path / "p.html"
    page.write_text("<canvas id=c width=180 height=320></canvas><script>const x=document.getElementById('c').getContext('2d');window.__meta={W:180,H:320,FPS:6,DURATION:1};window.__draw=t=>{x.fillStyle='#223';x.fillRect(0,0,180,320);x.fillStyle='#fc6';x.fillRect(t*100,100,30,30)};window.__ready=true</script>")
    out = bang.render_html(page, tmp_path / "o.mp4", fps=6)
    assert out.exists() and out.stat().st_size > 500

def test_production_bible_is_faceless_and_tagged():
    from ivs.config import load_config
    from ivs.pipeline import Pipeline
    from ivs import content as C, direction as D, director as DIR, masterplan as M
    p = Pipeline(load_config(None)); sd = next(d for d in C.load_stories(p.sel.stories_dir, split=False) if d["id"] == "al-fil")
    c = C.build_story(sd, p.sel.quran)[0]; t = DIR.treat(c, sd, p.db); b = M.build(c, t, D.build_storyboard(sd, p.db, treatment=t), p.db)["production_bible"]
    assert "NOT MODELLED" in b["D_appearance_sheet"]["head_face_hair"] and all(x["faceless"] for x in b["C_character_roster"])
    assert set(b) >= {"A_scene_breakdown", "H_reusable_asset_library", "I_scene_asset_dependencies", "O_optimisation", "not_built_yet"}
