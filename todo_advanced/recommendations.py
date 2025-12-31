"""
Tag recommendation engine using keyword similarity and co-occurrence history.
"""

from typing import List, Tuple
from difflib import SequenceMatcher
from .tags import get_tag_manager
from .storage import get_storage


class TagRecommender:
    """Recommends tags based on similarity and usage patterns."""

    def __init__(self):
        self.tag_manager = get_tag_manager()
        self.storage = get_storage()

    def _string_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings (0.0 to 1.0)."""
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

    def recommend_by_keyword(
        self, keyword: str, limit: int = 5, threshold: float = 0.4
    ) -> List[Tuple[str, float]]:
        """
        Recommend tags based on keyword similarity.
        Returns list of (tag_name, similarity_score) tuples.
        """
        all_tags = self.tag_manager.list_tags()
        recommendations = []

        for tag in all_tags:
            similarity = self._string_similarity(keyword, tag.name)

            # Also check aliases
            for alias in tag.aliases:
                alias_sim = self._string_similarity(keyword, alias)
                similarity = max(similarity, alias_sim)

            if similarity >= threshold:
                recommendations.append((tag.name, similarity))

        # Sort by score descending
        recommendations.sort(key=lambda x: x[1], reverse=True)
        return recommendations[:limit]

    def recommend_by_task_content(
        self, task_text: str, existing_tags: List[str] = None, limit: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Recommend tags for a task based on its content and existing tags.
        Returns list of (tag_name, score) tuples.
        """
        if existing_tags is None:
            existing_tags = []

        # Extract keywords from task text
        words = task_text.lower().split()
        all_tags = self.tag_manager.list_tags()

        scores = {}
        for tag in all_tags:
            if tag.name in existing_tags:
                continue

            # Keyword matching
            keyword_score = max(
                (self._string_similarity(word, tag.name) for word in words),
                default=0.0,
            )

            # Co-occurrence score with existing tags
            cooccurrence_score = 0.0
            if existing_tags:
                cooccurrences = [
                    self.storage.get_tag_cooccurrence(tag.name, existing_tag)
                    for existing_tag in existing_tags
                ]
                if cooccurrences:
                    cooccurrence_score = sum(cooccurrences) / len(cooccurrences) / 10.0

            # Usage frequency score
            all_tag_usages = [t.usage_count for t in all_tags if t.usage_count > 0]
            max_usage = max(all_tag_usages) if all_tag_usages else 1
            usage_score = (tag.usage_count / max_usage) * 0.3 if max_usage > 0 else 0

            total_score = (keyword_score * 0.5) + (cooccurrence_score * 0.3) + usage_score
            if total_score > 0:
                scores[tag.name] = total_score

        # Sort by score descending
        recommendations = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return recommendations[:limit]

    def recommend_by_cooccurrence(
        self, existing_tags: List[str], limit: int = 5
    ) -> List[Tuple[str, int]]:
        """
        Recommend tags that frequently co-occur with given tags.
        Returns list of (tag_name, total_cooccurrence_count) tuples.
        """
        cooccurrence_scores = {}

        for tag in existing_tags:
            related = self.tag_manager.get_related_tags(tag, limit=limit * 2)
            for related_tag, count in related:
                cooccurrence_scores[related_tag] = (
                    cooccurrence_scores.get(related_tag, 0) + count
                )

        # Sort by count descending
        recommendations = sorted(
            cooccurrence_scores.items(), key=lambda x: x[1], reverse=True
        )
        return recommendations[:limit]


# Global recommender instance
_recommender: TagRecommender = None


def get_recommender() -> TagRecommender:
    """Get or create global recommender."""
    global _recommender
    if _recommender is None:
        _recommender = TagRecommender()
    return _recommender


def reset_recommender() -> None:
    """Reset recommender (for testing)."""
    global _recommender
    _recommender = None
