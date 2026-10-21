import pytest

from src.app import app


@pytest.fixture(autouse=True)
def isolated_output(tmp_path, monkeypatch):
    monkeypatch.setitem(app.config, "OUTPUT_DIR", tmp_path / "output")
