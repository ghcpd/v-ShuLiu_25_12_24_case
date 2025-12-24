"""Higher-level tag logic, recommendations and utilities."""
from __future__ import annotations
from typing import List, Iterable, Optional, Tuple
from difflib import get_close_matches
from todo_advanced_pkg import storage


def normalize_name(name: str) -> str:
    return name.strip().lower()


def create_or_get_tag(name: str, **meta) -> str:
    name = normalize_name(name)
    storage._ensure_tag_row(storage._get_conn(), name)
    return name


def recommend_tags_for_text(text: str, top_n: int = 5) -> List[Tuple[str, float]]:
    # simple keyword-based recommendation + co-occurrence boost
    kws = [p for p in text.lower().split() if p]
    # candidate names from existing tags
    candidates = storage.all_tags()
    fuzzy = get_close_matches(" ".join(kws), candidates, n=top_n, cutoff=0.3)
    # score by usage_count + fuzzy match order
    scored = []
    for c in fuzzy:
        row = storage._get_tag_row_by_name(storage._get_conn(), c)
        score = (row["usage_count"] if row else 0) + 1.0
        scored.append((c, float(score)))
    # supplement with most-used tags
    if len(scored) < top_n:
        extra = sorted(storage.tag_stats().items(), key=lambda kv: -kv[1])
        for name, cnt in extra:
            if name not in [s[0] for s in scored]:
                scored.append((name, float(cnt)))
            if len(scored) >= top_n:
                break
    return scored[:top_n]


def tag_cooccurrence(tag: str, top_n: int = 5) -> List[Tuple[str, int]]:
    conn = storage._get_conn()
    row = storage._get_tag_row_by_name(conn, tag)
    if not row:
        return []
    cur = conn.execute(
        "SELECT t.name, c.weight FROM tag_cooccurrence c JOIN tags t ON t.id=c.tag_b WHERE c.tag_a=? ORDER BY c.weight DESC LIMIT ?",
        (row["id"], top_n),
    )
    return [(r["name"], r["weight"]) for r in cur.fetchall()]
