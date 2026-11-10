from ivs import scriptgen as S

def _clean(mp):
    for k in ["GEMINI_API_KEY","AI_API_KEY","AI_BASE_URL","AI_MODEL","GROQ_API_KEY","OPENROUTER_API_KEY","MISTRAL_API_KEY","TOGETHER_API_KEY","DEEPSEEK_API_KEY","OPENAI_API_KEY","ANTHROPIC_API_KEY","IVS_LLM"]:
        mp.delenv(k, raising=False)
    mp.setattr(S.Ollama, "available", lambda self: False)

def test_custom_key(monkeypatch):
    _clean(monkeypatch); monkeypatch.setenv("AI_API_KEY", "k"); monkeypatch.setenv("AI_BASE_URL", "http://x/v1"); monkeypatch.setenv("AI_MODEL", "m")
    l = S.pick_llm(); assert l.name == "custom" and l.model == "m"

def test_preset_and_force(monkeypatch):
    _clean(monkeypatch); monkeypatch.setenv("GROQ_API_KEY", "k"); monkeypatch.setenv("OPENAI_API_KEY", "k2")
    assert S.pick_llm().name == "groq"
    assert S.pick_llm(prefer="openai").name == "openai"
    monkeypatch.setenv("IVS_LLM", "none"); assert S.pick_llm() is None

def test_anthropic_and_none(monkeypatch):
    _clean(monkeypatch); assert S.pick_llm() is None
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k"); assert isinstance(S.pick_llm(), S.Anthropic)

def test_openai_compat_call(monkeypatch):
    class R:
        status_code = 200
        def raise_for_status(self): pass
        def json(self): return {"choices": [{"message": {"content": "{}"}}]}
    seen = {}
    def post(url, json=None, headers=None, timeout=0): seen.update(url=url, h=headers); return R()
    monkeypatch.setattr(S.requests, "post", post)
    assert S.OpenAICompat("k", "http://x/v1", "m").generate("hi") == "{}"
    assert seen["url"].endswith("/chat/completions") and seen["h"]["Authorization"] == "Bearer k"
