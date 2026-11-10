"""Real sound effects from Openverse (api.openverse.org, free, no API key) with strict licence handling.
 - Only CC0, CC BY and Public Domain Mark audio (commercial use + adaptation allowed). NC / ND / SA are never accepted.
 - Every download is recorded with creator, licence and link; CC BY credit lines go into the video description automatically.
 - The first good pick per sound role is PINNED in the cache, so there are ~8 searches ever (anonymous limit is small) and every video keeps a consistent sound.
 - Never used under Quran verses or recitation (sfx.py already stays silent there). Speech/music/chant/prayer-like results are rejected by title/tags.
 - Any failure (offline, rate limit, no safe match) silently falls back to the built-in synthetic effect.
Optional: earshot (github.com/Leonxlnx/earshot, MIT; install from GitHub, NOT the unrelated 'earshot' on PyPI) can double-check that a download really sounds like what it claims."""
from __future__ import annotations
import json, re, subprocess, urllib.parse, urllib.request
from pathlib import Path

API = "https://api.openverse.org/v1/audio/"
ALLOWED = ("cc0", "by", "pdm")
UA = "islamic-video-engine/1.0 (free, open-source video pipeline)"
LICENSE_NAME = {"cc0": "CC0 1.0", "pdm": "Public Domain Mark 1.0", "by": "CC BY"}
QUERIES = {   # synthetic recipe name -> Openverse queries (tried in order) + the words a good result should contain
    "footsteps": (["footsteps on sand", "footsteps gravel walking", "marching footsteps"], ["footstep", "step", "walk", "march"]),
    "rumble": (["low rumble drone", "distant rumble"], ["rumble", "drone", "low"]),
    "wings": (["birds wings flapping flock", "wing flap"], ["wing", "flap", "flock", "bird"]),
    "chirps": (["birds chirping", "morning birds"], ["bird", "chirp", "tweet", "song"]),
    "murmur": (["crowd murmur ambience", "crowd walla"], ["crowd", "murmur", "walla", "people"]),
    "thunder": (["distant thunder", "thunder rumble"], ["thunder"]),
}
BAD = re.compile(r"\b(speech\w*|speak\w*|voice\w*|vocal\w*|sing\w*|song\w*|music\w*|melod\w*|chant\w*|nasheed\w*|quran\w*|koran\w*|recit\w*|adhan|azan|pray\w*|dua|laugh\w*|scream\w*|cry\w*|crying|talk\w*|lyric\w*|beat\w*|pack|remix\w*|advert\w*|jingle\w*|narrat\w*|podcast\w*)\b", re.I)
STATE = {"offline": False}

def _get(url: str, timeout=20) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r: return r.read()
HTTP = _get          # tests replace this

def search(q: str, size=20) -> list[dict]:
    p = {"q": q, "license": ",".join(ALLOWED), "category": "sound_effect", "page_size": size, "mature": "false"}
    d = json.loads(HTTP(API + "?" + urllib.parse.urlencode(p)))
    return d.get("results", [])

def usable(c: dict) -> bool:
    lic = (c.get("license") or "").lower()
    if lic not in ALLOWED or not c.get("url"): return False
    text = " ".join([c.get("title") or ""] + [t.get("name", "") for t in (c.get("tags") or [])])
    if BAD.search(text): return False
    if (c.get("filetype") or "").lower() not in ("mp3", "ogg", "wav", "flac", "oga", "m4a", ""): return False
    return True

def score(c: dict, role: str, need: float) -> float:
    words = QUERIES[role][1]; text = ((c.get("title") or "") + " " + " ".join(t.get("name", "") for t in (c.get("tags") or []))).lower()
    s = 2.0 * sum(w in text for w in words)
    s += 1.0 if (c.get("license") or "").lower() in ("cc0", "pdm") else 0     # no credit needed: cleaner
    d = (c.get("duration") or 0) / 1000.0                                      # Openverse reports milliseconds
    if d: s += 1.5 if 3 <= d <= 90 else -2
    return s

def pick(cands: list[dict], role: str, need=8.0) -> dict | None:
    ok = [c for c in cands if usable(c)]
    def hits(c): t = ((c.get("title") or "") + " " + " ".join(x.get("name", "") for x in (c.get("tags") or []))).lower(); return sum(w in t for w in QUERIES[role][1])
    ok = [c for c in ok if hits(c) >= 1]            # must actually mention the sound we want
    ok.sort(key=lambda c: -score(c, role, need))
    return ok[0] if ok else None

def credit(c: dict) -> str:
    """CC BY needs: title, creator, licence (+ link). We always write it, also for CC0."""
    lic = (c.get("license") or "").lower(); ver = c.get("license_version") or ""
    name = f"{LICENSE_NAME.get(lic, lic.upper())}{' ' + ver if lic == 'by' and ver else ''}"
    return f"\"{c.get('title') or 'untitled'}\" by {c.get('creator') or 'unknown'} ({c.get('source') or 'openverse'}), {name}: {c.get('foreign_landing_url') or c.get('url')}"

def _download(url: str, dst: Path, max_mb=15) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40) as r:
        n = int(r.headers.get("Content-Length") or 0)
        if n > max_mb * 1e6: raise ValueError("file too large")
        data = r.read(int(max_mb * 1e6) + 1)
        if len(data) > max_mb * 1e6: raise ValueError("file too large")
    dst.write_bytes(data)

def prepare(raw: Path, out: Path, dur: float, loud=-30) -> Path:
    """Normalise, then loop with cross-fades (no clicks at the seam) and fade in/out to exactly `dur` seconds."""
    from .audio import run, probe_duration
    base = out.with_suffix(".base.wav")
    run(["ffmpeg", "-y", "-i", str(raw), "-t", "45", "-vn", "-af", f"aformat=channel_layouts=stereo,aresample=44100,loudnorm=I={loud}:TP=-4:LRA=9,aresample=44100", str(base)])
    d = probe_duration(base); x = 0.4
    fade = f"afade=t=in:d=0.6,afade=t=out:st={max(dur - 0.8, 0):.2f}:d=0.8"
    if d >= dur + 0.1: run(["ffmpeg", "-y", "-i", str(base), "-t", f"{dur:.2f}", "-af", fade, "-ar", "44100", str(out)])
    else:
        reps = min(40, int(dur / max(d - x, 0.5)) + 2); inp = []; chain = []; last = "0:a"
        for i in range(reps): inp += ["-i", str(base)]
        for i in range(1, reps): chain.append(f"[{last}][{i}:a]acrossfade=d={x}:c1=tri:c2=tri[a{i}]"); last = f"a{i}"
        chain.append(f"[{last}]atrim=0:{dur:.2f},{fade}[o]")      # fades go inside the graph (cannot combine -af with -filter_complex)
        run(["ffmpeg", "-y", *inp, "-filter_complex", ";".join(chain), "-map", "[o]", "-ar", "44100", str(out)])
    base.unlink(missing_ok=True); return out

def earshot_ok(wav: Path, role: str) -> bool | None:
    """Optional second opinion from earshot's `match` (None = not installed / unusable). Experimental: output parsed leniently, untested here."""
    import shutil
    if not shutil.which("earshot"): return None
    q = {"footsteps": "footsteps walking", "rumble": "low rumble", "wings": "birds flapping wings", "chirps": "birds chirping", "murmur": "crowd murmur", "thunder": "thunder"}[role]
    try:
        r = subprocess.run(["earshot", "match", str(wav), q, "--json"], capture_output=True, text=True, timeout=300)
        if r.returncode: return None
        hits = re.findall(r'"verdict"\s*:\s*"([^"]+)"', r.stdout)
        return bool(hits) and hits[0] in ("strong", "plausible")
    except Exception: return None

def real_effect(role: str, dur: float, cache: Path, ocfg: dict | None = None) -> tuple[Path, dict] | None:
    """-> (wav, asset-record) or None (use the synthetic effect)."""
    ocfg = ocfg or {}
    if STATE["offline"] or role not in QUERIES: return None
    d = Path(cache) / "openverse"; d.mkdir(parents=True, exist_ok=True); pin = d / f"pin_{role}.json"
    try:
        if pin.exists(): c = json.loads(pin.read_text())
        else:
            c = None
            for q in QUERIES[role][0]:
                c = pick(search(q), role, dur)
                if c: break
            if not c: pin.write_text("null"); return None
            raw = d / f"{c['id']}.raw"; _download(c["url"], raw, ocfg.get("max_mb", 15))
            if ocfg.get("verify_with_earshot"):
                tmp = d / f"{c['id']}.chk.wav"; prepare(raw, tmp, 6.0)
                if earshot_ok(tmp, role) is False: pin.write_text("null"); return None
            pin.write_text(json.dumps(c))
        if c is None: return None
        raw = d / f"{c['id']}.raw"
        if not raw.exists(): _download(c["url"], raw, ocfg.get("max_mb", 15))
        out = d / f"{role}_{c['id']}_{int(round(dur * 10))}.wav"
        if not out.exists(): prepare(raw, out, dur)
        lic = (c.get("license") or "").lower(); ver = c.get("license_version") or ""
        return out, {"name": out.name, "kind": "sfx", "source_url": c.get("foreign_landing_url") or c.get("url"),
                     "license": f"{LICENSE_NAME.get(lic, lic)}{' ' + ver if lic == 'by' and ver else ''}", "attribution": credit(c)}
    except Exception as e:
        STATE['last_error'] = repr(e)
        if "urlopen" in repr(e) or "URLError" in type(e).__name__ or isinstance(e, (OSError,)): STATE["offline"] = True      # stop retrying for this run
        return None
