import json
from concurrent.futures import ThreadPoolExecutor
from importlib import import_module

import pytest
from PIL import Image

from src.app import app
from src.services.optimization import run_optimization
from src.services.output import save_output


def configuration(algorithm="hill_climbing", **parameters):
    return {
        "algorithm": algorithm,
        "objective": "objective_2",
        "seed": 42,
        "algorithm_seed": 43,
        "problem": {
            "ships": [{"id": "s", "width": 2, "length": 1, "max_capacity": 2}],
            "vehicles": [{"id": "A", "width": 1, "length": 1,
                          "shipping_fee": 10, "weight": 1, "eta": 0}],
        },
        "parameters": {"max_iterations": 2, **parameters},
    }


@pytest.mark.parametrize("algorithm,parameters,plot_count", [
    ("hill_climbing", {}, 1),
    ("stochastic_hill_climbing", {}, 1),
    ("sideways_move", {"maximum_sideways_move": 0}, 1),
    ("random_restart", {"maximum_restart": 2}, 1),
    ("random_restart", {"maximum_restart": 0}, 1),
    ("simulated_annealing", {}, 3),
    ("simulated_annealing", {"max_iterations": 0}, 3),
    ("genetic_algorithm", {"population_size": 2, "max_iterations": 0}, 1),
])
def test_api_saves_complete_json_and_readable_pngs(tmp_path, algorithm, parameters, plot_count):
    response = app.test_client().post("/api/optimize", json=configuration(algorithm, **parameters))
    assert response.status_code == 200
    result = response.get_json()
    output = result["output"]
    assert output["status"] == "saved"
    assert len(output["plots"]) == plot_count
    if algorithm == "simulated_annealing":
        assert any(path.endswith("-sa-exponential.png") for path in output["plots"])
    saved = json.loads((tmp_path / output["result"]).read_text(encoding="utf-8"))
    assert saved == result
    assert saved["configuration"]["objective"] == "objective_2"
    for path in output["plots"]:
        with Image.open(tmp_path / path) as image:
            assert image.format == "PNG"
            assert image.width >= 800 and image.height >= 400
            image.verify()
    assert not list((tmp_path / "output").rglob("*.tmp"))


def test_concurrent_saves_have_unique_names_and_preserve_results(tmp_path):
    result = run_optimization(configuration())
    with ThreadPoolExecutor(max_workers=2) as pool:
        saved = list(pool.map(lambda _: save_output(result, tmp_path / "output"), range(2)))
    assert saved[0]["output"]["run_id"] != saved[1]["output"]["run_id"]
    assert len(list((tmp_path / "output/results").glob("*.json"))) == 2
    assert len(list((tmp_path / "output/plots").glob("*.png"))) == 2
    for item in saved:
        assert json.loads((tmp_path / item["output"]["result"]).read_text()) == item
    assert "output" not in result


def test_invalid_request_creates_no_output(tmp_path):
    response = app.test_client().post("/api/optimize", json={})
    assert response.status_code == 400
    assert not (tmp_path / "output").exists()


def test_unwritable_output_preserves_optimization_result(tmp_path):
    (tmp_path / "output").write_text("A file blocks output directory creation")
    response = app.test_client().post("/api/optimize", json=configuration())
    assert response.status_code == 200
    result = response.get_json()
    assert result["status"] == "success"
    assert result["output"]["status"] == "error"
    assert result["final_state"]
    assert "masih dapat diunduh" in result["output"]["message"]


def test_failed_plot_cleans_partial_files_and_preserves_optimization(tmp_path, monkeypatch):
    def fail(result, path):
        path.write_bytes(b"partial PNG")
        raise OSError("Disk full")

    monkeypatch.setattr(import_module("src.services.output"), "annealing_plot", fail)
    response = app.test_client().post("/api/optimize", json=configuration("simulated_annealing"))
    assert response.status_code == 200
    result = response.get_json()
    assert result["status"] == "success"
    assert result["output"]["status"] == "error"
    assert not list((tmp_path / "output").rglob("*.*"))


def test_overflowed_sa_factor_can_be_saved(tmp_path):
    result = run_optimization(configuration("simulated_annealing"))
    result["metrics"]["e_deltaet_history"] = [None, 0.5]
    result["metrics"]["e_deltaet_overflow_history"] = [True, False]
    saved = save_output(result, tmp_path / "output")
    assert saved["output"]["status"] == "saved"
    assert json.loads((tmp_path / saved["output"]["result"]).read_text()) == saved


def test_sa_exponential_plot_preserves_factors_above_one_and_marks_overflow(monkeypatch):
    output = import_module("src.services.output")
    result = run_optimization(configuration("simulated_annealing"))
    result["iterations"] = 5
    result["metrics"]["e_deltaet_history"] = [0, 0.5, 1, 3, None]
    result["metrics"]["e_deltaet_overflow_history"] = [False, False, False, False, True]
    figures = []
    monkeypatch.setattr(output, "save_figure", lambda figure, path: figures.append(figure))
    output.annealing_exponential_plot(result, None)
    figure = figures[0]
    try:
        axes = figure.axes[0]
        line = axes.lines[0]
        assert list(line.get_xdata()) == [1, 2, 3, 4, 5]
        assert list(line.get_ydata())[:4] == [0, 0.5, 1, 3]
        assert line.get_color() == "#386641"
        assert "Simulated Annealing" in axes.get_title()
        assert any("1 nilai overflow" in text.get_text() for text in figure.texts)
    finally:
        figure.clear()
