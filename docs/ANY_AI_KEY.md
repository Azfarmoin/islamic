# Use any AI key for script drafting

Set ONE secret (GitHub: Settings > Secrets > Actions, or `export` locally). Auto order: Gemini > OpenAI-compatible > Anthropic > local Ollama > deterministic fallback. Force with `IVS_LLM`.

| Provider | Secret | Free tier? |
|---|---|---|
| Gemini | GEMINI_API_KEY | yes (keep billing off) |
| Groq | GROQ_API_KEY | yes, rate-limited |
| OpenRouter | OPENROUTER_API_KEY | `:free` models only |
| Mistral | MISTRAL_API_KEY | experiment tier |
| Together / DeepSeek / OpenAI | TOGETHER_/DEEPSEEK_/OPENAI_API_KEY | no - may bill you |
| Anthropic | ANTHROPIC_API_KEY | no - paid |
| Anything else OpenAI-compatible | AI_API_KEY + AI_BASE_URL + AI_MODEL | depends |

Free-tier terms change; check the provider. Paid keys break the $0 guarantee. All AI output is still validated line by line and needs human review. Only public source text is sent. Keys go only in auth headers. Untested live (sandbox is offline); mock-tested.
