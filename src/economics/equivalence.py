"""Household-size equivalence-scale helpers."""

from __future__ import annotations

from math import sqrt


def square_root_equivalence_scale(household_size: float) -> float:
    """Return the square-root equivalence scale for a household.

    The scale treats shared living costs as partly joint: a larger household
    needs more resources than a one-person household, but less than a strict
    per-capita multiple.
    """

    if household_size <= 0:
        raise ValueError("household_size must be positive")
    return sqrt(household_size)


def equivalize_resources(resources: float, household_size: float) -> float:
    """Adjust household resources for household size."""

    return resources / square_root_equivalence_scale(household_size)
