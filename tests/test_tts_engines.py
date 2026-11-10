from pathlib import Path
from ivs import tts_engines as T

def test_skips_unavailable_and_unsupported(monkeypatch, tmp_path):
    monkeypatch.setattr(T, "available", lambda: {"chatterbox": False, "qwen3": True, "fish": False})
    assert T.try_engines("x", "ur", tmp_path / "a.wav", {"engines": ["chatterbox", "qwen3", "fish"]}) is None   # no Urdu support anywhere
    assert T.try_engines("x", "en", tmp_path / "a.wav", {"engines": []}) is None

def test_order_and_fallthrough(monkeypatch, tmp_path):
    monkeypatch.setattr(T, "available", lambda: {"chatterbox": True, "qwen3": True, "fish": False})
    def boom(*a, **k): raise RuntimeError("gpu oom")
    monkeypatch.setitem(T.BACKENDS, "chatterbox", boom)
    monkeypatch.setitem(T.BACKENDS, "qwen3", lambda *a, **k: 4.2)
    d, credit = T.try_engines("hello", "en", tmp_path / "a.wav", {"engines": ["chatterbox", "qwen3"]})
    assert d == 4.2 and "Qwen3-TTS" in credit and "Apache" in credit

def test_fish_needs_url(monkeypatch):
    monkeypatch.delenv("FISH_SPEECH_URL", raising=False)
    assert T.available()["fish"] is False
