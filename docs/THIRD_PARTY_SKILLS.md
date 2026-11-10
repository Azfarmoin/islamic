# Added third-party skills (all MIT, vendored as text for manual use)

All three are **agent skills**: an AI coding agent follows them to write the video code. Running the agent costs LLM tokens, so none of them runs in the free GitHub Actions pipeline. What is free: the vendored docs, the briefs, and `python -m ivs bang-render`, which renders their pages.

| Skill | Repo | Vendored in | What we use | Watch out |
|---|---|---|---|---|
| Claude Animated Shorts | mromidev/claude-animated-shorts | `third_party/claude-animated-shorts/` (SKILL.md, README, STYLE_BIBLE, 7 reports; not the 18 MB of reference frames, which are "for style study only") | world, camera, lighting and grade ideas | Its characters are cartoon cards **with faces** and it renders with Remotion (check Remotion's licence yourself; free use is limited to individuals/small teams as far as I know). Under our rules only faceless silhouettes are allowed. |
| Every Frame Is Code / motion-kit | kiselas/every-frame-is-code | `third_party/motion-kit/` (rules 00-17, SKILL.md, runtime JS) | "a frame is a pure function of time" pages, effects cookbook, kinetic type, transitions | Page contract `window.__meta`, `window.__draw(t)`, `window.__ready`; `bang-render` supports it. Some examples load libraries from a CDN. |
| Opus Video Studio | xdis/opus-video-studio | `third_party/opus-video-studio/` (README, CLAUDE.md, docs) | Route A only (code-drawn Canvas/Three.js/Blender) | Route B needs an Apple-silicon Mac + ~20 GB models, Route C paid APIs: not used. Its voice step uses edge-tts (online): never for Quran. |

I picked these repos from your names; there are other projects with similar names (for example opus-pro/opus-video-studio is OpusClip's paid-credit plugin, which I did NOT add). Tell me if you meant a different one.

## Use
- `python -m ivs lemo-brief story:iqra --tool motion-kit|animated-shorts|opus-studio --out brief.md` writes the verified text + religious rules + the right install/usage note.
- `python -m ivs bang-render page.html --out film.mp4` renders pages that expose either contract (`window.OPENER` or `window.__draw`), free and offline (GSAP CDN served locally).

## Your 3D production spec (A-O)
Added as the **Production Bible** section of every story's `director_package.md` (and `director_package.json`): scene breakdown, world map, character roster, appearance sheet, animation needs, props, environment assets, reusable asset library, scene-to-asset dependency map, lighting, camera, interaction, VFX and optimisation plans, with every row tagged A (explicit) / B (inferred) / C (artistic).

Two parts of that spec are deliberately **not** done:
- Faces, hair and facial expressions: our rule is faceless figures only, and no depiction of Allah, prophets or sahaba.
- "Implement every scene": the 3D engine builds desert, mountain, sea, night and sky scenes with faceless walkers, spearmen, camels, elephants, ships and birds. Interiors (mosque, rooms, doors, furniture), forests, rain, cities, large crowds and object interaction are **not built**. The bible lists these under "Not built yet" for each story instead of pretending.
