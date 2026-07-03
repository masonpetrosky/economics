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
    assert "official CBO supplemental workbook" in text
    assert "not publication-ready" in text


def test_readme_documents_editable_install_and_notebook() -> None:
    readme = Path("README.md").read_text()

    assert 'pip install -e ".[dev]"' in readme
    assert "notebooks/01_cbo_proxy_starter.ipynb" in readme
    assert "data/raw/fred_real_median_personal_income.csv" in readme
