from pathlib import Path
from ivs import audio as A

CFG = {"_root": ".", "paths": {"cache": "x"}, "audio": {"recitation": {"enabled": True, "permission_verified": True, "reciter": "Alafasy_128kbps", "base_url": "https://everyayah.com/data",
       "mirrors": ["everyayah", "islamic_network"], "islamic_edition": "ar.alafasy", "islamic_bitrate": 128}}}

def test_abs_ayah_known_points():
    assert A._abs_ayah(CFG, 1, 1) == 1 and A._abs_ayah(CFG, 2, 1) == 8 and A._abs_ayah(CFG, 114, 6) == 6236

def test_falls_back_to_second_mirror(monkeypatch, tmp_path):
    calls = []
    class R:
        def __init__(s, code, n): s.status_code, s.content = code, b"x" * n
    def get(u, timeout=0):
        calls.append(u); return R(404, 0) if "everyayah" in u else R(200, 5000)
    monkeypatch.setattr(A.requests, "get", get); monkeypatch.setattr(A, "probe_duration", lambda p: 3.0)
    r = A.fetch_recitation(CFG, tmp_path, 94, 5)
    assert r and "cdn.islamic.network" in r["source_url"] and r["source_url"].endswith(f"/{A._abs_ayah(CFG, 94, 5)}.mp3") and len(calls) == 2
    calls.clear(); r2 = A.fetch_recitation(CFG, tmp_path, 94, 5)       # cached: no network, source remembered
    assert r2["source_url"] == r["source_url"] and not calls

def test_all_mirrors_fail_returns_none(monkeypatch, tmp_path):
    class R: status_code = 500; content = b""
    monkeypatch.setattr(A.requests, "get", lambda u, timeout=0: R())
    assert A.fetch_recitation(CFG, tmp_path, 1, 1) is None
