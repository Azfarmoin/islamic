import json, subprocess
from pathlib import Path
import pytest
from ivs import openverse as O, sfx

def cand(**k):
    d = {"id": "a1", "title": "Footsteps on sand walking", "creator": "Jo", "license": "cc0", "license_version": "1.0", "url": "https://x/a.mp3", "foreign_landing_url": "https://freesound.org/s/1/", "duration": 12000, "filetype": "mp3", "source": "freesound", "tags": [{"name": "footsteps"}]}
    d.update(k); return d

def test_licence_filter_rejects_nc_nd_sa_and_speech_music_prayer():
    for lic in ("by-nc", "by-nd", "by-sa", "nc", ""): assert not O.usable(cand(license=lic))
    for t in ("Call to prayer", "Quran recitation ambient", "Nasheed beat", "Man speaking footsteps", "my song"): assert not O.usable(cand(title=t)), t
    assert O.usable(cand()) and O.usable(cand(license="by")) and O.usable(cand(license="pdm"))

def test_pick_prefers_cc0_and_relevant_and_requires_relevance():
    a = cand(id="a", license="by"); b = cand(id="b", license="cc0"); c = cand(id="c", title="Door slam", tags=[], license="cc0")
    assert O.pick([a, b, c], "footsteps")["id"] == "b"
    assert O.pick([c], "footsteps") is None

def test_credit_line_has_creator_licence_link():
    s = O.credit(cand(license="by", license_version="4.0"))
    assert "Jo" in s and "CC BY 4.0" in s and "freesound.org" in s

def test_real_effect_pins_downloads_and_converts(tmp_path, monkeypatch):
    calls = []
    def http(url, timeout=20): calls.append(url); return json.dumps({"results": [cand()]}).encode()
    src = tmp_path / "src.wav"; subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "anoisesrc=d=2:c=brown", str(src)], check=True)
    monkeypatch.setattr(O, "HTTP", http); monkeypatch.setattr(O, "_download", lambda url, dst, max_mb=15: dst.write_bytes(src.read_bytes())); O.STATE["offline"] = False
    r = O.real_effect("footsteps", 5.0, tmp_path); assert r and r[0].exists() and r[1]["kind"] == "sfx" and r[1]["license"] == "CC0 1.0"
    n = len(calls); r2 = O.real_effect("footsteps", 7.0, tmp_path); assert r2 and len(calls) == n          # pinned: no second search
    from ivs.audio import probe_duration
    assert abs(probe_duration(r[0]) - 5.0) < 0.2 and abs(probe_duration(r2[0]) - 7.0) < 0.2           # 2 s source looped to length

def test_offline_falls_back_to_synthetic(tmp_path, monkeypatch):
    def boom(url, timeout=20): raise OSError("blocked")
    monkeypatch.setattr(O, "HTTP", boom); O.STATE["offline"] = False
    cfg = {"audio": {"sfx": {"openverse": {"enabled": "auto"}}}}; assets = []
    out = sfx.effects_for("army_march", 3.0, tmp_path, cfg, assets)
    assert out and all(Path(p).exists() for p in out) and assets == [] and O.STATE["offline"] is True
    O.STATE["offline"] = False

def test_disabled_never_touches_network(tmp_path, monkeypatch):
    monkeypatch.setattr(O, "HTTP", lambda *a, **k: (_ for _ in ()).throw(AssertionError("network used")))
    assert sfx.effects_for("flock", 2.0, tmp_path, {"audio": {"sfx": {"openverse": {"enabled": False}}}}, [])
