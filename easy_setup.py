#!/usr/bin/env python3
"""One-file guided setup. Run:  python easy_setup.py
Menu: 1) local setup  2) YouTube login  3) GitHub (repo + secrets + permissions)  4) everything.
Secrets are typed hidden, saved only to .env (git-ignored) and sent to GitHub through `gh` on stdin (never on a command line, never printed)."""
from __future__ import annotations
import getpass, os, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENV = ROOT / ".env"
PY = sys.executable

def say(m=""): print(m, flush=True)
def ok(m): say("  [ok]   " + m)
def bad(m): say("  [FIX]  " + m)
def ask(q, default=""):
    a = input(f"{q}{' [' + default + ']' if default else ''}: ").strip()
    return a or default
def yes(q, default=True):
    a = input(f"{q} [{'Y/n' if default else 'y/N'}]: ").strip().lower()
    return default if not a else a.startswith("y")

def run(cmd, **kw):
    return subprocess.run(cmd, cwd=ROOT, **kw)

def env_read() -> dict:
    d = {}
    if ENV.exists():
        for l in ENV.read_text().splitlines():
            if "=" in l and not l.strip().startswith("#"):
                k, v = l.split("=", 1); d[k.strip()] = v.strip()
    return d

def env_set(k: str, v: str):
    d = env_read(); d[k] = v
    ENV.write_text("".join(f"{a}={b}\n" for a, b in d.items())); 
    try: os.chmod(ENV, 0o600)
    except Exception: pass

def check_tools() -> bool:
    say("\nChecking your computer...")
    good = True
    if sys.version_info >= (3, 11): ok(f"Python {sys.version.split()[0]}")
    else: bad("Python 3.11+ needed: https://www.python.org/downloads/"); good = False
    if shutil.which("ffmpeg"): ok("FFmpeg")
    else: bad("FFmpeg missing. Windows: winget install ffmpeg | Mac: brew install ffmpeg | Linux: sudo apt install ffmpeg"); good = False
    if shutil.which("git"): ok("Git")
    else: bad("Git missing (needed only for GitHub): https://git-scm.com/downloads")
    ok("Node.js (optional effects)") if shutil.which("node") else say("  [skip] Node.js not found: optional JavaScript effects will be skipped")
    return good

def local_setup():
    if not check_tools(): say("\nInstall the missing items above, then run this again."); return False
    say("\n1/4 Installing Python packages...")
    if run([PY, "-m", "pip", "install", "-r", "requirements.txt"]).returncode: bad("pip install failed (read the message above)"); return False
    say("\n2/4 Downloading the free English voice model (~120 MB, once)...")
    if run([PY, "scripts/fetch_models.py"]).returncode: bad("model download failed; check your internet and re-run")
    say("\n3/4 Preparing the database and checking the Quran data...")
    for sub in (["init"], ["verify-data"], ["validate"]):
        if run([PY, "-m", "ivs", *sub]).returncode: bad(f"'ivs {sub[0]}' reported a problem (read above)")
    if yes("\n4/4 Make one test video now? (takes a few minutes; needs internet for recitation)", True):
        run([PY, "-m", "ivs", "make"]); say("Your video is in the 'output' folder. Watch it before anything goes online.")
    say("\nLocal setup done.")
    return True

def youtube_login():
    say("\nYouTube login. You need an OAuth 'Desktop app' client from Google Cloud (steps: docs/YOUTUBE_SETUP.md).")
    say("Tip: publish the consent screen to Production, otherwise the token dies after 7 days.")
    e = env_read()
    cid = ask("Client ID", e.get("YOUTUBE_CLIENT_ID", ""))
    sec = getpass.getpass("Client secret (hidden): ").strip() or e.get("YOUTUBE_CLIENT_SECRET", "")
    if not (cid and sec): bad("Both are required."); return False
    env_set("YOUTUBE_CLIENT_ID", cid); env_set("YOUTUBE_CLIENT_SECRET", sec)
    say("A browser window will open: sign in with the channel's Google account and allow access.")
    r = run([PY, "-m", "ivs", "auth-youtube"], capture_output=True, text=True)
    tok = next((l.split("=", 1)[1].strip() for l in r.stdout.splitlines() if l.startswith("YOUTUBE_REFRESH_TOKEN=")), "")
    if not tok: bad("Login failed:\n" + (r.stderr or r.stdout)[-400:]); return False
    env_set("YOUTUBE_REFRESH_TOKEN", tok); ok("Saved to .env (kept private, never uploaded to git)")
    return True

def gh_ok() -> bool:
    if not shutil.which("gh"):
        bad("GitHub CLI missing. Install from https://cli.github.com then run:  gh auth login   and re-run this."); return False
    if run(["gh", "auth", "status"], capture_output=True).returncode:
        say("You are not logged in to GitHub. Running 'gh auth login'..."); 
        if run(["gh", "auth", "login"]).returncode: return False
    return True

def gh_set(kind: str, name: str, value: str):
    cmd = ["gh", kind, "set", name] + ([] if kind == "secret" else ["--body", value])
    r = run(cmd, input=value if kind == "secret" else None, text=True, capture_output=True)
    (ok if r.returncode == 0 else bad)(f"{kind} {name}" + ("" if r.returncode == 0 else ": " + r.stderr.strip()[:150]))

def github_setup():
    if not (shutil.which("git") and gh_ok()): return False
    if not (ROOT / ".git").exists():
        run(["git", "init", "-b", "main"]); 
    run(["git", "add", "-A"]); run(["git", "commit", "-m", "Islamic video studio", "--allow-empty"], capture_output=True)
    has_remote = run(["git", "remote", "get-url", "origin"], capture_output=True).returncode == 0
    if not has_remote:
        name = ask("New GitHub repo name", "islamic-video-studio")
        vis = "--public" if yes("Public repo? (recommended: unlimited free Actions minutes; private = 2000 min/month)", True) else "--private"
        if run(["gh", "repo", "create", name, vis, "--source", ".", "--remote", "origin", "--push"]).returncode: bad("Repo creation failed (read above)"); return False
    else:
        run(["git", "push", "-u", "origin", "HEAD"])
    say("\nTurning on workflow permissions (read/write + allow PR creation)...")
    slug = run(["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"], capture_output=True, text=True).stdout.strip()
    r = run(["gh", "api", "-X", "PUT", f"repos/{slug}/actions/permissions/workflow", "-f", "default_workflow_permissions=write", "-F", "can_approve_pull_request_reviews=true"], capture_output=True, text=True)
    (ok if r.returncode == 0 else bad)("workflow permissions" + ("" if r.returncode == 0 else ": set them by hand in Settings > Actions > General"))
    e = env_read()
    say("\nUploading secrets (hidden; never printed)...")
    for k in ("YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN"):
        if e.get(k): gh_set("secret", k, e[k])
        else: say(f"  [skip] {k} not set yet: run option 2 first for YouTube uploads")
    say("\nOptional AI key for script drafting (Gemini is free: aistudio.google.com/apikey, billing OFF). Press Enter to skip.")
    ai = getpass.getpass("GEMINI_API_KEY (hidden): ").strip()
    if ai: env_set("GEMINI_API_KEY", ai); gh_set("secret", "GEMINI_API_KEY", ai)
    say("\nSetting variables...")
    gh_set("variable", "IVS_YT_PRIVACY", ask("YouTube privacy (private/unlisted/public)", "private"))
    gh_set("variable", "IVS_VIDEOS_PER_DAY", ask("Videos per day (free quota allows about 6)", "5"))
    if yes("\nStart the first run now?", True):
        run(["gh", "workflow", "run", "daily.yml"]); say("Started. Watch it: GitHub repo > Actions tab > daily-video")
    say("\nGitHub setup done. Approve videos by commenting /approve N on the review issue.")
    return True

def main():
    if "--check" in sys.argv: sys.exit(0 if check_tools() else 1)
    say("ISLAMIC VIDEO STUDIO - guided setup (free, $0)\n  1) Local setup\n  2) YouTube login\n  3) GitHub setup\n  4) Everything, in order\n  q) Quit")
    c = ask("Choose", "4").lower()
    if c in ("1", "4"): 
        if not local_setup() and c == "4": return
    if c in ("2", "4"): youtube_login()
    if c in ("3", "4"): github_setup()

if __name__ == "__main__":
    main()
