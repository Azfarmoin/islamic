from types import SimpleNamespace as N
from ivs.topics import TopicSelector as T

def test_topic_ids():
    assert T.topic_id("quran:94:5-6") == "quran:94" and T.topic_id("quran:94:1") == "quran:94"
    assert T.topic_id("story:al-fil-p2") == "story:al-fil" and T.topic_id("story:al-fil") == "story:al-fil"
    assert T.topic_id("hadith:bukhari:6018") == "hadith:bukhari:6018"

def test_recent_window_and_relax():
    class C:
        def __init__(s, keys): s.keys = keys
        def execute(s, q, a): return N(fetchall=lambda: [{"key": k} for k in s.keys[-a[0]:][::-1]])
    sel = T.__new__(T); sel.cfg = {"dedupe": {"recent_topic_window": 3}}; sel.db = N(conn=C(["quran:94:1", "story:al-fil-p1", "quran:2:153", "quran:14:7"]))
    assert sel._recent_topics() == {"story:al-fil", "quran:2", "quran:14"}
    calls = []
    sel._pick = lambda only, avoid: (calls.append(bool(avoid)) or (None if avoid else "x"))
    sel.db.log = lambda *a, **k: None
    assert sel.next_content() == "x" and calls == [True, False]       # relaxes once instead of skipping the day
