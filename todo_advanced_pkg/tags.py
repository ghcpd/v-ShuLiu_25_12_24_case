"""Tag logic and recommendation utilities."""
import json
from datetime import datetime
from typing import List, Dict
from difflib import SequenceMatcher


def score_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def recommend_tags_by_text(candidate_tags: List[Dict], text: str, top_k: int = 5) -> List[str]:
    text = text.lower()
    scored = []
    for t in candidate_tags:
        name = t["name"]
        sim = score_similarity(name, text)
        score = sim * 0.6 + (min(t.get("usage_count", 0), 100) / 100.0) * 0.4
        scored.append((score, name))
    scored.sort(reverse=True)
    return [name for _, name in scored[:top_k]]
