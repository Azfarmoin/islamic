# FULL SETUP - every feature, from zero

## EASIEST WAY: one guided script
Unzip, open a terminal in the folder, run `python easy_setup.py` (Windows: double-click `setup.bat`; Mac/Linux: `./setup.sh`). Choose 4 (everything). It checks your tools, installs packages, downloads the voice model, makes a test video, logs in to YouTube, creates the GitHub repo, uploads secrets, sets permissions and starts the first run. Secrets are typed hidden and kept only in `.env` (git-ignored) and GitHub secrets. You still must do by hand: install Python/FFmpeg/Git, install the GitHub CLI (`gh auth login`), and create the Google OAuth Desktop client (`docs/YOUTUBE_SETUP.md`). The manual steps below are the same thing spelled out.

Costs $0 if you stay on free tiers. Items marked (optional) never block the core pipeline; each falls back automatically.

## Part A - Run it on your PC first (30 min)
1. Install Python 3.11+, FFmpeg (`ffmpeg -version` must work) and Git. Node 22+ is optional (Part D).
2. `cd islamic-video-engine && python -m venv .venv`, activate it, `pip install -r requirements.txt`.
3. English voice model (~120 MB, once): `python scripts/fetch_models.py`.
4. Initialise and verify the Quran data: `python -m ivs init` then `python -m ivs verify-data`.
5. Health check: `python -m ivs validate` and `python -m ivs dry-run`, then `python -m ivs make` (makes one video in `output/`). Watch it before anything goes online.
6. Recitation needs internet access to everyayah.com. Read `docs/LICENSES.md` first; `permission_verified: true` in `config.yaml` is your declaration that you checked the terms. If unsure, set it to false (videos become text-only).

## Part B - GitHub (automation, 15 min)
1. New PUBLIC repo (unlimited free minutes; private = 2,000 min/month). Push the project.
2. Settings > Actions > General > Workflow permissions: Read and write, tick "Allow GitHub Actions to create pull requests".
3. Settings > Secrets and variables > Actions. Add what you need below.

## Part C - YouTube upload
1. console.cloud.google.com > new project > enable "YouTube Data API v3".
2. OAuth consent screen: External, add yourself as test user, then PUBLISH to Production (otherwise the token expires in 7 days).
3. Credentials > OAuth client ID > type Desktop app.
4. On your PC: `python -m ivs auth-youtube` (follow the browser prompt).
5. Secrets: `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REFRESH_TOKEN`.
6. Variables: `IVS_YT_PRIVACY=private` (switch to unlisted, then public, once you trust it), `IVS_VIDEOS_PER_DAY=5`.
7. Quota: free = 10,000 units/day, ~1,650 per upload, so about 6 uploads/day. Do not raise `IVS_YT_QUOTA` until Google approves an extension.
8. First run: Actions > daily-video > Run workflow. Check the log, the review issue and the `ivs-state` branch.
9. Daily routine: comment `/approve N` or `/skip N` on the review issue (owner only). Stories, hadith and AI drafts always wait for you.

## Part D - Optional features
| Feature | How to enable | If skipped |
|---|---|---|
| AI script drafting | One secret: `GEMINI_API_KEY` (free, aistudio.google.com/apikey, billing OFF), or `GROQ_API_KEY`, `OPENROUTER_API_KEY`, `MISTRAL_API_KEY`, or generic `AI_API_KEY`+`AI_BASE_URL`+`AI_MODEL`. Force with variable `IVS_LLM`. See `docs/ANY_AI_KEY.md` | Local Ollama, then built-in fallback script |
| Story videos | Add sourced entries to `content/queue.yaml` or `content/stories/`; verify every line; delete `draft.needs_human_review`; merge | Only Quran/hadith videos |
| Real sound effects | On by default (`audio.sfx.openverse`), CC0/CC BY/PDM, credits in description | Synthetic effects |
| Better English voice | `edge-tts` is in requirements; `allow_edge: true` in config (online, unofficial, English story narration only) | Kokoro |
| Neural voices (Chatterbox, Qwen3-TTS, Fish Speech) | GPU machine: `pip install chatterbox-tts` and/or `pip install qwen-tts`; Fish: self-host and `export FISH_SPEECH_URL=...`. See `docs/TTS_ENGINES.md` | Kokoro. Not for CI (no GPU) |
| JS effects and transitions | Node 22+, `cd js && npm ci`, `npx playwright install --with-deps chromium`; or `IVS_CHROME=/path/to/chrome` | Pillow/FFmpeg effects |
| Real 3D (low-poly) | Blender's Python module (`bpy`, needs a compatible Python), then `python -m ivs test-3d`, `python -m ivs film <story>`; `IVS_LOWPOLY=0` for smooth | 2.5D parallax scenery (default). 3D is key shots only; full film takes hours on CPU |
| Documentary files | Automatic per video: VIDEO_DIRECTOR.json, 12 production JSONs, EXPLANATION_PLAN.json, PRODUCTION_CHECKLIST.json, production_report.md | - |
| Dashboard | `python -m ivs dashboard --port 8000` | - |
| Cleanup | `python -m ivs cleanup --days 14 --apply` | - |

## Part E - Things to know
- Push a commit at least every 60 days or GitHub disables scheduled workflows.
- 5+ near-identical Shorts a day can look like spam; vary topics and keep privacy private until reviewed.
- Have a qualified person review Arabic/Urdu editorial lines before going public.
- Never put keys in `config.yaml` or commits; secrets only.
- Untested live in the build sandbox: EveryAyah download, Gemini and other AI keys, Openverse, Edge, neural TTS, YouTube upload. Expect to fix small things on your first real run.

## Troubleshooting
`python -m ivs status` (queue/state), `validate` (config, workflows, secrets presence), `audit`, Actions logs, `docs/LIMITATIONS.md`.
