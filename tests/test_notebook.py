import json
from pathlib import Path

NOTEBOOK_PATH = Path("notebooks/01_cbo_proxy_starter.ipynb")


def test_starter_notebook_exists_and_mentions_cbo_proxy_caveat() -> None:
    notebook = json.loads(NOTEBOOK_PATH.read_text())
    text = "\n".join(
        "".join(cell.get("source", []))
        for cell in notebook["cells"]
        if cell.get("cell_type") == "markdown"
    )

    assert "starter proxy" in text
    assert "official Additional Data for Researchers ZIP" in text
    assert "not publication-ready" in text


def test_readme_documents_editable_install_and_notebook() -> None:
    readme = Path("README.md").read_text()

    assert 'pip install -e ".[dev]"' in readme
    assert "notebooks/01_cbo_proxy_starter.ipynb" in readme
    assert "data/raw/fred_real_median_personal_income.csv" in readme


def test_docs_document_cps_real_dollar_qa_workflow() -> None:
    readme = Path("README.md").read_text()
    data_sources = Path("docs/data_sources.md").read_text()
    methodology = Path("docs/methodology.md").read_text()

    assert "data/raw/annual_price_index.csv" in readme
    assert "scripts/build_cps_ipums_real.py" in readme
    assert "scripts/build_cps_public_proxy_qa.py" in readme
    assert "cps_ipums_median_adult_equivalent_resources_real.csv" in readme
    assert "annual_price_index.csv" in data_sources
    assert "year" in data_sources
    assert "price_index" in data_sources
    assert "nominal CPS/IPUMS" in methodology
    assert "real CPS/IPUMS" in methodology
    assert "indexed public-proxy QA" in methodology
