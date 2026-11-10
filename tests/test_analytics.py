from ivs import analytics as A

def test_learn_needs_samples():
    assert "at least 5" in A.learn([{"category": "x", "views_per_day": 1}])[0]
    r = [{"category": "a", "views_per_day": v} for v in (1, 2, 3)] + [{"category": "b", "views_per_day": v} for v in (9, 9)]
    assert "Highest: b" in A.learn(r)[0]

def test_fetch_parses(monkeypatch):
    class P:
        def access_token(self): return "t"
    class H:
        def get(self, url, params=None, headers=None, timeout=0):
            class R:
                def raise_for_status(s): pass
                def json(s): return {"items": [{"id": "v1", "statistics": {"viewCount": "10", "likeCount": "2"}}]}
            return R()
    assert A.fetch(P(), ["v1"], H()) == {"v1": {"viewCount": 10, "likeCount": 2, "commentCount": 0}}
