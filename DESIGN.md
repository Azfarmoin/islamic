# DESIGN.md — visual, motion and sound system

Single reference for how every video should look and sound. Code lives in `ivs/visuals.py`, `ivs/anim.py`, `ivs/scenery.py`, `ivs/direction.py`, `ivs/studio.py`.

## Principles
1. Reverence first: no faces; never depict Allah, prophets, sahaba or angels. Figures are faceless silhouettes.
2. Quran text is shown exactly as verified, in Amiri, large, high contrast, never covered by effects.
3. Calm pacing. Effects serve meaning; nothing flashes. Silence before reveals.
4. Every video is visualised (scenery + motion), 3–4 scenery changes per ~60 s.
5. Consecutive videos must differ in camera, palette and scenery.

## Palette (`visuals.PALETTES`, `direction.PALETTES`)
Deep night blue / indigo base, warm gold accent (`gold`), cream ink for text. Character robes: sand_brown, indigo and siblings; one per story.

## Typography (`assets/fonts`, all OFL)
| Role | Font | Notes |
|---|---|---|
| Arabic | Amiri Regular/Bold | 124 px, raqm shaping |
| Urdu | Noto Nastaliq Urdu | 68 px, text only (no Urdu speech) |
| English | Noto Sans | 60 px |
Captions sit at the top on narration scenes (`caption_top`) so the scene stays visible.

## Scenery (`anim.SCENES`)
desert_night, desert_dawn, sea_calm, sea_storm, night_sea, mountain_dawn, sky_stars, geometric_night, geometric_dawn. Chosen by `scenery.pick/sequence` from story text; transitions at each change.

## Motion
Layered parallax (2.5D) for every video; real Blender 3D key shots via `ivs film <story>` / `ivs test-3d` (CPU: ~10.5 s/frame HD). Slow camera moves, ease-in/out, transitions via GL-Transitions when Chromium is available.

## VFX
Dust, stars, mist, light rays, vignette, soft grain, particle drift (PixiJS/p5 when Chromium present, otherwise Pillow/FFmpeg fallbacks).

## Sound
Real CC0/CC BY/PDM effects from Openverse (credited), synthetic fallback. Ambient bed under narration only. No music or synthetic voice over Quran recitation. Narration: Chatterbox / Qwen3-TTS / Fish Speech (if installed) -> Kokoro (en) fallback.

## Per-video data files
`VIDEO_DIRECTOR.json`, the 12 production JSON files, `production_report.md`, frame records, film plan: written for every video (see `docs/DOCUMENTARY.md`).
