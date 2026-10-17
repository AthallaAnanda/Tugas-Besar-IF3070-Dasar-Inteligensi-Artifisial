from pathlib import Path

import pytest

from src.app import app
from src.core.constraint import is_valid
from src.core.state import State, load_problem
from src.experiments.runner import runner
from src.services.experiment import run_experiment
from src.services.optimization import run_optimization


SAMPLE = Path(__file__).resolve().parents[2] / "data/sample/small.json"


def problem_data():
    return load_problem(SAMPLE).to_dict()


def configuration(algorithm="hill_climbing"):
    return {
        "algorithm": algorithm,
        "problem": problem_data(),
        "seed": 42,
        "algorithm_seed": 43,
        "parameters": {
            "max_iterations": 10,
        },
        "record_steps": True,
    }


@pytest.mark.parametrize(
    "algorithm",
    ["hill_climbing", "simulated_annealing"],
)
def test_result_and_trace_follow_same_iterations(algorithm):
    result = run_optimization(configuration(algorithm))
    frames = result["trace"]["frames"]

    assert result["status"] == "success"
    assert frames[0]["iteration"] == 0
    assert frames[-1]["iteration"] == result["iterations"]
    assert len(frames) == len(result["history"])
    assert is_valid(State.from_dict(result["final_state"]))

    for frame in frames:
        iteration = frame["iteration"]
        assert frame["objective_value"] == result["history"][iteration]
        assert frame["best_value"] == result["best_history"][iteration]

    terminal = [
        placement
        for ship in result["terminal_state"]["ships"]
        for placement in ship["placements"]
    ]

    assert frames[-1]["placements"] == terminal


def test_trace_interval_keeps_last_iteration():
    config = configuration("simulated_annealing")
    config["trace_interval"] = 4
    result = run_optimization(config)

    iterations = [
        frame["iteration"]
        for frame in result["trace"]["frames"]
    ]

    assert iterations[0] == 0
    assert iterations[-1] == result["iterations"]
    assert len(iterations) == len(set(iterations))


def test_trace_can_be_disabled():
    config = configuration()
    config["record_steps"] = False

    result = run_optimization(config)

    assert result["trace"]["frames"] == []
    assert result["trace"]["enabled"] is False


def test_experiment_pairs_initial_states():
    result = run_experiment({
        "problem": problem_data(),
        "seed": 42,
        "runs": 2,
        "configurations": [
            {
                "algorithm": "hill_climbing",
                "parameters": {"max_iterations": 2},
            },
            {
                "algorithm": "simulated_annealing",
                "parameters": {"max_iterations": 2},
            },
        ],
    })

    assert len(result["results"]) == 4
    assert len(result["summaries"]) == 2

    first = result["results"][0]["result"]["initial_state"]
    paired = result["results"][2]["result"]["initial_state"]

    assert first == paired
    assert all(
        not item["result"]["trace"]["enabled"]
        for item in result["results"]
    )


def test_runner_saves_json_and_csv(tmp_path):
    result = runner({
        "problem": problem_data(),
        "runs": 1,
        "seed": 42,
        "configurations": [
            {
                "algorithm": "hill_climbing",
                "parameters": {"max_iterations": 1},
            }
        ],
    }, output_dir=tmp_path)

    assert Path(result["saved_files"]["json"]).exists()
    assert Path(result["saved_files"]["csv"]).exists()


def test_api_serves_frontend_and_optimization():
    client = app.test_client()

    assert client.get("/").status_code == 200
    assert client.get("/assets/js/app.js").status_code == 200
    assert client.get("/api/capabilities").status_code == 200

    response = client.post("/api/optimize", json=configuration())

    assert response.status_code == 200
    assert response.get_json()["status"] == "success"


@pytest.mark.parametrize("payload", [
    {},
    {"algorithm": "genetic_algorithm"},
    {**configuration(), "parameters": {"max_iterations": -1}},
    {**configuration(), "trace_interval": 0},
])
def test_api_rejects_invalid_request(payload):
    response = app.test_client().post("/api/optimize", json=payload)

    assert response.status_code == 400
    assert response.get_json()["status"] == "error"