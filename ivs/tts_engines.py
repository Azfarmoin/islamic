"""Optional neural TTS backends for STORY narration only (never Quran recitation).
Each backend is auto-detected: it activates only if its package imports (or, for Fish Speech,
FISH_SPEECH_URL is set). Any failure falls through to the next engine, ending at Kokoro/eSpeak.
UNTESTED LIVE in the build sandbox (no network/GPU) - covered by mocked tests only."""
from __future__ import annotations
import importlib.util, os, subprocess
from pathlib import Path

LICENCE = {"chatterbox": "MIT", "qwen3": "Apache-2.0", "fish": "code Apache-2.0; weights CC-BY-NC-SA-4.0 (non-commercial)"}
LANGS = {"chatterbox": {"en", "ar"}, "qwen3": {"en"}, "fish": {"en", "ar"}}    # Urdu: none of them support it
_CACHE: dict = {}

def _has(mod: str) -> bool:
    try: return importlib.util.find_spec(mod) is not None
    except Exception: return False

def _device() -> str:
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception: return "cpu"

def available() -> dict[str, bool]:
    return {"chatterbox": _has("chatterbox"), "qwen3": _has("qwen_tts"), "fish": bool(os.environ.get("FISH_SPEECH_URL"))}

def _dur(p: Path) -> float:
    o = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout
    return float(o.strip())

def speak_chatterbox(text: str, lang: str, out: Path, opts: dict) -> float:
    import torchaudio
    m = _CACHE.get("cb")
    if m is None:
        if lang == "en":
            from chatterbox.tts import ChatterboxTTS
            m = ChatterboxTTS.from_pretrained(device=_device())
        else:
            from chatterbox.mtl_tts import ChatterboxMultilingualTTS
            m = ChatterboxMultilingualTTS.from_pretrained(device=_device())
        _CACHE["cb"] = m
    kw = {"language_id": lang} if lang != "en" else {}
    wav = m.generate(text, **kw)
    torchaudio.save(str(out), wav, m.sr)
    return _dur(out)

def speak_qwen3(text: str, lang: str, out: Path, opts: dict) -> float:
    import soundfile as sf
    m = _CACHE.get("qw")
    if m is None:
        from qwen_tts import Qwen3TTSModel
        m = Qwen3TTSModel.from_pretrained(opts.get("qwen3_model", "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice"), device_map=_device())
        _CACHE["qw"] = m
    wavs, sr = m.generate_custom_voice(text=text, language="English", speaker=opts.get("qwen3_speaker", "Ryan"))
    sf.write(str(out), wavs[0], sr)
    return _dur(out)

def speak_fish(text: str, lang: str, out: Path, opts: dict) -> float:
    """Experimental: POSTs to a self-hosted Fish Speech API server given by FISH_SPEECH_URL.
    The request/response shape is NOT verified here - treat as a stub until tested against your server."""
    import requests
    r = requests.post(os.environ["FISH_SPEECH_URL"].rstrip("/") + "/v1/tts", json={"text": text, "format": "wav"}, timeout=int(opts.get("timeout", 180)))
    r.raise_for_status()
    out.write_bytes(r.content)
    return _dur(out)

BACKENDS = {"chatterbox": speak_chatterbox, "qwen3": speak_qwen3, "fish": speak_fish}
NAMES = {"chatterbox": "Chatterbox", "qwen3": "Qwen3-TTS", "fish": "Fish Speech"}

def try_engines(text: str, lang: str, out: Path, nar: dict) -> tuple[float, str] | None:
    """Walk audio.narration.engines in order; return (duration, credit) or None to let Kokoro/eSpeak take over."""
    order = nar.get("engines") or []
    av = available()
    for name in order:
        if name not in BACKENDS or not av.get(name) or lang not in LANGS[name]: continue
        try:
            d = BACKENDS[name](text, lang, out, nar)
            if d and d > 0.3: return d, f"{NAMES[name]} ({LICENCE[name]})"
        except Exception:
            continue
    return None
