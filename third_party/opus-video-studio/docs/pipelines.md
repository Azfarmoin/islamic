# Pipelines, tools and lessons learned

> To make a video, just tell Claude in one sentence or send a screenshot; the matching skill below is picked automatically.
>
> **Standard method for story animation: local 5B first/last-frame.** Every shot has a fixed first frame and a fixed last frame; the model only fills in the motion between them. Always make a 5-second preview first and render the full video only after approval.

---

## 1. All skills (if unsure, use `video-idea`; capabilities and limits are in `docs/capability-map.md`)

| What you want | Say to Claude | Skill | Output | Time |
|---|---|---|---|---|
| Motivational quote + epic animal footage | "Make a quote video with an eagle", or send a screenshot | `video-quote` | vertical 1080×1920, ≈ 25 s | about 25 min |
| Original comedy skit with a twist (Aju at Work) | "Make Aju episode 3", "Make something funny" | `video-skit` | vertical, 60 fps, ≈ 10 s | about 12 min |
| **Cartoon character from a photo + heart-warming MV** (emma) | "Turn this photo into a cartoon video", "Make emma episode 2" | `video-char-mv` | vertical 720×1280, 60 fps, ≈ 14 s, with a song + bold subtitles | about 4 min per shot; about 45 min for 11 shots |
| Shuai & Mei Q&A about a mental model | "Next Top Thinking episode: XX" | `video-talk` | vertical 3D cartoon, 60 fps, under 1 min | about 30–60 min |
| **Any new idea, or "can you make this?" (front door)** | "I have an idea…", "Is this effect possible?" | `video-idea` | checks `docs/capability-map.md`, picks a route, writes the plan | — |
| Code-animated explainer (2D curves and numbers, or Three.js 3D) | "Make an explainer animation about XX" | `video-explainer` | vertical 1080×1920, 60 fps | about 30 min (kp01) |
| Floor-plan animation | "Turn this floor plan into an animation" | `video-floorplan` | vertical 1080×1920, 60 fps | about 1 h (kp03) |
| Blender black-and-white line-art story (plotome style) | "Explain XX with a line-art animation" | `video-lineart` | vertical 1080×1920, 30 fps | about 1 h, render about 9 min (kp02) |

Skill files: `.claude/skills/<name>/SKILL.md`.

## 2. Tools

| File | Purpose |
|---|---|
| `make_video.py` | Vertical pipeline: voice-over (edge-tts, emotion tuned per line) → local footage → compositing (title, subtitles, captions, follow prompt). `style: skit` turns on smooth mode: frame-accurate generation, de-flicker, interpolation to 60 fps |
| `make_fable.py` | Horizontal fable pipeline: several characters taking turns in one shot, subtitles switching line by line, darkening on a comeback line (`darken`), footage reuse (`same_as`), action-only shots |
| `check_video.py` | QC: resolution, frame rate, audio track, duration, first frame not black; writes a per-shot contact sheet and a layout check image |
| `tools/code_anim/render.py` | **Code-animation pipeline**: voice-over → timeline → Chrome renders the HTML (Canvas or Three.js) frame by frame → compositing. Uses the system `python3` |
| `tools/code_anim/sfx.py` | Code-synthesised sound effects (pop / tick / tap / whoosh / rise / thud / chime) placed on timeline events |
| `tools/blender_line/make.py` + `kpNN_scene.py` | **Blender line-art pipeline**: voice-over → Blender render (Freestyle white lines) → ASS subtitles + ambience → compositing |
| `tools/mlx_wan22_i2v.py` | **Local 5B image-to-video / first-last-frame** (our patch on top of FastMetal): `--image` locks the first frame, `--last-image` locks the last frame by setting the timestep of the corresponding tokens to 0 |
| `tools/make_char_mv.py` | **Photo-character MV end to end**: one JSON (character, per-shot first/last frames, subtitles, music) → FLUX keyframes → 5B first/last-frame → two-pass grading → 60 fps → subtitles and music → automatic QC |
| `tools/make_talk_mv.py` | **Two-character dialogue pipeline** (Shuai & Mei): per-speaker voices → keyframes → 5B → grading → speaker-coloured subtitles |
| `tools/color_match.py` | Pulls a video's colours back to a reference image (RGB mean and variance) |
| `tools/clean_keyframe.py` | Inpaints watermarks (top-left, bottom-right) and burned-in subtitles out of a keyframe |
| `tools/fonts/Inter-Bold.ttf` | Default bold font (OFL, Latin only); override with `STUDIO_FONT` for CJK text |
| `engines/FastVideo` + `engines/models/FastMetal-5B-QAD` | Local Wan2.2 5B (MLX, 3-step distilled). Not in the repo |
| `draw-things-cli` (Homebrew) | Command-line Draw Things. Models live in `~/Library/Containers/com.liuliu.draw-things/Data/Documents/Models` |
| `characters/aju-cat.md` | Aju's character card: prompt lock blocks, topic bank, safety checklist |
| `characters/xiaoshuai-xiaomei.md` | Shuai & Mei's character card |

## 3. How each step is done, and why (lessons learned)

**Pictures**
- Local 5B text-to-video: fine for one character doing a simple action; **two animals in physical contact fuse together** (tested: a leopard pulling a wolf became one blob). Faces of humans in period costume aren't consistent across shots. Cats and cartoon animals work best.
- The first frame decides everything: the established approach is "**keyframe first, then image-to-video**". Local 5B image-to-video works: the first frame matches exactly and the following motion is about 60–70 % right.
- The model over-saturates colours: pull them back with `color_match.py` after image-to-video.
- One animal species per shot (realistic style); in cartoon style write `Two separate animals`.
- Don't write `cinematic lighting` or `glowing` in prompts — the picture turns purple and looks like CG.

**Smoothness**
- No frame interpolation at generation time: every frame is really generated. The old `--fast` interpolation produced a jelly effect.
- Frame rate: the model's native 24 fps (5B). **Don't force-convert to 30 fps** — that repeats 1 frame in every 4 and looks juddery. After de-flicker, use motion interpolation to reach 60 fps.
- The title stays fixed for the whole video; only the picture area gets a 0.2 s fade-in (previously the title flashed on every cut).
- The first frame must not be black, or previews in chat apps, photo galleries and Douyin show an empty box.

**Sound**
- Tune rate and pitch per line: tired → excited → deflated. A flat read sounds stiff.
- Avoid words the voice mispronounces (for Chinese voices, polyphonic characters; for English voices, ambiguous numbers and abbreviations) — reword around them.
- Normalise loudness to −16 LUFS; trim leading/trailing silence; use "…" to create pauses.
- Pick background music from the platform's library (original audio 100, music 15–30).

**Preview and delivery**
- The built-in previews in VS Code and Cursor don't support H.264 and show black — the file is fine. Use QuickTime or Finder Quick Look: `open -a "QuickTime Player" works/<code>_<name>/<code>.mp4`.
- `works/<code>_<name>/` holds only the final video, cover and post copy. Tests go in `assets/test/`.
- Write the post copy in the order of the fields on Douyin's publish page: title, description (with an engagement question), cover, self-declaration, music, collection.

**Compliance**
- No "AI" text on the picture (the user's preference), but **always tick "Content is AI-generated" when publishing**; Douyin then adds its own label.
- No IP from novels, films or games, no real people, no uniforms or law-enforcement figures; nothing vulgar, and no dangerous or imitable behaviour (e.g. a gas cylinder); for story videos, say "The story is fictional" in the description.

**The machine**
- Cool down for 60 s between shots; run `caffeinate` during generation to prevent sleep, **don't close the lid**, stay on mains power, quit Chrome.

## 4. Generation routes compared (tests plus research)

| Route | Similarity / quality | Speed | Cost | Status |
|---|---|---|---|---|
| Local 5B text-to-video | Interactions fuse; matching a reference about 40–50 % | about 3 min per 3 s | free | ✅ used for the Aju series |
| Local 5B, first frame only + colour correction | First frame identical, ending doesn't match, interactions turn into a blob | about 3 min per 3 s | free | ❌ superseded by first/last-frame |
| **Local 5B first/last-frame + colour correction (standard)** | **about 80 % match** on a test sequence (simple dialogue shots 90 %, physical interaction 60–80 %) | **about 2 min per shot** | free | ✅ **the standard method for all story animation** |
| Draw Things Wan2.2 I2V 14B | Blurry output when the acceleration LoRA didn't take effect | about 9 min per 2 s measured | free | ❌ dropped: the LoRA must be converted inside the app, too slow |
| Jimeng Seedance 2.0 (app or official API) | about 80–90 %, multi-shot, native lip-sync | fast | daily free credits; API about ¥1 per second | needs the user's own account |
| LTX-2.3 (available in draw-things-cli) | Can drive lip-sync from audio (untested) | untested | free | fallback |

## 5. Existing works and scripts

| File | Content | Status |
|---|---|---|
| `works/kp01_compound-interest/` | Code-animated explainer: compound interest, English re-render | sample, tracked in the repo |
| `works/kp03_two-bedroom-floorplan/` | Three.js floor-plan animation of an 89 m² two-bedroom flat, English re-render | sample, tracked in the repo |
| `scripts/kp02.json` | Blender line art: sunk cost (a cinema story) | script only |
| `scripts/ep01.json` | Quote + tiger and wolf pack | script (video not in the repo) |
| `scripts/ep04.json`, `scripts/ep05.json` | Aju at Work, episodes 1 and 2 (The Raise, The Review) | scripts (videos not in the repo) |
| `scripts/ep06.json` | Original animal fable, episode 1 (4 short fables) | script; only shots 1–2 were generated |
| `scripts/kid01.json` | emma's autumn, photo-character MV | script (character images are personal and not in the repo) |
| `scripts/zy01.json` | Top Thinking episode 1: iterative thinking | paused; only a 3-shot preview was made |

## 6. Suggested next steps

1. Make an original fable with the first/last-frame method: FLUX keyframes via `draw-things-cli`, 5B first/last-frame video, then `make_fable.py` for compositing, until there is a publishable version (move `ep06` onto this flow).
2. Make the first Three.js structural explainer (e.g. a 3D heart or engine) with `video-explainer`.
3. Render the full kp02 line-art video.
