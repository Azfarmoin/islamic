from __future__ import annotations
import argparse, json, os, subprocess, sys
from pathlib import Path
from .config import load_config
from .pipeline import Pipeline

def cfg_path(cfg, rel):
    return Path(__file__).resolve().parent.parent / rel

def main(argv=None):
    ap = argparse.ArgumentParser(prog="ivs", description="Islamic Video Engine (zero-cost)")
    ap.add_argument("--config", default=None)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init", help="create database")
    sub.add_parser("verify-data", help="check pinned Quran data + run verification over the whole catalog")
    sub.add_parser("make", help="generate the next unique verified video now")
    sub.add_parser("list", help="show items")
    p = sub.add_parser("approve"); p.add_argument("id", type=int)
    p = sub.add_parser("skip"); p.add_argument("id", type=int)
    p = sub.add_parser("rerender"); p.add_argument("id", type=int)
    p = sub.add_parser("publish"); p.add_argument("id", type=int); p.add_argument("--publish-at", default=None)
    sub.add_parser("tick", help="one scheduler iteration")
    sub.add_parser("daemon", help="run scheduler loop")
    p = sub.add_parser("dashboard"); p.add_argument("--port", type=int, default=8787)
    sub.add_parser("audit", help="license / zero-cost audit")
    sub.add_parser("auth-youtube", help="OAuth setup (prints refresh token)")
    p = sub.add_parser("storyboard", help="creative direction + storyboard + QC for a story"); p.add_argument("story", nargs="?")
    p = sub.add_parser("shot", help="render one storyboard scene in Blender (3D)"); p.add_argument("story"); p.add_argument("scene", type=int)
    p.add_argument("--tier", default="draft", choices=["draft", "hd", "full"]); p.add_argument("--seconds", type=float, default=None)
    p = sub.add_parser("film", help="full story film with 3D shots (slow: renders Blender shots first)"); p.add_argument("story")
    p.add_argument("--tier", default=None, choices=["draft", "hd", "full"]); p.add_argument("--max-3d-seconds", type=float, default=None)
    p = sub.add_parser("draft-story", help="AI-assisted story draft (local Ollama or deterministic fallback) -> content/stories/drafts/")
    p.add_argument("ref", help="e.g. 105:1-5"); p.add_argument("--id", required=True); p.add_argument("--title", required=True); p.add_argument("--theme", default="lessons from the Quran")
    p.add_argument("--notes", default=None, help="YAML file: list of {text, source} from tafsir/books you checked"); p.add_argument("--model", default="qwen2.5:3b"); p.add_argument("--no-llm", action="store_true")
    sub.add_parser("hardware", help="detect CPU/RAM/GPU and show the render tier plan")
    p = sub.add_parser("ci-run", help="GitHub Actions: one tick (make due video, publish approved/auto) + report"); 
    p = sub.add_parser("ci-command", help="parse an issue comment: prints 'approve N' / 'skip N' or exits 2"); p.add_argument("text")
    p = sub.add_parser("ci-act", help="GitHub Actions: approve or skip an item (re-renders if the file is gone) and publish"); p.add_argument("action", choices=["approve", "skip"]); p.add_argument("id", type=int)
    p = sub.add_parser("draft-queue", help="draft the next N entries of content/queue.yaml into content/stories/ (flagged needs_human_review)"); p.add_argument("--n", type=int, default=1); p.add_argument("--model", default=None)
    sub.add_parser("lemo-styles", help="rank the vendored Lemo-Opuscar styles by how figure-free they are")
    p = sub.add_parser("lemo-brief", help="write a film brief (verified text + religious rules) for the Lemo-Opuscar Claude Code plugin"); p.add_argument("key", help="story:<id> or quran:<surah>:<a>[-<b>]"); p.add_argument("--style", default=None); p.add_argument("--out", default=None); p.add_argument("--tool", choices=["lemo", "bang", "motion-kit", "animated-shorts", "opus-studio"], default="lemo")
    p = sub.add_parser("package", help="write the Master Director package (director/authenticity cards, scene table, prompts, QC checklist) for story:<id> or quran:S:A"); p.add_argument("key"); p.add_argument("--out", default=None)
    p = sub.add_parser("kinetic", help="free kinetic-typography short (GSAP template) from verified text: story:<id> or quran:S:A"); p.add_argument("key"); p.add_argument("--out", default="kinetic.mp4"); p.add_argument("--fps", type=int, default=24)
    p = sub.add_parser("bang-render", help="render any Bang-Motion-style index.html (window.OPENER.tl) to MP4, free, offline"); p.add_argument("html"); p.add_argument("--out", default="bang.mp4"); p.add_argument("--w", type=int, default=1080); p.add_argument("--h", type=int, default=1920); p.add_argument("--fps", type=int, default=24)
    sub.add_parser("test-3d", help="build and render one real Blender 3D test scene -> output/test_3d/test_3d.{blend,mp4,json}")
    sub.add_parser("dry-run", help="everything except rendering/publishing: selected topic, source, script, director, scenes, render plan, metadata")
    sub.add_parser("validate", help="check config, zero-cost mode, workflows, data, tools, secrets presence")
    sub.add_parser("status", help="item counts by status"); p = sub.add_parser("fetch-recitation", help="pre-download authentic recitation for every verse the project uses (curated ayat, story verses, Quranic duas)"); p.add_argument("--all", action="store_true", help="the whole Quran (6236 files)"); sub.add_parser("stats", help="fetch views/likes/comments for published videos + advisory learning notes"); sub.add_parser("test", help="run the automated test suite"); sub.add_parser("render-test", help="render one tiny 2.5D scenery clip")
    p = sub.add_parser("cleanup", help="remove old intermediate files"); p.add_argument("--days", type=int, default=14); p.add_argument("--apply", action="store_true")
    sub.add_parser("pause"); sub.add_parser("resume")
    a = ap.parse_args(argv)
    cfg = load_config(a.config)
    if a.cmd == "film":
        cfg = json.loads(json.dumps(cfg)); cfg["paths"] = {"db": "output/film/film.sqlite3", "output": "output/film", "cache": "output/film/cache"}
        cfg.setdefault("three_d", {}).update({"enabled": True, **({"tier": a.tier} if a.tier else {}), **({"max_seconds": a.max_3d_seconds} if a.max_3d_seconds else {})})
    if a.cmd.startswith("ci-") or a.cmd == "draft-queue":
        from . import ci as CI
        CI.apply_overrides(cfg)
    pipe = Pipeline(cfg)

    if a.cmd == "init":
        print("database ready:", pipe.db.path)
    elif a.cmd == "verify-data":
        from .catalog import QURAN
        from .content import build_quran, build_hadith
        from .catalog import HADITH
        bad = 0
        for e in QURAN:
            c, rep = build_quran(pipe.sel.quran, e)
            print(("OK  " if c else "FAIL"), f"{e[0]}:{e[1]}-{e[2]}", rep["problems"]); bad += c is None
        for e in HADITH:
            c, rep = build_hadith(pipe.sel.hadith, e)
            print(("OK  " if c else "FAIL"), f"hadith {e['collection']} {e['number']}", rep["problems"]); bad += c is None
        sys.exit(1 if bad else 0)
    elif a.cmd == "make":
        i = pipe.make_next()
        if i is None: print("No sufficiently unique verified content available; skipped (nothing fabricated).")
        else:
            it = pipe.db.get_item(i); print(f"item {i}: {it['status']}  {it['video_path']}  {it['error'] or ''}")
    elif a.cmd in ("storyboard", "shot"):
        from .content import load_stories
        from . import direction as D
        for st in load_stories(cfg_path(cfg, "content/stories")):
            if a.story and st["id"] != a.story: continue
            sb = D.build_storyboard(st, pipe.db); qc = D.qc_storyboard(sb, pipe.db)
            if a.cmd == "storyboard":
                D.save(pipe.db, st, sb, qc); print(json.dumps({"concept": sb["concept"], "characters": sb["characters"], "scenes": sb["scenes"], "qc": qc}, ensure_ascii=False, indent=1))
            else:
                from .blender_shot import render_shot
                print(render_shot(sb["scenes"][a.scene - 1], sb["characters"], a.tier, Path("output/shots") / f"{st['id']}_s{a.scene}_{a.tier}.mp4", seconds=a.seconds))
    elif a.cmd == "film":
        pipe.render_3d = True; pipe.cfg["script"]["require_review"] = True
        i = pipe.make_next(only=f"story:{a.story}")
        if i is None: print("story not available (verification/duplicate)"); sys.exit(1)
        it = pipe.db.get_item(i); print(f"item {i}: {it['status']}  {it['video_path']}  {it['error'] or ''}")
    elif a.cmd == "draft-story":
        import yaml as _y
        from .scriptgen import draft_story, Ollama
        notes = _y.safe_load(Path(a.notes).read_text(encoding="utf-8")) if a.notes else []
        st, rep = draft_story(pipe.sel.quran, a.ref, a.id, a.title, a.theme, notes, None if a.no_llm else __import__('ivs.scriptgen', fromlist=['pick_llm']).pick_llm(a.model), Path(__file__).resolve().parent.parent / "content" / "stories" / "drafts")
        print(json.dumps(rep, ensure_ascii=False, indent=1)); print("draft saved to content/stories/drafts/" + a.id + ".yaml" if st else "failed")
    elif a.cmd == "hardware":
        from . import hardware as HW
        hw = HW.detect(); print(json.dumps({"hardware": hw, "plan": HW.effective_three_d(cfg, hw)}, indent=1))
    elif a.cmd == "kinetic":
        from . import bang
        print(bang.kinetic(pipe, a.key, Path(a.out), a.fps))
    elif a.cmd == "bang-render":
        from . import bang
        print(bang.render_html(Path(a.html), Path(a.out), a.w, a.h, a.fps))
    elif a.cmd == "package":
        from . import masterplan, lemo, direction as _D, director as _DIR, content as _C
        if a.key.startswith("story:"):
            sd = next((d for d in _C.load_stories(pipe.sel.stories_dir) if f"story:{d['id']}" == a.key), None)
            if sd is None: raise SystemExit("unknown story (drafts awaiting review are not loaded)")
            c = _C.build_story(sd, pipe.sel.quran)[0]; t = _DIR.treat(c, sd, pipe.db); sb = _D.build_storyboard(sd, pipe.db, treatment=t)
        else:
            _, s, rng = a.key.split(":"); a1, _, a2 = rng.partition("-"); c = _C.build_quran_seq(pipe.sel.quran, int(s), int(a1), int(a2 or a1))[0]; t = sb = None
        pk = masterplan.build(c, t, sb, pipe.db); md = masterplan.to_markdown(pk)
        if a.out: Path(a.out).write_text(md, encoding="utf-8"); print("written", a.out)
        else: print(md)
    elif a.cmd == "lemo-styles":
        from . import lemo
        for s in lemo.styles(): print(f"{s['slug']:24} {s['name'][:32]:32} figure-density {s['figure_density']:5}  religious-imagery {s['religious_imagery_mentions']}")
    elif a.cmd == "lemo-brief":
        from . import lemo
        txt = lemo.brief(pipe, a.key, a.style, a.tool)
        if a.out: Path(a.out).write_text(txt, encoding="utf-8"); print("written", a.out)
        else: print(txt)
    elif a.cmd == "ci-command":
        from .ci import parse_command
        r = parse_command(a.text)
        if not r: sys.exit(2)
        print(f"{r[0]} {r[1]}")
    elif a.cmd == "ci-run":
        from . import ci as CI
        from .scheduler import tick
        from .publish_youtube import YouTubePublisher
        yt_on = cfg["publishing"]["platforms"]["youtube"]["enabled"]
        res = tick(pipe, YouTubePublisher(cfg, pipe.db) if yt_on else None)
        rep = CI.build_report(pipe, res); CI.write_outputs(rep); print(json.dumps(rep, indent=1, ensure_ascii=False))
        if rep["errors"] or any(i["status"] == "failed" for i in rep["generated"]): sys.exit(1)
    elif a.cmd == "ci-act":
        it = pipe.db.get_item(a.id)
        if it is None: print("no such item"); sys.exit(1)
        if a.action == "skip": pipe.skip(a.id); print(f"item {a.id} skipped"); sys.exit(0)
        if it["status"] in ("published",): print("already published"); sys.exit(0)
        if not it["video_path"] or not Path(it["video_path"]).exists(): pipe.render_item(a.id); it = pipe.db.get_item(a.id)      # fresh runner: rebuild the same verified content
        if it["status"] == "failed": print("render failed:", it["error"]); sys.exit(1)
        pipe.approve(a.id)
        if cfg["publishing"]["platforms"]["youtube"]["enabled"]:
            from .publish_youtube import YouTubePublisher
            print(YouTubePublisher(cfg, pipe.db).publish(a.id)["url"])
        else: print(f"item {a.id} approved (YouTube secrets not set: nothing uploaded)")
    elif a.cmd == "draft-queue":
        import yaml as _y
        from .scriptgen import draft_story, Ollama
        from .content import load_stories
        root = Path(__file__).resolve().parent.parent; sd = root / "content" / "stories"
        have = {p.stem for p in sd.glob("*.yaml")}; queue = _y.safe_load((root / "content" / "queue.yaml").read_text(encoding="utf-8")) or []
        from .scriptgen import pick_llm
        llm = pick_llm(a.model); print("LLM:", type(llm).__name__ if llm else "none (deterministic fallback)")
        done = 0
        for e in queue:
            if e["id"] in have: continue
            st, rep = draft_story(pipe.sel.quran, e["ref"], e["id"], e["title"], e.get("theme", "lessons from the Quran"), e.get("notes", []), llm, sd)
            print(e["id"], rep.get("mode"), "dropped:", len(rep.get("dropped", [])), rep.get("problems", []))
            if st: done += 1
            if done >= a.n: break
        if done == 0: print("queue empty: nothing to draft")
    elif a.cmd == "list":
        for r in pipe.db.items():
            print(f"{r['id']:>3}  {r['status']:<12} {r['key']:<24} {r['title'] or ''}")
    elif a.cmd == "approve": pipe.approve(a.id); print("approved", a.id)
    elif a.cmd == "skip": pipe.skip(a.id); print("skipped", a.id)
    elif a.cmd == "rerender": print(json.dumps(pipe.render_item(a.id).get("failed", []))); 
    elif a.cmd == "publish":
        from .publish_youtube import YouTubePublisher
        print(YouTubePublisher(cfg, pipe.db).publish(a.id, a.publish_at))
    elif a.cmd == "tick":
        from .scheduler import tick
        from .publish_youtube import YouTubePublisher
        print(tick(pipe, YouTubePublisher(cfg, pipe.db)))
    elif a.cmd == "daemon":
        from .scheduler import daemon
        from .publish_youtube import YouTubePublisher
        daemon(pipe, YouTubePublisher(cfg, pipe.db))
    elif a.cmd == "dashboard":
        from .dashboard import create_app
        create_app(pipe).run(host="127.0.0.1", port=a.port)
    elif a.cmd == "audit":
        from .audit import run_audit
        r = run_audit(cfg)
        for d in r["dependencies"]: print(" | ".join(d))
        print()
        for c in r["checks"]: print(c["status"].upper().ljust(5), c["name"], "-", c["detail"])
        print("\nFree-tier limits (never assumed unlimited):")
        for n_, d_ in r["free_tier_limits"]: print(" -", n_ + ":", d_)
    elif a.cmd == "auth-youtube":
        from .publish_youtube import auth_flow, load_env
        load_env(Path(cfg["_root"]) / ".env")
        cid, sec = os.environ.get("YOUTUBE_CLIENT_ID"), os.environ.get("YOUTUBE_CLIENT_SECRET")
        if not (cid and sec): sys.exit("Set YOUTUBE_CLIENT_ID and YOUTUBE_CLIENT_SECRET in .env first (docs/YOUTUBE_SETUP.md)")
        print("YOUTUBE_REFRESH_TOKEN=" + auth_flow(cid, sec))
    elif a.cmd == "test-3d":
        from . import studio; r = studio.test_3d(cfg); print(json.dumps(r, indent=1)); sys.exit(0 if r["ok"] else 1)
    elif a.cmd == "dry-run":
        from . import studio; print(json.dumps(studio.dry_run(pipe, cfg), indent=1, ensure_ascii=False, default=str))
    elif a.cmd == "validate":
        from . import studio; r = studio.validate(cfg, pipe); print(json.dumps(r, indent=1)); sys.exit(0 if r["ok"] else 1)
    elif a.cmd == "fetch-recitation":
        from . import audio as AU, content as C
        from .catalog import QURAN
        refs = []
        if a.all:
            refs = [(s_, a_) for s_ in range(1, 115) for a_ in range(1, pipe.sel.quran.verse_count(s_) + 1)]
        else:
            for e in QURAN: refs += [(e[0], x) for x in range(e[1], e[2] + 1)]
            for d in C.load_stories(pipe.sel.stories_dir, split=False):
                for l in d.get("lines", []):
                    if l.get("quran"):
                        sur, _, rng = str(l["quran"]).partition(":"); a1, _, a2 = rng.partition("-"); refs += [(int(sur), x) for x in range(int(a1), int(a2 or a1) + 1)]
        refs = list(dict.fromkeys(refs)); cache = Path(cfg["_root"]) / cfg["paths"]["cache"] if "cache" in cfg.get("paths", {}) else Path(cfg["_root"]) / "data" / "cache"
        r = AU.prefetch(cfg, cache, refs); print(json.dumps({"verses": len(refs), **r}, indent=1)); sys.exit(0 if not r["missing"] else 1)
    elif a.cmd == "stats":
        from . import analytics; from .publish_youtube import YouTubePublisher
        print(json.dumps(analytics.collect(pipe.db, YouTubePublisher(cfg, pipe.db)), indent=1, default=str))
    elif a.cmd == "status":
        from . import studio; print(json.dumps(studio.status(pipe), indent=1, default=str))
    elif a.cmd == "cleanup":
        from . import studio; print(json.dumps(studio.cleanup(cfg, a.days, a.apply), indent=1))
    elif a.cmd == "test":
        sys.exit(subprocess.call([sys.executable, "-m", "pytest", "-q", str(Path(__file__).resolve().parent.parent / "tests")]))
    elif a.cmd == "render-test":
        from . import anim; import tempfile
        d = Path(tempfile.mkdtemp()); A = anim.build_assets(Path(cfg["_root"]) / cfg["paths"]["cache"]); o = anim.scene_clip(A, "desert_dawn", None, 1.5, 12, d / "t.mp4", None); print("ok", o, o.stat().st_size)
    elif a.cmd in ("pause", "resume"):
        pipe.db.put_setting("paused", "1" if a.cmd == "pause" else "0"); print(a.cmd + "d")

if __name__ == "__main__":
    main()
