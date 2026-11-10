"""Bang Motion (github.com/bangtutorial/bang-motion, MIT) support, 100% free:
 - render_html(): turns ANY Bang-Motion-style page (single index.html with window.OPENER.tl) into an MP4 with our headless Chromium + FFmpeg
   (frame-exact: time is set per frame, nothing is screen-recorded; CDN GSAP is served locally so it works offline).
 - kinetic(): a deterministic, agent-free kinetic-typography short built from VERIFIED text with a built-in GSAP template (js/kinetic).
The Bang Motion *agent skill* itself (an AI agent writing the page) costs LLM tokens, so it is vendored for manual use only: see docs/BANG_MOTION.md."""
from __future__ import annotations
import json, os, shutil, subprocess, tempfile
from pathlib import Path
from . import jsfx

ROOT = Path(__file__).resolve().parent.parent

def _encode(frames: Path, fps: int, out: Path) -> None:
    jsfx._ff("-framerate", fps, "-i", frames / "%05d.png", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out)

def render_html(html: Path, out: Path, w=1080, h=1920, fps=24, data: dict | None = None, scale=1) -> Path:
    ok, why = jsfx.available()
    if not ok: raise SystemExit(f"JS effects not available: {why} (install Node 22 and run `npm ci` in js/)")
    fr = Path(tempfile.mkdtemp())
    try:
        jsfx._node({"mode": "bang", "html": str(html), "w": w, "h": h, "fps": fps, "out": str(fr), "data": data, "scale": scale})
        out.parent.mkdir(parents=True, exist_ok=True); _encode(fr, fps, out)
    finally: shutil.rmtree(fr, ignore_errors=True)
    return out

def line_seconds(en: str, ar: str) -> float:
    """Reading time: Arabic is held longer (it is the primary text); never below 3.5 s."""
    return round(max(3.5, 1.8 + 0.055 * len(en) + 0.02 * len(ar)), 1)

def kinetic(pipe, key: str, out: Path, fps=24, w=1080, h=1920) -> Path:
    from . import lemo
    c = lemo.verified_text(pipe, key); lines = []
    for s in c["lines"]:
        lines.append({"ref": s["label"], "ar": s["ar"], "en": s["en"], "ur": s["ur"], "dur": line_seconds(s["en"], s["ar"])})
    proj = Path(tempfile.mkdtemp())
    try:
        src = ROOT / "js" / "kinetic"; shutil.copy(src / "index.html", proj / "index.html")
        shutil.copy(ROOT / "js" / "node_modules" / "gsap" / "dist" / "gsap.min.js", proj / "gsap.min.js")
        shutil.copytree(ROOT / "assets" / "fonts", proj / "fonts")
        return render_html(proj / "index.html", out, w, h, fps, data={"lines": lines, "seed": sum(map(ord, key))})
    finally: shutil.rmtree(proj, ignore_errors=True)
