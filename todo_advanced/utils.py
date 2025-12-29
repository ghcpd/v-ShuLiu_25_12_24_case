"""Utility helpers used across modules."""
from __future__ import annotations

import time


def now_ts() -> float:
    return time.time()
