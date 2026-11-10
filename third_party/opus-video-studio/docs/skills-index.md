# Skills index (all 8, with commands to reproduce each)

> Skills live in `.claude/skills/<name>/SKILL.md` in this repo; Claude Code picks them up automatically when you work here.
> How to use: tell Claude what you want to make, or send a screenshot. If you don't know which one fits, say "I have an idea…" and the front door `video-idea` takes over.
> Self-test: `zsh tools/smoke_test.sh` (about 2 minutes; ends with "ALL PASSED").

## Overview

| # | Skill | What it does | Say to Claude | Route | Verified sample | Time per episode | Quality |
|---|---|---|---|---|---|---|---|
| 0 | **`video-idea`** | **Front door**: works out what kind of idea it is and how well it can be done, writes the plan, then calls one of the skills below | "I have an idea…", "Can you make a video like this?" + screenshot | see `docs/capability-map.md` | — | — | — |
| 1 | `video-explainer` | Code-animated explainers: curves, numbers, formulas; Three.js 3D too | "Make an explainer animation about XX" | code 2D / 3D | kp01 compound interest | about 30 min | 90 %+ |
| 2 | `video-floorplan` | Floor-plan animation: plan → CAD → 3D → sun study → phone tour | "Turn this floor plan into an animation", "Make a three-bedroom layout video" | Three.js 3D | kp03 two-bedroom flat | about 1 h | 90 % |
| 3 | `video-lineart` | Black-and-white line-art 3D stories (plotome style) | "Explain XX with a line-art animation" | Blender | kp02 sunk cost (script) | about 1 h | 80 % |
| 4 | `video-quote` | Quote + epic animal footage | "Make a quote video with an eagle" | local AI, realistic | ep01 | about 25 min | 60 % |
| 5 | `video-skit` | Aju comedy skits with a twist | "Make Aju episode 3" | local AI, realistic | ep04, ep05 | about 12 min | 60 % |
| 6 | `video-char-mv` | Photo → 3D cartoon character → heart-warming MV | "Make emma episode 2, winter" | local AI cartoon + first/last frame | kid01 emma's autumn | about 45 min | 70–80 % |
| 7 | `video-talk` | Shuai & Mei explain a mental model in Q&A form | "Next Top Thinking episode: XX" | local AI two-person cartoon | zy01 (first 3 shots only, paused) | about 30–60 min | 70 % |

## Commands to reproduce each skill

Run everything from the repo root. Replace NN with a new number (run `ls works scripts` to find the next unused one). `python` for skills 6–7 means a Python 3.11+ environment with numpy / opencv / pillow.

### 1. video-explainer (code-animated explainers)
```bash
cp scripts/kp01.json scripts/kpNN.json                                        # edit name / html / lines
cp tools/code_anim/kp01_compound.html tools/code_anim/kpNN_<name>.html        # 2D; for 3D start from three_template.html
python3 tools/code_anim/render.py scripts/kpNN.json --stills 0,5,12,20         # self-check stills
caffeinate -i python3 tools/code_anim/render.py scripts/kpNN.json              # full video → works/<name>/kpNN.mp4
python3 tools/code_anim/sfx.py scripts/kpNN.json                               # optional: adds sound effects if the JSON has sfx
```
Details: `works/kp01_compound-interest/REPRODUCE.md`

### 2. video-floorplan (floor-plan animation)
```bash
cp scripts/kp03.json scripts/kpNN.json
cp tools/code_anim/kp03_house.html tools/code_anim/kpNN_<name>.html   # edit WALLS / LAB / furniture / ROOMCAM / phone list
python3 tools/code_anim/render.py scripts/kpNN.json --stills <one time per stage>
caffeinate -i python3 tools/code_anim/render.py scripts/kpNN.json     # ≈ 70 s of video takes about 9–10 minutes
python3 tools/code_anim/sfx.py scripts/kpNN.json                      # delete _no_sfx.mp4 before re-rendering
```
Details: `works/kp03_two-bedroom-floorplan/REPRODUCE.md`

### 3. video-lineart (Blender line art)
```bash
cp scripts/kp02.json scripts/kpNN.json
cp tools/blender_line/kp02_scene.py tools/blender_line/kpNN_scene.py     # make.py looks for <code>_scene.py
python3 tools/blender_line/make.py scripts/kpNN.json --stills 50,200,400  # frame number = seconds × 30
caffeinate -i python3 tools/blender_line/make.py scripts/kpNN.json --preview 10
caffeinate -i python3 tools/blender_line/make.py scripts/kpNN.json        # full video
```

### 4. video-quote / 5. video-skit (vertical AI-footage pipeline)
```bash
.venv/bin/python make_video.py scripts/epNN.json --provider local-video
.venv/bin/python check_video.py scripts/epNN.json
```
Aju's character card: `characters/aju-cat.md`

### 6. video-char-mv (photo-character MV)
```bash
python tools/make_char_mv.py scripts/kidNN.json --only 1    # one shot first
python tools/make_char_mv.py scripts/kidNN.json             # everything (resumable)
python tools/make_char_mv.py scripts/kidNN.json --compose   # after changing only subtitles or music
```
Sample: `scripts/kid01.json`; character images go in `characters/<name>/` (personal photos stay local)

### 7. video-talk (Shuai & Mei)
```bash
python tools/make_talk_mv.py scripts/zyNN.json --preview 3
python tools/make_talk_mv.py scripts/zyNN.json
```
Character card: `characters/xiaoshuai-xiaomei.md`; write the plan first at `works/zyNN_top-thinking_<model>/PLAN.md`

## Shared rules (every skill follows them)

1. **Plan → user approves → preview (stills or 5 s) → user approves → full video → QC → delivery**
2. Deliver to `works/<code>_<name>/`: `<code>.mp4`, `_cover.jpg`, `_post.txt` (one version each for Douyin and Xiaohongshu); a new route also gets a `REPRODUCE.md`; finally update the works list in `README.md`
3. QC: specs, loudness about −16 LUFS, frame 1 must not be empty, a frame from every stage, and it must make sense with the sound off
4. For local GPU jobs, run a short test first, cool down between shots, ask the user before long jobs
5. Tick the AI label when publishing; no third-party IP, no real people
6. Built something new or hit a new pitfall: update `docs/capability-map.md` and the relevant SKILL.md

## Environment (to restore on a new machine)

| Component | Location / install |
|---|---|
| System `python3` | For code animation: `pip install playwright numpy`; drives the locally installed Google Chrome (`channel='chrome'`) |
| edge-tts | On PATH or in `.venv/`: `python3 -m venv .venv && .venv/bin/pip install edge-tts` (needs internet). `.venv/bin/python` also runs `make_video.py` / `check_video.py` |
| Python 3.11+ env with numpy / opencv / pillow | Runs the char-mv / talk pipelines |
| `engines/FastVideo/.venv` + `engines/models/FastMetal-5B-QAD` | Wan2.2 5B image-to-video (about 20 GB, not in the repo; download separately) |
| Draw Things + `draw-things-cli` | `brew install draw-things-cli`; the FLUX.2 klein 4B model lives in `~/Library/Containers/com.liuliu.draw-things/Data/Documents/Models/` |
| Blender 5.x | `brew install --cask blender` |
| ffmpeg (with libass and drawtext) | `brew install ffmpeg` |
| Fonts | `tools/fonts/Inter-Bold.ttf` (OFL, Latin only); set `STUDIO_FONT` to a CJK font for Chinese text |
| Three.js | Loaded in the page through an importmap from jsdelivr, `three@0.160.0` (needs internet) |

## Related docs

- `docs/capability-map.md`: which route each kind of idea takes, measured limits, known pitfalls
- `docs/viral-code-video-notes.md`: lessons from viral code-made videos, plus proposed skills (exploded views, zooms, QC, beat-syncing)
- `docs/pipelines.md`: tool list, how each step is done and why
- `README.md`: folder layout, works list
