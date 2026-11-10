# Free Gemini key, Openverse SFX, Earshot

## Gemini (free tier) for story drafting
1. https://aistudio.google.com/apikey -> "Create API key" (no card). Do NOT enable billing on that project: then it can never charge.
2. GitHub repo -> Settings -> Secrets and variables -> Actions -> secret `GEMINI_API_KEY`. Optional variable `GEMINI_MODEL` (default `gemini-2.5-flash`; Google renames models, so change it here if one is retired).
3. Locally: `export GEMINI_API_KEY=...`. `IVS_LLM=auto|gemini|ollama|none` forces a choice. Auto = Gemini if a key exists, else Ollama, else the deterministic fallback.
- Free-tier rate limits (HTTP 429) are retried with back-off, then the run falls back; it never pays.
- Only public text is sent (verified translation + your sourced notes). On the free tier Google may use prompts to improve its products.
- Gemini only drafts. Every line still goes through the same source-support, no-Arabic, no-invented-facts checks, and the draft is ignored until you remove `needs_human_review`.
- The key is sent only in the `x-goog-api-key` header. Not tested live from the sandbox (no access); tested with mocks.

## Openverse real SFX
Used automatically when the network allows (`audio.sfx.openverse.enabled: auto`); otherwise the synthetic effects are used. Licences cc0 / by / pdm only; each pick is pinned so renders stay reproducible; CC BY credits are added to the video description. Never layered over Quran recitation. Not tested live from the sandbox (Openverse blocked there).

## Earshot (optional, experimental)
`verify_with_earshot: false` by default. Needs torch + CLAP, installed from GitHub (not the PyPI package named "earshot"). Heavy for a free runner; leave off unless you need it.
