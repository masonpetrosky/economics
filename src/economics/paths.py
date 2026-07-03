"""Repository-relative path helpers."""

from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    """Return the repository root based on the installed source location."""

    return Path(__file__).resolve().parents[2]


def data_path(*parts: str) -> Path:
    """Return a path under the repo's data directory."""

    return repo_root() / "data" / Path(*parts)


def raw_data_path(*parts: str) -> Path:
    """Return a path under data/raw."""

    return data_path("raw", *parts)


def processed_data_path(*parts: str) -> Path:
    """Return a path under data/processed."""

    return data_path("processed", *parts)


def output_path(*parts: str) -> Path:
    """Return a path under outputs."""

    return repo_root() / "outputs" / Path(*parts)
