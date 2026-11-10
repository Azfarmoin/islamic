# Opus Video Studio: instructions for Claude

The user will describe a video idea at any time, or send a screenshot of someone else's video, and expect you to **actually make it**.

- **Read `docs/capability-map.md` first**, pick a route, and say honestly how close you can get.
- If it isn't clear which series an idea belongs to, use the `video-idea` skill (the front door).
- Folder rules and the works list are in `README.md`; **commands to reproduce every skill are in `docs/skills-index.md`**; tool notes are in `docs/pipelines.md`.
- If anything about the environment is in doubt, run `zsh tools/smoke_test.sh` first (about 2 minutes).
- Skills live in `.claude/skills/<name>/SKILL.md` in this repo.

## Series and skills

| Series | Code | Skill |
|---|---|---|
| Code-animated explainers (2D Canvas, Three.js 3D) | kp | `video-explainer` |
| Floor-plan animation (plan → CAD → 3D → sun study → phone tour) | kp | `video-floorplan` |
| Blender line-art stories | kp | `video-lineart` |
| Quote + epic animal footage | ep | `video-quote` |
| Aju comedy skits | ep | `video-skit` |
| Heart-warming photo-character MV (emma) | kid | `video-char-mv` |
| Shuai & Mei "Top Thinking" | zy | `video-talk` |
| Realistic subtle motion, other new ideas | xs / new code | `video-idea` |

## Always

1. Plan document → user approves → preview (stills or 5 s) → user approves → full video → QC → delivery.
2. Finished videos go in `works/<code>_<name>/` with `<code>.mp4`, `<code>_cover.jpg` and `<code>_post.txt` (one version each for Douyin and Xiaohongshu). Intermediates go in `assets/<code>/` (gitignored).
3. The standard method for story animation is local 5B first/last-frame. For local GPU jobs, run a short test first, ask the user before long jobs, and cool down between shots.
4. Python environments: system `python3` with playwright + numpy for code animation (needs Google Chrome); `.venv/bin/python` (or PATH) for edge-tts and the older `make_video.py` pipeline; a Python 3.11+ env with numpy / opencv / pillow for `make_char_mv.py` and `make_talk_mv.py`; `engines/FastVideo/.venv/bin/python` for the 5B model.
5. Default font is `tools/fonts/Inter-Bold.ttf` (Latin only); set `STUDIO_FONT` to a CJK font when on-screen text is Chinese.
6. Tick the AI label when publishing; no "AI" text on the picture; no third-party IP, no real people.
7. When you build something new or hit a new pitfall, update `docs/capability-map.md`, `README.md` and the relevant skill.
