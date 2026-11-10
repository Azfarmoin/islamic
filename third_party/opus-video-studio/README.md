# Opus Video Studio

**A short-video studio where Claude Opus 5.5 writes the script and the code, and your Mac renders the video.**

You describe an idea in one sentence, or drop in a screenshot of a video you like. Claude picks a production route, writes the copy, the shot list and the animation code, renders a preview for you to approve, then produces a finished vertical video with voice-over, subtitles, a cover and ready-to-paste post copy for Douyin / Xiaohongshu (or any short-video platform). Most videos are **drawn entirely by code** (Canvas 2D, Three.js, Blender), so text, numbers and diagrams are pixel-perfect. When a story needs characters, it uses **local AI models** (FLUX.2 klein 4B for keyframes and Wan2.2 5B first/last-frame image-to-video). Everything runs locally and costs nothing per video.

## Sample videos

Both samples are English re-renders of pieces originally made in Chinese, and both are 100 % code-drawn with no AI imagery.

| | |
|---|---|
| ![kp01 cover](works/kp01_compound-interest/kp01_cover.jpg) | ![kp03 cover](works/kp03_two-bedroom-floorplan/kp03_cover.jpg) |
| **[kp01 · Compound Interest](works/kp01_compound-interest/kp01.mp4)**: a 2D Canvas explainer, ≈ 45 s at 60 fps. 1.01^365 vs 0.99^365, numbers counting up day by day and a curve drawn from the formula. [How it was made](works/kp01_compound-interest/REPRODUCE.md) | **[kp03 · Two-Bedroom Floor Plan](works/kp03_two-bedroom-floorplan/kp03.mp4)**: Three.js 3D, ≈ 70 s at 60 fps. Plan → CAD sheets → walls rise → room-by-room tour → sun study → phone listing, with code-synthesised sound effects. [How it was made](works/kp03_two-bedroom-floorplan/REPRODUCE.md) · [Original plan](works/kp03_two-bedroom-floorplan/PLAN.md) |

## How it works

Opus 5.5 does not output video pixels itself. It writes the script, prompts and **code**, reviews stills and contact sheets, and runs voice-over, subtitles, compositing and QC. The pictures come from one of three routes:

| Route | Picture source | Strengths | Tools |
|---|---|---|---|
| **A · Code** | Every frame is computed by a program: `window.draw(t)` in headless Chrome, or a Blender Python scene | Crisp text, exact numbers and diagrams, deterministic, fast, no GPU heat | Canvas 2D, Three.js, Blender (EEVEE + Freestyle), Playwright, ffmpeg |
| **B · Local AI** | FLUX.2 klein 4B draws a first and a last frame for each shot, and Wan2.2 5B fills in the motion between them | Characters, emotion, cartoon worlds | Draw Things (`draw-things-cli`), FastVideo / FastMetal-5B-QAD on MLX |
| **C · Cloud AI** | Seedance / Kling / Veo style APIs | Lip-sync, big expressions, multi-person action | *not integrated*; would need your own API key |

Rule of thumb: **use A whenever it can do the job**. Use B for character-driven stories, preferably in a 3D-cartoon style. Realistic B footage is best kept to subtle-motion shots. See [`docs/capability-map.md`](docs/capability-map.md) for measured quality per route (honest numbers: code explainers ≈ 90 %, 3D cartoon MVs ≈ 70–80 %, realistic AI footage ≈ 50–60 %) and hard limits. For example, the local 5B model runs out of memory at 121 frames at 1280×704, while 73 frames is fine.

Each voice line is synthesised with **edge-tts**: `en-US-AndrewNeural` narration by default, with `en-US-AvaNeural` and `en-US-BrianNeural` for second characters. Any edge-tts voice works, Chinese ones included.

## Quick start

### Requirements

- macOS on Apple Silicon (tested on an M4 Pro with 24 GB). Route A also works on any machine that has Chrome and ffmpeg
- **Google Chrome** (Playwright drives it with `channel='chrome'`)
- **Python 3** with `playwright` and `numpy` (code animation) and `edge-tts` (voice-over; needs internet)
- **ffmpeg** built with libass / drawtext
- Optional:
  - **Blender 5.x** for line-art videos
  - **Draw Things** + `draw-things-cli` with the FLUX.2 klein 4B model, for AI keyframes
  - **FastVideo + the FastMetal-5B-QAD model** (≈ 20 GB) for local image-to-video
  - a Python 3.11+ env with numpy / opencv / pillow for the character-MV and dialogue pipelines

### Install

```bash
git clone https://github.com/xdis/opus-video-studio.git && cd opus-video-studio
pip install playwright numpy edge-tts      # Playwright uses your installed Chrome, no browser download needed
brew install ffmpeg
# optional
brew install --cask blender
brew install draw-things-cli               # then download FLUX.2 klein 4B in the Draw Things app
```

The local video model is **not in this repo**. To use route B, clone [FastVideo](https://github.com/hao-ai-lab/FastVideo) into `engines/FastVideo` (with its own `.venv`) and download the model into `engines/models/FastMetal-5B-QAD`, for example with `hf download FastVideo/FastMetal-5B-QAD --local-dir engines/models/FastMetal-5B-QAD`. `engines/` is gitignored.

### Self-test

```bash
zsh tools/smoke_test.sh     # about 2 minutes, prints ALL PASSED; optional components show as warnings
```

### Render the samples yourself

```bash
python3 tools/code_anim/render.py scripts/kp01.json --stills 0,10,20,30     # a few stills to check (assets/kp01/stills/)
caffeinate -i python3 tools/code_anim/render.py scripts/kp01.json           # full video → works/kp01_compound-interest/kp01.mp4
caffeinate -i python3 tools/code_anim/render.py scripts/kp03.json && python3 tools/code_anim/sfx.py scripts/kp03.json
```

Or open the repo in Claude Code and just say *"make an explainer animation about the rule of 72"*.

## Commands per pipeline

Run these from the repo root. `NN` is the next unused episode number. Full details are in [`docs/skills-index.md`](docs/skills-index.md).

| Pipeline | Commands |
|---|---|
| Code explainer (2D / Three.js) | `python3 tools/code_anim/render.py scripts/kpNN.json --stills 0,5,12` → `caffeinate -i python3 tools/code_anim/render.py scripts/kpNN.json` → optional `python3 tools/code_anim/sfx.py scripts/kpNN.json` |
| Floor-plan animation | same as above, starting from `scripts/kp03.json` + `tools/code_anim/kp03_house.html` |
| Blender line art | `python3 tools/blender_line/make.py scripts/kpNN.json --stills 50,200` → `--preview 10` → full render without flags |
| Quote video / comedy skit | `python make_video.py scripts/epNN.json --provider local-video` → `python check_video.py scripts/epNN.json` |
| Photo-character MV | `python tools/make_char_mv.py scripts/kidNN.json --only 1` → without `--only` for all shots → `--compose` to re-mix |
| Two-character dialogue | `python tools/make_talk_mv.py scripts/zyNN.json --preview 3` → without flags for the full episode |

Text uses `tools/fonts/Inter-Bold.ttf` (Latin only) by default. For Chinese or other CJK on-screen text, point `STUDIO_FONT` at a CJK font: `STUDIO_FONT=/path/to/NotoSansSC-Bold.otf python3 tools/code_anim/render.py ...`.

## Repository layout

```
opus-video-studio/
├── .claude/skills/        8 Claude Code skills (one per pipeline, plus the video-idea front door)
├── CLAUDE.md              standing instructions for Claude in this repo
├── docs/
│   ├── capability-map.md          which route for which idea, measured limits
│   ├── skills-index.md            every skill with commands to reproduce it
│   ├── pipelines.md               tools, lessons learned, route comparison
│   └── viral-code-video-notes.md  research notes on viral "Opus writes code → video" works
├── scripts/               one JSON per video: lines, shots, prompts, subtitles, music
│   └── kp01 kp02 kp03 ep01 ep04 ep05 ep06 kid01 zy01
├── characters/            character cards with prompt lock blocks (Aju the cat; Shuai & Mei)
├── tools/
│   ├── code_anim/         render.py (Chrome frame renderer), sfx.py, kp01/kp03 pages, three_template.html
│   ├── blender_line/      make.py + kp02_scene.py (EEVEE + Freestyle line art)
│   ├── fonts/             Inter-Bold.ttf + OFL license
│   ├── mlx_wan22_i2v.py   Wan2.2 5B first/last-frame image-to-video
│   ├── make_char_mv.py    photo-character MV pipeline
│   ├── make_talk_mv.py    two-character dialogue pipeline
│   ├── color_match.py     pull AI footage back to a reference grade
│   ├── clean_keyframe.py  inpaint watermarks / burned-in subtitles
│   └── smoke_test.sh      self-test
├── make_video.py          vertical AI-footage pipeline (quote videos, skits)
├── make_fable.py          horizontal multi-character fable pipeline
├── check_video.py         QC: specs, first frame, contact sheets
├── works/                 finished videos, one folder per video: <code>_<name>/
│   ├── kp01_compound-interest/
│   └── kp03_two-bedroom-floorplan/
├── assets/                intermediates: voice clips, frames, keyframes (gitignored)
└── engines/               local AI engine + models, ≈ 20 GB (gitignored, download separately)
```

Episode codes: `kp` code explainers (2D, 3D, Blender) · `ep` quote videos, Aju skits and fables · `kid` children's cartoon MVs · `zy` "Top Thinking" (Shuai & Mei) · `xs` realistic subtle motion. Script slugs in the repo: `kp02_sunk-cost` (script only), `ep01`, `ep04`–`ep06` (Aju the cat), `kid01` (emma), `zy01` (Shuai & Mei).

## Skills

The skills in `.claude/skills/` load automatically in Claude Code when you work in this repo.

| Skill | What it makes | Route | Say something like |
|---|---|---|---|
| `video-idea` | **Front door**: classifies any idea or screenshot, estimates quality honestly, writes a plan, calls the right skill | — | "I have an idea…", "Can you make a video like this?" |
| `video-explainer` | Code-animated explainers: curves, numbers, formulas, Three.js 3D | A | "Make an explainer about the rule of 72" |
| `video-floorplan` | Floor plan → CAD → 3D → sun study → phone tour | A | "Turn this floor plan into an animation" |
| `video-lineart` | Quiet black-and-white line-art 3D stories (plotome style) | A | "Explain sunk cost with a line-art animation" |
| `video-quote` | Motivational quote + AI animal footage | B | "Make a quote video with an eagle" |
| `video-skit` | 10–15 s comedy skits with a twist (Aju the office cat) | B | "Make Aju episode 3" |
| `video-char-mv` | A photo turned into a 3D cartoon character, then a heart-warming MV | B | "Turn this photo into a cartoon MV" |
| `video-talk` | "Top Thinking": Shuai & Mei explain a mental model in under a minute | B | "Next Top Thinking episode: inversion" |

## Workflow rules

Every pipeline follows the same loop, and Claude is instructed to stick to it:

1. **Plan**: copy, shot list, style, duration and compliance notes go into `works/<code>_<name>/PLAN.md`, and you approve them.
2. **Preview**: keyframe stills for code routes, or a 5-second / first-3-shots preview for AI routes, and you approve them.
3. **Full render**: GPU jobs get a short test first, a cool-down between shots, and a heads-up before anything long.
4. **QC**: resolution, frame rate, loudness ≈ −16 LUFS, a non-empty first frame, a contact sheet checked frame by frame, and it must make sense with the sound off. Broken AI shots are re-rolled at most twice.
5. **Deliver**: `<code>.mp4`, `<code>_cover.jpg` and `<code>_post.txt`, then update the capability map whenever a new limit or pitfall is found.

## Responsible use

- **Label AI-generated content when you publish.** Tick the platform's "AI-generated" declaration (on Douyin this is required by China's AI-content labeling rules). Any video with an AI voice-over or AI footage counts.
- **Original content only**: no third-party IP (characters from films, games or anime), no real people's faces or voices, no brands or logos, no uniforms or law-enforcement imagery.
- Photos of real people (e.g. your child for `video-char-mv`) are used **only to design a cartoon character** and never appear in the video. Keep them out of the repo.
- When publishing, pick music from the platform's licensed library instead of baking copyrighted songs into the upload.

## License

- Code and docs: [MIT](LICENSE), © 2026 xdis.
- `tools/fonts/Inter-Bold.ttf`: Inter by Rasmus Andersson, under the SIL Open Font License 1.1 ([`tools/fonts/Inter-OFL.txt`](tools/fonts/Inter-OFL.txt)).
- The AI models (FLUX.2 klein, Wan2.2 / FastMetal-5B-QAD) are not included and are covered by their own licenses.
