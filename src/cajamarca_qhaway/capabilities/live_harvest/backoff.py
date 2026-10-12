"""Calculo de reintentos con exponential backoff y full jitter para peticiones HTTP."""

from __future__ import annotations

import random


def calculate_jitter_delay(
    attempt: int,
    initial_delay: float = 1.5,
    factor: float = 2.0,
    jitter_max: float = 1.0,
    max_delay: float = 30.0,
) -> float:
    """Calcula el tiempo de espera para el intento actual con Full Jitter.

    Formula:
        base_delay = min(max_delay, initial_delay * (factor ** attempt))
        delay = random.uniform(0, base_delay + jitter_max)
    """
    if attempt < 0:
        return 0.0
    computed_base = min(max_delay, initial_delay * (factor**attempt))
    jitter_cap = max(0.01, computed_base + jitter_max)
    return round(random.uniform(0.1, jitter_cap), 3)
