import json
from ivs import scriptgen as S

class R:
    def __init__(s, code, js=None, text=""): s.status_code, s._j, s.text = code, js, text
    def json(s): return s._j
    def raise_for_status(s):
        if s.status_code >= 400: raise RuntimeError(s.status_code)

def test_gemini_header_key_and_retry(monkeypatch):
    calls = []
    def post(url, json=None, headers=None, timeout=0):
        calls.append((url, headers)); 
        return R(429) if len(calls) == 1 else R(200, {"candidates": [{"content": {"parts": [{"text": "{\"ok\":1}"}]}}]})
    monkeypatch.setattr(S.requests, "post", post); monkeypatch.setattr("time.sleep", lambda s: None)
    g = S.Gemini(key="K123", model="m"); assert g.generate("x") == '{"ok":1}'
    assert len(calls) == 2 and "K123" not in calls[0][0] and calls[0][1]["x-goog-api-key"] == "K123"

def test_gemini_gives_up_without_paying(monkeypatch):
    monkeypatch.setattr(S.requests, "post", lambda *a, **k: R(429)); monkeypatch.setattr("time.sleep", lambda s: None)
    try: S.Gemini(key="k", tries=2).generate("x"); assert False
    except RuntimeError as e: assert "limit" in str(e)

def test_pick_llm(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False); monkeypatch.setenv("IVS_LLM", "auto")
    monkeypatch.setattr(S.Ollama, "available", lambda s: False); assert S.pick_llm() is None
    monkeypatch.setenv("GEMINI_API_KEY", "k"); assert isinstance(S.pick_llm(), S.Gemini)
    monkeypatch.setenv("IVS_LLM", "none"); assert S.pick_llm() is None
