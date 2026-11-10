# Setup from zero ($0, ~30-40 min, once)

1. **GitHub**: create a PUBLIC repo, push the project, then Settings > Actions > General > Workflow permissions = read and write + "Allow GitHub Actions to create pull requests".
2. **YouTube**: Google Cloud project > enable YouTube Data API v3 > OAuth consent screen (External, add yourself, PUBLISH to Production, else the token dies in 7 days) > OAuth client ID type Desktop app. On your PC run `pip install -r requirements.txt && python -m ivs auth-youtube`. Add secrets `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REFRESH_TOKEN`; add variable `IVS_YT_PRIVACY=private` (switch to unlisted/public later).
3. **Gemini (optional, free)**: https://aistudio.google.com/apikey, billing OFF. Secret `GEMINI_API_KEY`; optional variable `GEMINI_MODEL`.
4. **Volume**: `IVS_VIDEOS_PER_DAY` (default 5, fits the free quota) but the free YouTube quota allows ~6 uploads/day. Set `IVS_YT_QUOTA` only AFTER Google approves a quota extension.
5. **First run**: Actions tab > daily-video > Run workflow. Check the log, the review issue, the `ivs-state` branch, and watch the video artifact before approving.
6. **Daily**: comment `/approve N` or `/skip N` on the review issue (owner only). Stories/hadith/AI drafts always wait for you. For story drafts: add entries to `content/queue.yaml` with sourced notes; Monday PR; verify every line; delete `draft.needs_human_review`; merge.
7. **Watch out**: recitation-permission flag; push something every <60 days or schedules get disabled; 10 near-identical Shorts/day can look like spam; have a qualified person review Arabic/Urdu editorial lines before going public.

Troubleshooting: auth error = token expired (publish the OAuth app, redo auth); nothing uploads = a YouTube secret is missing; "queue empty" = add queue entries (Quran-walk continues); quota error = lower IVS_VIDEOS_PER_DAY.
See also GITHUB_ACTIONS.md, YOUTUBE_SETUP.md, GEMINI_AND_SFX.md.
