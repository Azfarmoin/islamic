# Bang Motion (github.com/bangtutorial/bang-motion, MIT)

Bang Motion is an **agent skill**: an AI coding agent writes a single `index.html` motion graphic (GSAP timeline, `window.OPENER`) from your brief. Running the agent costs LLM tokens, so it is **not** part of the free automated pipeline. What is free, and added:

| Command | What it does | Cost |
|---|---|---|
| `python -m ivs kinetic quran:114:1-4 --out k.mp4` (or `story:iqra`) | Agent-free kinetic-typography short (1080x1920) from our **verified** text: Arabic with tashkeel (whole-line reveal, never split into letters), English, Urdu, reference, drifting geometric stars, progress bar. Template: `js/kinetic/index.html` | $0 |
| `python -m ivs bang-render page.html --out film.mp4` | Renders any Bang-Motion-style page to MP4 frame by frame in headless Chromium (replaces its puppeteer export; GSAP CDN served locally so it works offline) | $0 |
| `python -m ivs lemo-brief story:iqra --tool bang` | Brief with verified text + religious rules to paste into the Bang Motion skill on your PC | your agent tokens |

The skill itself (MIT) is vendored in `third_party/bang-motion/` (SKILL.md, references, starter pages, scripts) for manual use: `/plugin marketplace add bangtutorial/bang-motion`.

## Honest limits
- `kinetic` output is **silent** and not yet wired into the daily pipeline (it would need the recitation/narration audio muxed and timed to the animation). Use it as a standalone short or B-roll.
- Timing is by reading-speed estimate (`line_seconds`), not synced to a recitation.
- Bang Motion's own pages load fonts from Google Fonts and may assume 16:9; `bang-render` blocks Google Fonts (falls back to local fonts) and defaults to 9:16.
- The vendored docs are in Indonesian. I did not run the agent skill.
- A kinetic video of a story still needs the human review gate before posting.
