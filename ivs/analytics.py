"""Post-publish stats + simple learning notes.
SCOPE (honest): uses videos.list?part=statistics (1 quota unit per 50 ids) -> views, likes, comments only.
Impressions, CTR, watch time and audience retention need the separate YouTube Analytics API and an extra OAuth scope (yt-analytics.readonly)
which this project does not request, so they are NOT collected. Learning = which categories/hooks got more views per day; advisory only, never auto-changes content."""
from __future__ import annotations
import datetime as dt, json, os
import requests

URL = "https://www.googleapis.com/youtube/v3/videos"

def fetch(pub, ids: list[str], http=None) -> dict[str, dict]:
    """pub = YouTubePublisher (for access_token). Returns {video_id: {views, likes, comments}}."""
    http = http or requests; tok = pub.access_token(); out = {}
    for i in range(0, len(ids), 50):
        r = http.get(URL, params={"part": "statistics", "id": ",".join(ids[i:i + 50])}, headers={"Authorization": f"Bearer {tok}"}, timeout=30)
        r.raise_for_status()
        for it in r.json().get("items", []):
            s = it.get("statistics", {}); out[it["id"]] = {k: int(s.get(k, 0)) for k in ("viewCount", "likeCount", "commentCount")}
    return out

def collect(db, pub, http=None) -> dict:
    rows = [r for r in db.items("published") if r["platform_id"]]
    stats = fetch(pub, [r["platform_id"] for r in rows], http) if rows else {}
    now = dt.datetime.now(dt.timezone.utc)
    report = []
    for r in rows:
        s = stats.get(r["platform_id"])
        if not s: continue
        try: age = max(1.0, (now - dt.datetime.fromisoformat(r["published_at"])).total_seconds() / 86400)
        except Exception: age = 1.0
        rec = {"item": r["id"], "key": r["key"] if "key" in r.keys() else None, "category": r["category"] if "category" in r.keys() else None, **s, "views_per_day": round(s["viewCount"] / age, 2), "age_days": round(age, 1)}
        db.put_setting(f"stats:{r['platform_id']}", json.dumps(rec)); report.append(rec)
    return {"videos": report, "learning": learn(report), "not_collected": "impressions, CTR, watch time, retention (need YouTube Analytics API scope)"}

def learn(report: list[dict]) -> list[str]:
    if len(report) < 5: return ["Need at least 5 published videos before any pattern means anything."]
    by = {}
    for r in report: by.setdefault(r.get("category") or "?", []).append(r["views_per_day"])
    avg = {k: round(sum(v) / len(v), 2) for k, v in by.items() if len(v) >= 2}
    if not avg: return ["Not enough videos per category to compare."]
    best = max(avg, key=avg.get)
    return [f"Views/day by category (n>=2): {avg}. Highest: {best}. Small samples and channel age dominate; treat as a hint, not a rule."]
