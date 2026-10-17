from pathlib import Path

import pytest

from src.app import app
from src.core.constraint import is_valid
from src.core.state import State, load_problem
from src.services.optimization import run_optimization


SAMPLE = Path(__file__).resolve().parents[2] / "data/sample/small.json"


def problem_data():
    return load_problem(SAMPLE).to_dict()


def configuration(algorithm="hill_climbing"):
    parameters = {"max_iterations": 10}
    if algorithm == "genetic_algorithm":
        parameters.update(population_size=4, max_iterations=3)
    if algorithm == "random_restart":
        parameters.update(maximum_restart=2, max_iterations=3)
    return {"algorithm": algorithm, "problem": problem_data(), "seed": 42,
            "algorithm_seed": 43, "parameters": parameters}


@pytest.mark.parametrize("algorithm", [
    "hill_climbing", "stochastic_hill_climbing", "sideways_move", "random_restart",
    "simulated_annealing", "genetic_algorithm",
])
def test_optimization_returns_valid_reproducible_solution_and_history(algorithm):
    first = run_optimization(configuration(algorithm))
    second = run_optimization(configuration(algorithm))
    assert first["status"] == "success"
    assert len(first["history"]) == first["iterations"] + 1
    assert first["objective_value"] == first["best_history"][-1]
    assert first["objective_value"] >= first["history"][0]
    assert is_valid(State.from_dict(first["initial_state"]))
    assert is_valid(State.from_dict(first["final_state"]))
    for key in ("initial_state", "final_state", "history", "best_history"):
        assert first[key] == second[key]
    assert first["duration"] >= 0
    assert first["initialization_duration"] >= 0


def test_api_serves_frontend_and_supported_optimization_contract():
    client = app.test_client()
    assert {rule.rule for rule in app.url_map.iter_rules()} == {
        "/", "/assets/<path:filename>", "/api/health", "/api/sample",
        "/api/capabilities", "/api/optimize",
    }
    assert client.get("/").status_code == 200
    assert client.get("/assets/js/app.js").status_code == 200
    assert set(client.get("/api/capabilities").get_json()) == {"algorithms", "objectives"}
    response = client.post("/api/optimize", json=configuration())
    assert response.status_code == 200
    assert set(response.get_json()) == {
        "status", "objective_value", "iterations", "duration", "initial_state", "final_state",
        "history", "best_history", "mean_history", "metrics", "initialization_duration",
        "algorithm", "step_type", "stop_reason", "statistics", "configuration",
    }


@pytest.mark.parametrize("payload", [
    {}, {"algorithm": "genetic_algorithm"},
    {**configuration(), "parameters": {"max_iterations": -1}},
    {**configuration(), "parameters": {"max_iterations": True}},
    {**configuration(), "parameters": {"unknown": 1}},
])
def test_api_rejects_invalid_request(payload):
    response = app.test_client().post("/api/optimize", json=payload)
    assert response.status_code == 400
    assert response.get_json()["status"] == "error"


@pytest.mark.parametrize("algorithm,parameters,reason", [
    ("hill_climbing", {"max_iterations": 1}, "no_improvement"),
    ("stochastic_hill_climbing", {"max_iterations": 3}, "no_neighbors"),
    ("sideways_move", {"max_iterations": 3}, "no_admissible_move"),
    ("random_restart", {"maximum_restart": 0}, "max_restarts"),
    ("simulated_annealing", {"max_iterations": 0}, "max_iterations"),
    ("simulated_annealing", {"initial_temperature": 1, "min_temperature": 1}, "min_temperature"),
    ("simulated_annealing", {}, "no_neighbors"),
    ("genetic_algorithm", {"population_size": 2, "max_iterations": 0}, "max_iterations"),
])
def test_service_explains_termination_without_algorithm_instrumentation(algorithm, parameters, reason):
    result = run_optimization({"algorithm": algorithm, "problem": {
        "ships": [{"id": "empty", "width": 1, "length": 1, "max_capacity": 1}], "vehicles": [],
    }, "seed": 42, "parameters": parameters})
    assert result["stop_reason"] == reason


@pytest.mark.parametrize("algorithm", [
    "hill_climbing", "stochastic_hill_climbing", "sideways_move", "random_restart",
    "simulated_annealing", "genetic_algorithm",
])
def test_null_seeds_are_generated_per_run_and_can_be_reused_manually(monkeypatch, algorithm):
    from importlib import import_module

    module = import_module("src.services.optimization")
    generated = iter([7001, 9001, 7002, 9002])
    monkeypatch.setattr(module.secrets, "randbits", lambda bits: next(generated))
    client = app.test_client()
    payload = {**configuration(algorithm), "seed": None, "algorithm_seed": None}
    first_response = client.post("/api/optimize", json=payload)
    second_response = client.post("/api/optimize", json=payload)
    assert first_response.status_code == second_response.status_code == 200
    first = first_response.get_json()
    second = second_response.get_json()
    assert (first["configuration"]["seed"], first["configuration"]["algorithm_seed"]) == (7001, 9001)
    assert (second["configuration"]["seed"], second["configuration"]["algorithm_seed"]) == (7002, 9002)
    repeated = client.post("/api/optimize", json={**payload, "seed": 7001, "algorithm_seed": 9001}).get_json()
    for field in ("initial_state", "final_state", "history", "best_history", "mean_history"):
        assert repeated[field] == first[field]
    if algorithm == "random_restart":
        assert repeated["configuration"]["restart_seeds"] == first["configuration"]["restart_seeds"]
