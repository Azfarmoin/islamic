# Capability map: which route for which idea

> Compiled from hands-on tests by Claude Opus 5.5 (October 2026). Machine: Apple M4 Pro, 24 GB RAM, everything local and free.
> When the user describes an idea, Claude checks this map to pick a route, then calls the matching skill (the front-door skill is `video-idea`).

## 1. Get one thing straight first

**Opus 5.5 does not output video pixels itself.** It writes the script, shot list and prompts, writes the animation code, looks at images and picks the good ones, and handles voice-over, subtitles, compositing and QC. The pictures come from only three sources:

| Picture source | How it works | Local tools |
|---|---|---|
| **A. Drawn by code** (2D / 3D) | Every frame is computed; text and numbers are 100 % accurate and never warp | HTML Canvas, Three.js (Chrome screenshots frame by frame), Blender scripts |
| **B. Drawn by AI** | Generate images first (FLUX) → then image-to-video (Wan 5B first/last-frame) | `draw-things-cli` + `tools/mlx_wan22_i2v.py` |
| **C. Cloud AI** (not integrated yet) | Seedance 2.0 / Kling / Veo: lip-sync, big expressions, several people in frame | Needs the user's account or API key, roughly ¥1 per second |

The videos online "made with Opus 5.5" (the 418 on Skillry, plotome's 46-minute animation) are **almost all route A**. Live-action short dramas use Opus for the script and route C for the pictures.

## 2. Route selection

| The idea looks like… | Route | Skill | Measured quality | Time per episode |
|---|---|---|---|---|
| Explaining a principle, numbers, curves, comparisons (compound interest, rule of 72, probability) | A · 2D code animation | `video-explainer` | **90 %+** (kp01) | about 30 min |
| Floor plan → CAD → 3D → sun study → phone tour | A · Three.js 3D | `video-floorplan` | **90 %** (kp03) | about 1 h |
| 3D structural explainers (heart, engine, solar system, buildings), Skillry style | A · Three.js 3D | `video-explainer` (Three.js variant; no episode made yet) | expected 90 % | about 40–60 min |
| Minimal line-art 3D stories, quiet narrated pieces like plotome | A · Blender line art | `video-lineart` | 80 % (kp02 preview; figures look puppet-like) | about 1 h (render about 9 min) |
| A cartoon character from a photo + heart-warming MV | B · 3D cartoon | `video-char-mv` | 70–80 % (kid01) | about 45 min |
| Shuai & Mei explaining a mental model in Q&A form | B · two-person 3D cartoon | `video-talk` | 70 % (no lip-sync) | about 30–60 min |
| Aju comedy skits with a twist | B · realistic cat | `video-skit` | 60 % (soft picture; a 3D cartoon cat is recommended instead) | about 12 min |
| Quote + epic animal footage | B · realistic animals | `video-quote` | 60 % | about 25 min |
| Realistic single person, realistic anthropomorphic animals, hard-hitting realism, mostly subtle motion | B · realistic + first/last frame + grading | the "realistic subtle motion" recipe in `video-idea` | stills 80 %, in motion 50 %, about 60–70 % after fixes | about 1.5–2 h per 30 s |
| Live-action lip-sync dramas, crying / laughing close-ups, fights or hugs between several people | C · cloud | not integrated | 90 % | depends on the API |

**How to choose:** use A whenever A can do it (clearest, fastest, free, no heat). Use B's cartoon style when you need characters and emotion. Use realistic B only for subtle-motion shots. Lip-sync needs C.

## 3. Measured limits per route (known pitfalls)

### A · Code animation
- **2D**: `tools/code_anim/render.py`; the HTML page needs `window.ready` and `window.draw(t)`. A ≈ 46 s video at 60 fps renders in about 7 minutes (about 0.15 s per frame).
- **Headless Chrome screenshots don't draw colour emoji**: draw icons in code (see `icon()` in `kp01_compound.html`).
- **Three.js** (renders locally with lighting and materials): starter template `tools/code_anim/three_template.html` (loads three@0.160.0 from jsdelivr through an importmap). The same render.py works; it waits for the library to load before rendering. Don't drive the page with `requestAnimationFrame`; set up the scene from t inside `draw(t)` and call `renderer.render()`; create the renderer with `preserveDrawingBuffer: true`. Load the library from a CDN or download it locally.
- **Blender 5.x** (on PATH): EEVEE + Freestyle white lines, about 0.33 s per 1080×1920 frame.
  - Subdivide large planes into a grid (`primitive_grid_add`), otherwise Freestyle can't resolve occlusion and lines behind show through.
  - Create the line style manually (`bpy.data.linestyles.new`).
  - Objects scaled down to invisibility must be turned off with `hide_render`, or they leave a small dot.
  - Subtitles are ASS with a 7 px black outline that masks the lines behind them.
  - 3D text uses the studio font (`tools/fonts/Inter-Bold.ttf`, Latin only); set `STUDIO_FONT` to a CJK font for Chinese text.

### B · Local AI
- **Images**: FLUX.2 klein 4B (`draw-things-cli generate --local --model flux_2_klein_4b_q6p.ckpt`), about 30–60 s per 1280×704 image.
  - Good at 3D cartoon; good at a single realistic person (80 %).
  - **Realistic multi-character scenes go wrong**: two heads, two hammers; **Chinese signage comes out garbled**.
  - Mitigation: only 1–2 characters per shot, 4–6 candidates per shot with Claude picking from them; no text in the picture — add it in post.
- **Image-to-video**: Wan2.2 5B (`tools/mlx_wan22_i2v.py`).
  - **At 1280×704, 121 frames (5 s) runs out of memory; 73 frames (3 s) works**, in about 4 minutes.
  - Realistic footage in motion: the person stays the same person and gestures look natural, but **the grade drifts to saturated blue and the shot gets reframed**.
  - Mitigation: always use first/last frames (`--last-image`) to lock the composition, pull the grade back with `tools/color_match.py`, then add a unified grain.
  - Two characters in physical contact fuse together; no lip-sync.
- **The machine**: cool down for 60 s between shots; ask the user before long jobs; quit Chrome and keep the lid open while generating.

### C · Cloud (to be integrated)
- Integration only needs an API key from the user. Claude then writes a script that calls the API shot by shot, at `tools/cloud_i2v.py`.

## 3.5 Lessons from viral code-made videos

See `docs/viral-code-video-notes.md` (research on Skillry and awesome-opus5-5-videos, 700+ prompts). Key points: every frame is a pure function of t; an exact palette with a single accent colour; no glow, particles or camera shake; labels as a 2D overlay; frame 1 is already a complete picture; every piece of information stays on screen for at least 2.5 s; contact sheet first, then a sample, then the full video; sound effects only on real on-screen actions (`tools/code_anim/sfx.py`). The notes also propose a few skills still to build: exploded views, zooms, QC and beat-syncing.

## 4. Verified samples (just follow them)

| Code | Route | Files |
|---|---|---|
| kp01 compound interest | A · 2D | `scripts/kp01.json` + `tools/code_anim/kp01_compound.html` → `works/kp01_compound-interest/` (with `REPRODUCE.md`) |
| kp03 two-bedroom floor plan | A · Three.js 3D | `scripts/kp03.json` + `tools/code_anim/kp03_house.html` + `sfx.py` → `works/kp03_two-bedroom-floorplan/` (with `REPRODUCE.md`) |
| kp02 sunk cost | A · Blender line art | `scripts/kp02.json` + `tools/blender_line/kp02_scene.py` + `make.py` (script only; render a 10 s preview with `--preview 10`) |
| kid01 emma's autumn | B · 3D cartoon | `scripts/kid01.json` + `tools/make_char_mv.py` (character images are personal and not in the repo) |
