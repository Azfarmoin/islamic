# Beginner setup, step by step (Windows, $0)

Time: about 60-90 minutes the first time. You do this once. Nothing here costs money. Never type a card number anywhere.
Words you will meet: **repo** = a project folder stored on GitHub. **Secret** = a password GitHub keeps hidden. **Workflow** = a robot job GitHub runs for you. **Terminal** = the black text window where you type commands.

## STAGE 0. Install 4 free tools on your PC
1. **Python**: go to python.org/downloads, download Python 3.12 or newer. Run the installer and TICK "Add python.exe to PATH" on the first screen, then Install Now.
2. **Git**: go to git-scm.com/download/win, install with all default options.
3. **VS Code** (a text editor, optional but easy): code.visualstudio.com.
4. **FFmpeg**: open the Start menu, type `PowerShell`, open it, and run: `winget install Gyan.FFmpeg` . Close and reopen PowerShell afterwards.
Check: in PowerShell run `python --version`, `git --version`, `ffmpeg -version`. Each must print a version. If one says "not recognized", reinstall that tool (for Python, make sure you ticked the PATH box) and open a NEW PowerShell.

## STAGE 1. Make a GitHub account and an empty repo
1. github.com > Sign up (free). Confirm your email.
2. Click the **+** (top right) > New repository. Name: `islamic-video-engine`. Choose **Public** (public = unlimited free robot minutes; private only gives 2000/month). Do NOT tick "Add a README". Click Create repository.
3. Keep that page open; you will need its address, like `https://github.com/YOURNAME/islamic-video-engine.git`.

## STAGE 2. Put the project on your PC and upload it
1. Unzip `islamic-video-engine-slim.zip` to `C:\ivs` so the folder `C:\ivs\islamic-video-engine` exists.
2. In PowerShell:
```
cd C:\ivs\islamic-video-engine
git init
git add .
git commit -m "first upload"
git branch -M main
git remote add origin https://github.com/YOURNAME/islamic-video-engine.git
git push -u origin main
```
(First time, Git may ask you to sign in to GitHub in a browser window: do it. If it complains "Please tell me who you are", run `git config --global user.name "Your Name"` and `git config --global user.email "you@example.com"`, then repeat the commit.)
3. Refresh the GitHub page: you should see the project files. The file `.env` is NOT uploaded on purpose.

## STAGE 3. Test it on your own PC first
1. In the same PowerShell:
```
pip install -r requirements.txt
python scripts/fetch_models.py
python -m ivs init
python -m ivs verify-data
python -m ivs audit
python -m ivs make
```
2. When `make` ends, open the folder `output` > the newest folder > `video.mp4`. WATCH IT. If it plays, the engine works. (The first `make` can take several minutes.)
3. If a command fails, copy the last 15 lines of red text; that is exactly what I need to fix it.

## STAGE 4. Allow GitHub's robot to work
On your repo page: Settings > Actions > General > scroll to **Workflow permissions** > choose **Read and write permissions** > tick **Allow GitHub Actions to create pull requests** > Save.
Then the **Actions** tab: if a green button says "I understand my workflows, go ahead and enable them", click it.

## STAGE 5. Connect YouTube (so it can upload)
Skip this stage if you only want videos to be made and reviewed. Do it when ready.
1. Go to console.cloud.google.com, sign in with the Google account that OWNS your YouTube channel.
2. Top bar > project drop-down > **New project** > name `ivs` > Create. Make sure `ivs` is selected.
3. Menu (three lines) > **APIs & Services** > **Library** > search `YouTube Data API v3` > open it > **Enable**.
4. APIs & Services > **OAuth consent screen** (or "Google Auth platform"): choose **External**, App name `ivs`, your email for support and developer contact, Save. Add your own Gmail under **Test users**.
5. On the same section, set publishing status to **In production** (Publish app). Google shows a warning for apps it has not reviewed; for your own personal use that is fine. If you stay in "Testing" the key stops working after 7 days.
6. APIs & Services > **Credentials** > Create credentials > **OAuth client ID** > Application type **Desktop app** > Create. A box shows a **Client ID** and **Client secret**: keep it open or download the JSON.
7. In your project folder, copy `.env.example` to a new file called `.env` (in PowerShell: `copy .env.example .env`), open it in VS Code, and fill the first two lines:
```
YOUTUBE_CLIENT_ID=paste-the-client-id
YOUTUBE_CLIENT_SECRET=paste-the-secret
```
8. Run `python -m ivs auth-youtube`. A browser opens: pick your channel's Google account > Continue (through the "not verified" warning: Advanced > go to ivs) > Allow. The terminal prints `YOUTUBE_REFRESH_TOKEN=....`. Copy everything after the `=`.
9. On GitHub: repo > Settings > Secrets and variables > Actions > **Secrets** tab > New repository secret. Create three, names EXACTLY:
   - `YOUTUBE_CLIENT_ID`
   - `YOUTUBE_CLIENT_SECRET`
   - `YOUTUBE_REFRESH_TOKEN`
10. **Variables** tab > New repository variable: `IVS_YT_PRIVACY` = `private`. (Videos upload as private so only you see them. Change to `unlisted` or `public` only after you trust the output.)
11. Important YouTube rule: a brand-new Google API project may have its uploads forced to PRIVATE until Google audits it. If your uploads stay private even when you ask for public, that is why; check YouTube's current API policy page.

## STAGE 6. Free Gemini key (optional, makes story drafts better)
1. aistudio.google.com/apikey > sign in > **Create API key**. No card is asked. Do not enable billing.
2. GitHub > Settings > Secrets and variables > Actions > Secrets > new secret `GEMINI_API_KEY` = the key.
Without it the drafting still works (it uses a local fallback).

## STAGE 7. Quran recitation permission (read carefully)
In `config.yaml` the setting `permission_verified` is `false`, so videos are text-only until you set it. Read the reuse and monetization terms of the recitation source named in `docs/LICENSES.md`. Only if the terms allow it, change it to `true` and write a note in `permission_note` saying what you checked and when. Then commit and push (`git add . && git commit -m "permission" && git push`). I cannot decide this for you.

## STAGE 8. First robot run
1. Repo > **Actions** tab > left list **daily-video** > **Run workflow** (green button) > Run workflow.
2. Click the new run to watch it. Takes about 10-15 minutes. Green tick = success, red cross = failure (click it, copy the last red lines, send them to me).
3. When done: scroll to **Artifacts** and download the video zip. Watch it.
4. A new Issue appears titled like "review" for each item waiting on you. Open it. If the video is good, write a comment exactly: `/approve 1` (use the item's number). To reject: `/skip 1`. Only you (the repo owner) can do this. With privacy `private` the upload goes to YouTube Studio as private; check it there.

## STAGE 9. Turn on the automatic schedule
Nothing to do: `daily-video` already runs every 2 hours and makes up to 5 videos a day (5 fits the free YouTube quota). To change the number: Settings > Secrets and variables > Actions > Variables > `IVS_VIDEOS_PER_DAY` (more than 6 needs Google's quota increase and `IVS_YT_QUOTA`).
Every Monday the `draft-scripts` robot proposes a story from `content/queue.yaml` as a Pull Request. Check every line against your sources, delete the line `needs_human_review: true` in the file, then Merge.

## Your daily routine (5 minutes)
Open the review issues, watch the videos, comment `/approve N` or `/skip N`. About once a month push any small change so GitHub does not pause the schedule after 60 inactive days.

## Quick fixes
- `python` not recognized: reinstall Python with the PATH box ticked.
- Workflow red on "Restore state" first time: normal if the `ivs-state` branch does not exist yet; re-run once.
- Uploads fail with "invalid_grant": refresh token expired. Publish the OAuth app (Stage 5, step 5) and repeat steps 8-9.
- No upload but video exists: a YouTube secret is missing or misspelled (names are case sensitive).
- Nothing was run against real GitHub/YouTube by me, so the first run may expose small problems. Send me the red log lines.
