# FRED Comparison Ingestion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add reproducible raw-to-processed FRED ingestion for the three public comparison metrics.

**Architecture:** Keep FRED-specific parsing and annualization in `economics.fred`, expose one CLI script, and let existing loaders consume processed CSVs. Tests use tiny CSV fixtures and do not depend on network or committed raw files.

**Tech Stack:** Python 3.12, pandas, pathlib, matplotlib, pytest.

## Global Constraints

- Do not add a FRED API key dependency.
- Do not download data automatically in project code.
- Keep raw FRED files out of git under ignored `data/raw/`.
- Support FRED graph CSVs with `observation_date,<FRED_SERIES_ID>` columns.
- Support project-shaped CSVs with `year,value` columns.
- Aggregate monthly disposable-income observations to full calendar-year means.
- Processed comparison CSVs must use `year`, `value`, `series_id`, `series`, `source`, and `notes` columns.

---

### Task 1: FRED Builders And CLI

**Files:**
- Create: `tests/test_fred_ingestion.py`
- Create: `src/economics/fred.py`
- Modify: `src/economics/__init__.py`
- Create: `scripts/build_fred_comparisons.py`

**Interfaces:**
- Produces: `FredSeriesSpec`, `FRED_SERIES`, `build_fred_series(raw_csv_path: str | Path, spec: FredSeriesSpec) -> pd.DataFrame`, and `build_all_fred_series(raw_dir: str | Path, processed_dir: str | Path) -> dict[str, Path]`.

- [x] Write failing tests for annual FRED CSV parsing, project-shaped CSV parsing, monthly full-year averaging, incomplete monthly-year exclusion, missing-column errors, and CLI output.
- [x] Run the focused tests and confirm they fail because `economics.fred` does not exist.
- [x] Implement the minimal FRED module and CLI.
- [x] Export the new helpers from `economics.__init__`.
- [x] Run focused tests and confirm they pass.

### Task 2: Processed Data, Docs, And Comparison Chart

**Files:**
- Modify: `README.md`
- Modify: `docs/data_sources.md`
- Modify: `docs/methodology.md`
- Modify: `notebooks/01_cbo_proxy_starter.ipynb`
- Modify: `src/economics/charts.py`
- Create: `scripts/plot_public_proxies.py`
- Create: processed CSV outputs under `data/processed/`
- Modify or create tests covering chart/script behavior.

**Interfaces:**
- Consumes: Task 1 processed files and existing `load_comparison_series`.
- Produces: a public-proxies chart script that writes `outputs/charts/public_proxy_comparison.png`.

- [x] Write failing tests for multi-series chart output and bundled comparison processed files.
- [x] Implement the multi-series chart helper and comparison plot script.
- [x] Update docs and notebook to describe/use the processed FRED comparisons.
- [x] Download the three official FRED graph CSVs manually into ignored `data/raw/`.
- [x] Run `python scripts/build_fred_comparisons.py` to generate processed CSVs.
- [x] Run focused tests, full tests, ruff, both builder scripts, and both chart scripts.
