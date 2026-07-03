# CBO Ingestion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or inline TDD to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a reproducible raw-to-processed CBO proxy ingestion path.

**Architecture:** Keep ingestion in one focused package module, expose it through one CLI script, and document the official CBO raw ZIP contract. Tests use tiny ZIP fixtures so the suite does not depend on network or committed raw data.

**Tech Stack:** Python 3.12, pandas, pathlib, zipfile, pytest.

## Global Constraints

- Do not commit raw CBO data.
- Do not add an Excel dependency.
- Do not download data automatically.
- Keep processed output schema compatible with existing loaders, charts, and notebooks.
- Raise clear `ValueError` messages for missing ZIP members or CSV columns.

---

### Task 1: CBO ZIP Builder

**Files:**
- Create: `tests/test_cbo_ingestion.py`
- Create: `src/economics/cbo.py`
- Modify: `src/economics/__init__.py`

**Steps:**
- [x] Write failing tests for extracting the official CBO ZIP member, validating missing members and columns, and matching the bundled processed series.
- [x] Implement `build_cbo_proxy_from_researchers_zip(raw_zip_path: str | Path) -> pd.DataFrame`.
- [x] Export the new builder from `economics.__init__`.
- [x] Run focused tests.

### Task 2: CLI And Documentation

**Files:**
- Create: `scripts/build_cbo_proxy.py`
- Modify: `README.md`
- Modify: `docs/data_sources.md`
- Modify: `data/processed/cbo_proxy_median_adjusted_income_after_tax_transfer.csv`

**Steps:**
- [x] Write a failing CLI test for building a processed CSV from a tiny ZIP fixture.
- [x] Implement the script with `--raw-zip` and `--out` arguments defaulting to the documented repo paths.
- [x] Update docs to reference the CBO researchers ZIP and exact member file.
- [x] Regenerate/update the processed CSV metadata to say it comes from the official researchers ZIP.
- [x] Run tests, ruff, the CBO builder, and the chart script.
