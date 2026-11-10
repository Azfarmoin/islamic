import importlib.util, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("easy_setup", Path(__file__).resolve().parent.parent / "easy_setup.py")
E = importlib.util.module_from_spec(spec); spec.loader.exec_module(E)

def test_env_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(E, "ENV", tmp_path / ".env")
    E.env_set("A", "1"); E.env_set("B", "x=y"); E.env_set("A", "2")
    assert E.env_read() == {"A": "2", "B": "x=y"}

def test_secret_never_on_command_line(monkeypatch):
    seen = {}
    def fake(cmd, **kw): seen.update(cmd=cmd, input=kw.get("input")); return type("R", (), {"returncode": 0, "stderr": ""})()
    monkeypatch.setattr(E, "run", fake)
    E.gh_set("secret", "K", "topsecret")
    assert "topsecret" not in " ".join(seen["cmd"]) and seen["input"] == "topsecret"
