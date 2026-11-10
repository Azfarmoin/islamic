"""Scenery for EVERY video (ayat, hadith, stories). Picks a faceless animated landscape (anim.SCENES) from the meaning of the verified English text.
Scenery only: sky, light, dunes, sea, mountains, stars, geometric pattern. No people, no faces, no prophets/angels. It is mood, NOT a claim about where or when anything happened."""
from __future__ import annotations
import hashlib
RULES = [  # (keywords in the English text/theme, scene tag)
    (("storm", "punish", "torment", "wrath", "fire"), "sea_storm"),
    (("ship", "sea", "ocean", "boat", "water", "rain", "river", "ocean"), "sea_calm"),
    (("night", "darkness", "sleep", "prostrat", "pray at night", "moon"), "desert_night"),
    (("mountain", "hill", "difficult", "difficulty", "hardship", "patience", "persever", "burden", "trial"), "mountain_dawn"),
    (("relief", "ease", "hope", "dawn", "morning", "light", "mercy", "forgiv", "repent", "guidance", "guide"), "desert_dawn"),
    (("star", "heaven", "sky", "creat", "earth", "universe", "knowledge", "read", "pen"), "sky_stars"),
    (("remember", "remembrance", "prayer", "worship", "thank", "grateful", "trust", "rely", "heart"), "geometric_dawn"),
]
CALM = ["sky_stars", "desert_dawn", "geometric_night", "mountain_dawn", "geometric_dawn", "night_sea"]
def pick(text: str, key: str = "", prev: str | None = None) -> str:
    t = (text or "").lower()
    for words, tag in RULES:
        if any(w in t for w in words) and tag != prev: return tag
    h = int(hashlib.sha256(((key or "") + t).encode()).hexdigest(), 16)       # deterministic, different per video
    c = [x for x in CALM if x != prev]; return c[h % len(c)]

def sequence(text: str, key: str, n: int) -> list[str]:
    """n DIFFERENT scenery looks for one video (3-4 changes): the verse's own meaning first, then calm complementary looks, never the same twice in a row."""
    seq = [pick(text, key)]; h = int(hashlib.sha256((key or "x").encode()).hexdigest(), 16); pool = [t for t in dict.fromkeys(CALM + [r[1] for r in RULES]) if t != "sea_storm"]
    i = 0
    while len(seq) < n:
        c = pool[(h + i * 5) % len(pool)]; i += 1
        if c not in seq: seq.append(c)
    return seq
