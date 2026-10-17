from importlib import import_module

import pytest

from src.app import app
from src.core.objective import objective_1
from src.services.optimization import run_optimization
from tests.algorithms.test_hill_variants import state_with
from tests.services.test_application import configuration


def test_capabilities_publish_six_algorithms_and_variant_parameters():
    definitions = app.test_client().get("/api/capabilities").get_json()["algorithms"]
    assert list(definitions) == ["hill_climbing", "stochastic_hill_climbing", "sideways_move", "random_restart",
                                 "simulated_annealing", "genetic_algorithm"]
    assert definitions["sideways_move"]["parameters"]["maximum_sideways_move"]["min"] == 0
    assert definitions["random_restart"]["parameters"]["maximum_restart"]["min"] == 0
    assert definitions["stochastic_hill_climbing"]["uses_algorithm_seed"] is True


@pytest.mark.parametrize("algorithm", ["stochastic_hill_climbing", "sideways_move"])
def test_algorithm_seed_is_forwarded_and_initial_state_seed_is_separate(monkeypatch, algorithm):
    module = import_module("src.services.optimization")
    real_algorithm = module.FUNCTIONS[algorithm]
    seeds = []

    def capture(initial, objective, neighbors, parameters):
        seeds.append(parameters["seed"])
        return real_algorithm(initial, objective, neighbors, parameters)

    monkeypatch.setitem(module.FUNCTIONS, algorithm, capture)
    config = {**configuration(algorithm), "algorithm_seed": 123}
    result = run_optimization(config)
    assert seeds == [123]
    assert result["configuration"]["seed"] == 42


@pytest.mark.parametrize("algorithm,limit,expected", [
    ("stochastic_hill_climbing", 3, "max_iterations"),
    ("sideways_move", 2, "max_sideways_moves"),
    ("sideways_move", 0, "no_admissible_move"),
])
def test_plateau_is_not_mislabeled_as_strict_local_improvement_failure(monkeypatch, algorithm, limit, expected):
    module = import_module("src.services.optimization")
    initial = state_with("A")
    initial.vehicles = {"A": initial.vehicles["A"]}
    monkeypatch.setattr(module, "create_initial_state", lambda *args, **kwargs: initial.copy())
    result = run_optimization({**configuration(algorithm), "parameters": {
        "max_iterations": 3, **({"maximum_sideways_move": limit} if algorithm == "sideways_move" else {}),
    }})
    assert result["stop_reason"] == expected
    if algorithm == "stochastic_hill_climbing":
        assert result["iterations"] == 3


@pytest.mark.parametrize("maximum_restart", [0, 2])
def test_restart_initializations_are_recorded_and_match_each_search(monkeypatch, maximum_restart):
    module = import_module("src.services.optimization")
    real_initializer = module.create_initial_state
    initializations = []

    def capture(ships, vehicles, seed):
        initial = real_initializer(ships, vehicles, seed=seed)
        initializations.append((seed, initial.to_dict(), objective_1(initial)))
        return initial

    monkeypatch.setattr(module, "create_initial_state", capture)
    result = run_optimization({**configuration("random_restart"), "parameters": {
        "maximum_restart": maximum_restart, "max_iterations": 3,
    }})
    assert result["configuration"]["restart_seeds"] == [42 + index for index in range(maximum_restart + 1)]
    assert [seed for seed, _, _ in initializations] == result["configuration"]["restart_seeds"]
    assert result["initial_state"] == initializations[0][1]
    assert result["metrics"]["restarts"] == maximum_restart
    assert result["iterations"] == sum(result["metrics"]["iterations_per_restart"])
    for history, steps, (_, _, initial_value) in zip(result["metrics"]["history_per_restart"],
                                                   result["metrics"]["iterations_per_restart"], initializations):
        assert history[0] == initial_value
        assert len(history) == steps + 1
    assert result["objective_value"] == max(history[-1] for history in result["metrics"]["history_per_restart"])


@pytest.mark.parametrize("algorithm,parameters", [
    ("stochastic_hill_climbing", {"max_iterations": 0}),
    ("sideways_move", {"maximum_sideways_move": -1}),
    ("sideways_move", {"maximum_sideways_move": True}),
    ("random_restart", {"maximum_restart": -1}),
    ("random_restart", {"maximum_restart": True}),
    ("random_restart", {"maximum_restart": 1.5}),
    ("random_restart", {"max_iterations": 0}),
])
def test_hc_api_rejects_invalid_variant_limits(algorithm, parameters):
    config = configuration(algorithm)
    config["parameters"].update(parameters)
    response = app.test_client().post("/api/optimize", json=config)
    assert response.status_code == 400
