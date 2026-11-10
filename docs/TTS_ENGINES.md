# Optional narration engines (stories only, never Quran)

Config: `audio.narration.engines: [chatterbox, qwen3, fish]`. Each is used only if installed; any failure falls back to Kokoro (English). Credit + licence are added to the video description.

| Engine | Install | Languages | Licence | Needs |
|---|---|---|---|---|
| Chatterbox | `pip install chatterbox-tts` | en, ar (no Urdu) | MIT | GPU recommended |
| Qwen3-TTS | `pip install qwen-tts` | en used here (no Urdu/Arabic) | Apache-2.0 | GPU |
| Fish Speech / OpenAudio | self-host server, `export FISH_SPEECH_URL=http://host:port` | en, ar (no Urdu) | code Apache-2.0, **weights CC-BY-NC-SA-4.0 (non-commercial)** | GPU |

Status: **not tested live** (sandbox has no network/GPU). Mock tests cover ordering and fallback only. Fish adapter is a stub; its request shape is unverified. GitHub's free CPU runners are too slow for these models, so they are mainly for local runs on your own GPU/Colab. Free tier stays $0: Kokoro remains the default on CI.
