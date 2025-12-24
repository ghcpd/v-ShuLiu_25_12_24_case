"""Small utilities used across the package."""
from typing import Iterable, List


def fuzzy_contains(haystack: str, needle: str) -> bool:
    return needle.lower() in haystack.lower()


def chunked(iterable: Iterable, size: int):
    it = iter(iterable)
    while True:
        chunk = []
        try:
            for _ in range(size):
                chunk.append(next(it))
        except StopIteration:
            if chunk:
                yield chunk
            break
        yield chunk
